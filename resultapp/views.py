from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Value, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone
from datetime import date, timedelta
import json
import random

from .models import (
    Medicine, Supplier, Batch, Purchase,
    Sale, SaleItem, Customer, PharmacySettings
)
from .forms import CustomerForm
from .decorators import role_required


# ============================================================
# Home
# ============================================================

def index(request):
    return render(request, 'home.html')


# ============================================================
# Auth — Admin
# ============================================================

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin-dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin-dashboard')
        else:
            error = "Invalid credential or not authorized."

    return render(request, 'admin_login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin-login')


# ============================================================
# Auth — Pharmacist
# ============================================================

def pharmacist_login(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user and user.groups.filter(name='Pharmacist').exists():
            login(request, user)
            return redirect('pharmacist-dashboard')
        messages.error(request, "Invalid Pharmacist credentials")

    return render(request, 'auth/pharmacist_login.html')


def register_pharmacist(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = User.objects.create_user(username=username, password=password)
        group = Group.objects.get(name='Pharmacist')
        user.groups.add(group)

        messages.success(request, "Pharmacist created")
        return redirect('pharmacist-login')

    return render(request, 'auth/register_pharmacist.html')


@login_required
@role_required('Pharmacist')
def pharmacist_dashboard(request):
    return render(request, 'pharmacist/dashboard.html')


# ============================================================
# Auth — Customer
# ============================================================

def customer_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user is not None:
            if user.groups.filter(name='Customer').exists():
                login(request, user)
                return redirect('customer-dashboard')
            else:
                messages.error(request, "You are not a Customer")
        else:
            messages.error(request, "Invalid Customer credentials")

    return render(request, 'auth/customer_login.html')


def register_customer(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('customer-register')

        user = User.objects.create_user(username=username, password=password)
        group = Group.objects.get(name='Customer')
        user.groups.add(group)

        messages.success(request, "Account created successfully")
        return redirect('customer-login')

    return render(request, 'auth/register.html')


@login_required
@role_required('Customer')
def customer_dashboard(request):
    return render(request, 'customer/dashboard.html')


def user_logout(request):
    logout(request)
    return redirect('home')


# ============================================================
# Admin Dashboard
# ============================================================

@role_required('Admin')
def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')

    total_medicines = Medicine.objects.count()
    total_suppliers = Supplier.objects.count()
    total_expired_batches = Batch.objects.filter(
        expiry_date__lt=timezone.now().date(),
        status=True
    ).count()

    today = timezone.now().date()
    today_sales = Sale.objects.filter(created_at__date=today)
    total_today_sales = today_sales.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Weekly Sales (last 7 days)
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    weekly_labels = []
    weekly_data = []
    for d in dates:
        total = Sale.objects.filter(created_at__date=d).aggregate(
            Sum('total_amount')
        )['total_amount__sum'] or 0
        weekly_labels.append(d.strftime('%a'))
        weekly_data.append(float(total))

    # Daily Sales
    daily_sales = (
        Sale.objects
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('day')
    )
    daily_labels = [item['day'].strftime('%d %b') for item in daily_sales]
    daily_data = [float(item['total']) for item in daily_sales]
    daily_sales_table = [
        (item['day'].strftime('%d %b %Y'), float(item['total']))
        for item in daily_sales
    ]

    # Monthly Sales
    monthly_sales = (
        Sale.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    monthly_labels = [item['month'].strftime('%b %Y') for item in monthly_sales]
    monthly_data = [float(item['total']) for item in monthly_sales]

    context = {
        'total_medicines': total_medicines,
        'total_suppliers': total_suppliers,
        'total_expired_batches': total_expired_batches,
        'total_today_sales': total_today_sales,
        'weekly_labels': json.dumps(weekly_labels),
        'weekly_data': json.dumps(weekly_data),
        'daily_labels': json.dumps(daily_labels),
        'daily_data': json.dumps(daily_data),
        'daily_sales_table': daily_sales_table,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
    }

    return render(request, 'admin_dashboard.html', context)


# ============================================================
# Medicine
# ============================================================

@login_required
def add_medicine(request):
    if request.method == "POST":
        try:
            medicine_name = request.POST.get("medicine_name")
            company_name = request.POST.get("company_name")
            batch_no = request.POST.get("batch_no")
            manufacture_date = request.POST.get("manufacture_date")
            expiry_date = request.POST.get("expiry_date")
            buy_price = request.POST.get("buy_price")
            sell_price = request.POST.get("sell_price")
            quantity = request.POST.get("quantity")

            if not all([medicine_name, company_name, batch_no, expiry_date, buy_price, sell_price, quantity]):
                messages.error(request, "All fields are required.")
                return redirect("add_medicine")

            medicine, created = Medicine.objects.get_or_create(
                medicine_name=medicine_name,
                company_name=company_name
            )

            Batch.objects.create(
                medicine=medicine,
                batch_no=batch_no,
                manufacture_date=manufacture_date,
                expiry_date=expiry_date,
                buy_price=buy_price,
                sell_price=sell_price,
                quantity=quantity,
                status=True
            )

            messages.success(request, "Medicine and Batch added successfully.")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect("add_medicine")

    return render(request, "add_medicine.html")


@login_required
def manage_medicine(request):
    medicines = Medicine.objects.annotate(
        total_stock=Coalesce(Sum('batches__quantity'), Value(0))
    ).order_by('-created_date')

    if request.GET.get('delete'):
        medicine = get_object_or_404(Medicine, id=request.GET.get('delete'))
        if medicine.batches.exists():
            messages.error(request, "Cannot delete medicine with existing stock (batches).")
        else:
            medicine.delete()
            messages.success(request, "Medicine deleted successfully.")
        return redirect('manage_medicine')

    return render(request, 'manage_medicine.html', {'medicines': medicines})


@login_required
def edit_medicine(request, add_id):
    medicine = get_object_or_404(Medicine, id=add_id)

    if request.method == "POST":
        medicine.medicine_name = request.POST.get("medicine_name")
        medicine.company_name = request.POST.get("company_name")
        medicine.save()
        messages.success(request, "Medicine updated successfully.")
        return redirect("manage_medicine")

    return render(request, "edit_medicine.html", {"medicine": medicine})


@login_required
def expired_medicine(request):
    today = timezone.now().date()
    expired_batches = Batch.objects.filter(
        expiry_date__lt=today,
        status=True
    ).select_related('medicine').order_by('expiry_date')

    return render(request, "expired_medicine.html", {
        "expired_batches": expired_batches,
        "today": today
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from .models import Batch


# ============================================================
# Batch List
# ============================================================

from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date
from .models import Batch


def batch_list(request):

    # ✅ DELETE LOGIC
    if request.GET.get('delete'):
        batch_id = request.GET.get('delete')

        Batch.objects.filter(id=batch_id).delete()

        messages.success(request, "Batch deleted successfully")
        return redirect('batch_list')

    batches = Batch.objects.filter(status=True)\
        .select_related('medicine')\
        .order_by('-created_at')

    return render(request, 'batch_list.html', {
        'batches': batches,
        'today': date.today()
    })

# ============================================================
# Edit Batch
# ============================================================

@login_required
def edit_batch(request, id):
    batch = get_object_or_404(Batch, id=id)

    if request.method == "POST":

        batch.batch_no = request.POST.get('batch_no')
        batch.quantity = request.POST.get('quantity')
        batch.manufacture_date = request.POST.get('manufacture_date')
        batch.expiry_date = request.POST.get('expiry_date')
        batch.buy_price = request.POST.get('buy_price')
        batch.sell_price = request.POST.get('sell_price')

        # ⚠️ FIX: status must be handled safely
        batch.status = True if request.POST.get('status') == "1" else False

        batch.save()

        messages.success(request, "Batch updated successfully")
        return redirect('batch_list')

    return render(request, 'edit_batch.html', {'batch': batch})


# ============================================================
# Delete Batch (SAFE POST METHOD)
# ============================================================

@login_required
def delete_batch(request, id):
    batch = get_object_or_404(Batch, id=id)

    if request.method == "POST":
        batch.delete()
        messages.success(request, "Batch deleted successfully")
        return redirect('batch_list')

    return redirect('batch_list')





# ============================================================
# Supplier
# ============================================================

def add_supplier(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        phone = request.POST.get('phone')

        if not supplier_name or not phone:
            messages.error(request, "Supplier Name and Phone are required!")
            return redirect('add_supplier')

        Supplier.objects.create(
            supplier_name=supplier_name,
            company_name=request.POST.get('company_name'),
            phone=phone,
            email=request.POST.get('email'),
            address=request.POST.get('address')
        )
        messages.success(request, "Supplier Added Successfully!")
        return redirect('add_supplier')

    return render(request, 'add_supplier.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Supplier


def manage_supplier(request):

    # ✅ DELETE LOGIC HERE
    if request.GET.get('delete'):
        supplier_id = request.GET.get('delete')

        Supplier.objects.filter(id=supplier_id).delete()

        messages.success(request, "Supplier deleted successfully")
        return redirect('manage_supplier')

    suppliers = Supplier.objects.all()

    return render(request, 'manage_supplier.html', {
        'suppliers': suppliers
    })


def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        phone = request.POST.get('phone')

        if not supplier_name or not phone:
            messages.error(request, "Supplier Name and Phone are required!")
            return redirect('manage_supplier')

        supplier.supplier_name = supplier_name
        supplier.company_name = request.POST.get('company_name')
        supplier.phone = phone
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')
        supplier.save()

        messages.success(request, "Supplier updated successfully.")
        return redirect('manage_supplier')

    return render(request, 'edit_supplier.html', {'supplier': supplier})


# ============================================================
# Purchase
# ============================================================

def new_purchase(request):
    medicines = Medicine.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        try:
            supplier = get_object_or_404(Supplier, id=request.POST.get('supplier'))
            medicine = get_object_or_404(Medicine, id=request.POST.get('medicine'))
            batch_no = request.POST.get('batch_no')
            manufacture_date = request.POST.get('manufacture_date')
            expiry_date = request.POST.get('expiry_date')
            quantity = int(request.POST.get('quantity'))
            buy_price = request.POST.get('buy_price')
            sell_price = request.POST.get('sell_price')
            purchase_date = request.POST.get('purchase_date')

            Purchase.objects.create(
                supplier=supplier,
                medicine=medicine,
                batch_no=batch_no,
                manufacture_date=manufacture_date,
                expiry_date=expiry_date,
                quantity=quantity,
                buy_price=buy_price,
                sell_price=sell_price,
                purchase_date=purchase_date
            )

            batch, created = Batch.objects.get_or_create(
                medicine=medicine,
                batch_no=batch_no,
                defaults={
                    'manufacture_date': manufacture_date,
                    'expiry_date': expiry_date,
                    'quantity': quantity,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'status': True
                }
            )

            if not created:
                batch.quantity += quantity
                batch.buy_price = buy_price
                batch.sell_price = sell_price
                batch.save()

            messages.success(request, "Purchase added and stock updated.")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('new_purchase')

    return render(request, 'new_purchase.html', {
        'medicines': medicines,
        'suppliers': suppliers
    })


def purchase_history(request):
    purchases = Purchase.objects.select_related('supplier', 'medicine').order_by('-purchase_date')
    return render(request, 'purchase_history.html', {'purchases': purchases})


# ============================================================
# Sales
# ============================================================

def new_sale(request):
    medicines = Medicine.objects.all()

    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        medicine_ids = request.POST.getlist('medicine_id[]')
        batch_ids = request.POST.getlist('batch_id[]')
        qtys = request.POST.getlist('qty[]')

        sale_items = []
        total_amount = 0

        for med_id, batch_id, qty in zip(medicine_ids, batch_ids, qtys):
            if not qty or int(qty) <= 0:
                continue

            qty = int(qty)
            medicine = get_object_or_404(Medicine, id=med_id)
            batch = Batch.objects.get(
                id=batch_id,
                medicine=medicine,
                quantity__gt=0,
                status=True,
                expiry_date__gt=date.today()
            )

            if qty > batch.quantity:
                qty = batch.quantity

            total = qty * batch.sell_price
            sale_items.append({
                "medicine": medicine,
                "batch": batch,
                "qty": qty,
                "price": batch.sell_price,
                "total": total
            })

            batch.quantity -= qty
            batch.save()
            total_amount += total

        if sale_items:
            invoice = "INV" + str(random.randint(10000, 99999))
            sale = Sale.objects.create(
                invoice_no=invoice,
                customer_name=customer_name,
                total_amount=total_amount
            )
            for item in sale_items:
                SaleItem.objects.create(
                    sale=sale,
                    medicine=item["medicine"],
                    batch=item["batch"],
                    price=item["price"],
                    quantity=item["qty"],
                    total=item["total"]
                )
            messages.success(request, "Sale completed successfully")
            return redirect("sales_history")

        messages.error(request, "Please select at least one medicine")
        return redirect("new_sale")

    for med in medicines:
        valid_batches = med.batches.filter(
            status=True,
            quantity__gt=0,
            expiry_date__gt=date.today()
        ).order_by('expiry_date')
        med.valid_batches = valid_batches
        med.total_qty = valid_batches.aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, "new_sale.html", {"medicines": medicines})


def sales_history(request):
    sales = Sale.objects.all().order_by("-created_at")
    return render(request, "sales_history.html", {"sales": sales})


def invoice_print(request, id):
    sale = get_object_or_404(Sale, id=id)
    items = SaleItem.objects.filter(sale=sale)
    return render(request, 'invoice_print.html', {'sale': sale, 'items': items})


# ============================================================
# Customer
# ============================================================

def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added successfully")
            return redirect('manage_customer')
    else:
        form = CustomerForm()
    return render(request, 'add_customer.html', {'form': form})


def manage_customer(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'manage_customer.html', {'customers': customers})


def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated successfully")
            return redirect('manage_customer')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'edit_customer.html', {'form': form})


def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, "Customer deleted successfully")
    return redirect('manage_customer')


# ============================================================
# Reports
# ============================================================

def sales_report(request):
    sales = Sale.objects.all().order_by('-created_at')
    total_sales = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    return render(request, 'sales_report.html', {
        'sales': sales,
        'total_sales': total_sales
    })


def stock_report(request):
    batches = Batch.objects.select_related('medicine')
    total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0
    return render(request, 'stock_report.html', {
        'batches': batches,
        'total_stock': total_stock
    })






def purchase_report(request):
    purchases = Purchase.objects.all().order_by('-purchase_date').annotate(
        total=ExpressionWrapper(
            F('quantity') * F('buy_price'),
            output_field=DecimalField()
        )
    )
    total_purchase = purchases.aggregate(grand_total=Sum('total'))['grand_total'] or 0
    return render(request, 'purchase_report.html', {
        'purchases': purchases,
        'total_purchase': total_purchase
    })


from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

# ==========================================
# ১. Add User Function (নতুন ইউজার যোগ করা)
# ==========================================
def add_user(request):
    if request.method == 'POST':
        # ফর্ম থেকে ডাটা রিসিভ করা
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        status = request.POST.get('status')

        # পাসওয়ার্ড চেক
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('add_user')

        # ইউজারনেম আগে থেকেই আছে কি না চেক
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken!")
            return redirect('add_user')

        # নতুন ইউজার তৈরি করা
        new_user = User.objects.create_user(username=username, email=email, password=password)
        new_user.first_name = first_name
        new_user.last_name = last_name
        
        # রোল অনুযায়ী পারমিশন সেট করা (Admin/Manager/Staff)
        if role == 'Admin':
            new_user.is_superuser = True
            new_user.is_staff = True
        elif role == 'Pharmacist' or role == 'Manager':
            new_user.is_staff = True
        else:
            new_user.is_staff = False # সাধারণ স্টাফ
            
        # স্ট্যাটাস সেট করা (Active/Inactive)
        if status == 'Active':
            new_user.is_active = True
        else:
            new_user.is_active = False

        new_user.save()

        messages.success(request, "New user created successfully!")
        return redirect('manage_users') # সেভ হওয়ার পর Manage পেইজে নিয়ে যাবে

    # GET মেথড হলে শুধু ফর্ম দেখাবে
    return render(request, 'add_user.html')


# ==========================================
# ২. Manage Users Function (লিস্ট দেখানো)
# ==========================================
def manage_users(request):
    # ডাটাবেস থেকে সব ইউজারের লিস্ট আনা (নতুনরা আগে দেখাবে)
    all_users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': all_users
    }
    return render(request, 'manage_user.html', {'users': all_users})










# ============================================================
# Settings
# ============================================================

@login_required
def pharmacy_settings(request):
    settings = PharmacySettings.objects.first()

    if request.method == "POST":
        pharmacy_name = request.POST.get('pharmacy_name')
        owner_name = request.POST.get('owner_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        tax = request.POST.get('tax')
        discount = request.POST.get('discount')
        currency = request.POST.get('currency')

        if settings:
            settings.pharmacy_name = pharmacy_name
            settings.owner_name = owner_name
            settings.phone = phone
            settings.email = email
            settings.address = address
            settings.tax_percentage = tax
            settings.discount_percentage = discount
            settings.currency = currency
            if request.FILES.get('logo'):
                settings.logo = request.FILES['logo']
            settings.save()
            messages.success(request, "Settings Updated Successfully")
        else:
            PharmacySettings.objects.create(
                pharmacy_name=pharmacy_name,
                owner_name=owner_name,
                phone=phone,
                email=email,
                address=address,
                tax_percentage=tax,
                discount_percentage=discount,
                currency=currency,
                logo=request.FILES.get('logo')
            )
            messages.success(request, "Settings Saved Successfully")

        return redirect('pharmacy_settings')

    return render(request, 'settings/pharmacy_settings.html', {'settings': settings})



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import InvoiceSetting



def invoice_settings_view(request):
    # ডাটাবেস থেকে প্রথম রেকর্ডটি আনা, না থাকলে নতুন তৈরি করা
    settings, created = InvoiceSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        settings.invoice_prefix = request.POST.get('invoice_prefix')
        settings.paper_size = request.POST.get('paper_size')
        settings.terms_conditions = request.POST.get('terms_conditions')
        settings.footer_note = request.POST.get('footer_note')
        
        
        settings.show_discount = 'show_discount' in request.POST
        
        settings.save()
        messages.success(request, 'Invoice settings updated successfully!')
        return redirect('invoice_settings') # আপনার urls.py এর নাম অনুযায়ী পাল্টে নেবেন
    
    context = {
        'invoice_set': settings
    }
    return render(request, 'settings/invoice_settings.html', context)




@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully")
            return redirect('admin-dashboard')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'settings/change_password.html', {'form': form})














# from multiprocessing import context

# from django.shortcuts import get_object_or_404, redirect, render
# from django.contrib.auth import authenticate, login, logout 
# from django.contrib import messages
# from .models import *
# from django.contrib.auth.decorators import login_required
# from .decorators import role_required
# # Create your views here.

# def index(request):
#     return render(request, 'home.html')


# def admin_login(request):
#     if request.user.is_authenticated:
#         return redirect('admin-dashboard')
    
#     error = None
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username = username, password = password )

#         if user is not None and user.is_superuser:
#             login(request, user)
#             return redirect('admin-dashboard')
#         else:
#             error = "Invalid credential or not authorized."
#     return render(request, 'admin_login.html',locals())





# def pharmacist_login(request):

#     if request.method == 'POST':

#         user = authenticate(
#             request,
#             username=request.POST.get('username'),
#             password=request.POST.get('password')
#         )

#         if user and user.groups.filter(name='Pharmacist').exists():
#             login(request, user)
#             return redirect('pharmacist-dashboard')

#         messages.error(request, "Invalid Pharmacist credentials")

#     return render(request, 'auth/pharmacist_login.html')



# from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import Group
# from django.shortcuts import render, redirect
# from django.contrib import messages

# def customer_login(request):

#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request, username=username, password=password)

#         if user is not None:

#             # ✅ Check group
#             if user.groups.filter(name='Customer').exists():
#                 login(request, user)
#                 return redirect('customer-dashboard')

#             else:
#                 messages.error(request, "You are not a Customer")

#         else:
#             messages.error(request, "Invalid Customer credentials")

#     return render(request, 'auth/customer_login.html')



# from django.contrib.auth.models import User, Group

# def register_customer(request):

#     if request.method == 'POST':

#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, "Username already exists")
#             return redirect('customer-register')

#         user = User.objects.create_user(
#             username=username,
#             password=password
#         )

#         group = Group.objects.get(name='Customer')
#         user.groups.add(group)

#         messages.success(request, "Account created successfully")
#         return redirect('customer-login')

#     return render(request, 'auth/register.html')




# def register_pharmacist(request):

#     if request.method == 'POST':

#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = User.objects.create_user(
#             username=username,
#             password=password
#         )

#         group = Group.objects.get(name='Pharmacist')
#         user.groups.add(group)

#         messages.success(request, "Pharmacist created")
#         return redirect('pharmacist-login')

#     return render(request, 'auth/register_pharmacist.html')


# def user_logout(request):
#     logout(request)
#     return redirect('home')

# from .decorators import role_required
# from django.contrib.auth.decorators import login_required


# @login_required
# @role_required('Pharmacist')
# def pharmacist_dashboard(request):
#     return render(request, 'pharmacist/dashboard.html')


# @login_required
# @role_required('Customer')
# def customer_dashboard(request):
#     return render(request, 'customer/dashboard.html')







# from datetime import timedelta



# import json
# from datetime import timedelta

# from django.shortcuts import render, redirect
# from django.db.models import Sum
# from django.db.models.functions import TruncDate, TruncMonth
# from django.utils import timezone


# @role_required('Admin')
# def admin_dashboard(request):
#     if not request.user.is_authenticated:
#         return redirect('admin-login')

#     total_medicines = Medicine.objects.count()
#     total_expired_batches = Batch.objects.filter(
#         expiry_date__lt=timezone.now().date(),
#         status=True
#     ).count()
#     total_suppliers = Supplier.objects.count()

#     # Today's Sales
#     today = timezone.now().date()
#     today_sales = Sale.objects.filter(created_at__date=today)
#     total_today_sales = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0

#     # =========================
#     # ✅ Weekly Sales (LAST 7 DAYS)
#     # =========================
#     dates = [today - timedelta(days=i) for i in range(6, -1, -1)]

#     weekly_labels = []
#     weekly_data = []

#     for date in dates:
#         total = Sale.objects.filter(created_at__date=date).aggregate(
#             Sum('total_amount')
#         )['total_amount__sum'] or 0

#         weekly_labels.append(date.strftime('%a'))  # Mon, Tue...
#         weekly_data.append(float(total))

#     # =========================
#     # Existing Daily Chart
#     # =========================
#     daily_sales = (
#         Sale.objects
#         .annotate(day=TruncDate('created_at'))
#         .values('day')
#         .annotate(total=Sum('total_amount'))
#         .order_by('day')
#     )

#     daily_labels = [item['day'].strftime('%d %b') for item in daily_sales]
#     daily_data = [float(item['total']) for item in daily_sales]

#     daily_sales_table = [
#         (item['day'].strftime('%d %b %Y'), float(item['total']))
#         for item in daily_sales
#     ]

#     # Monthly
#     monthly_sales = (
#         Sale.objects
#         .annotate(month=TruncMonth('created_at'))
#         .values('month')
#         .annotate(total=Sum('total_amount'))
#         .order_by('month')
#     )

#     monthly_labels = [item['month'].strftime('%b %Y') for item in monthly_sales]
#     monthly_data = [float(item['total']) for item in monthly_sales]

#     context = {
#         'total_medicines': total_medicines,
#         'total_expired_batches': total_expired_batches,
#         'total_suppliers': total_suppliers,
#         'total_today_sales': total_today_sales,

#         # ✅ Weekly
#         'weekly_labels': json.dumps(weekly_labels),
#         'weekly_data': json.dumps(weekly_data),

#         # Existing
#         'daily_labels': json.dumps(daily_labels),
#         'daily_data': json.dumps(daily_data),
#         'daily_sales_table': daily_sales_table,

#         'monthly_labels': json.dumps(monthly_labels),
#         'monthly_data': json.dumps(monthly_data),
#     }

#     return render(request, 'admin_dashboard.html', context)



# def admin_logout(request):
#     logout(request)
#     return redirect('admin-login')


# @login_required
# def add_medicine(request):

#     if request.method == "POST":
#         try:
#             # Medicine Data
#             medicine_name = request.POST.get("medicine_name")
#             company_name = request.POST.get("company_name")

#             # Batch Data
#             batch_no = request.POST.get("batch_no")
#             manufacture_date = request.POST.get("manufacture_date")
#             expiry_date = request.POST.get("expiry_date")
#             buy_price = request.POST.get("buy_price")
#             sell_price = request.POST.get("sell_price")
#             quantity = request.POST.get("quantity")

#             # Validation
#             if not all([medicine_name, company_name, batch_no, expiry_date, buy_price, sell_price, quantity]):
#                 messages.error(request, "All fields are required.")
#                 return redirect("add_medicine")

#             # Create or Get Medicine
#             medicine, created = Medicine.objects.get_or_create(
#                 medicine_name=medicine_name,
#                 company_name=company_name
#             )

#             # Create Batch
#             Batch.objects.create(
#                 medicine=medicine,
#                 batch_no=batch_no,
#                 manufacture_date=manufacture_date,
#                 expiry_date=expiry_date,
#                 buy_price=buy_price,
#                 sell_price=sell_price,
#                 quantity=quantity,
#                 status=True
#             )

#             messages.success(request, "Medicine and Batch added successfully.")
#             return redirect("add_medicine")

#         except Exception as e:
#             messages.error(request, f"Error: {str(e)}")
#             return redirect("add_medicine")

#     return render(request, "add_medicine.html")




# from django.db.models import Sum, Value
# from django.db.models.functions import Coalesce
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from .models import Medicine


# @login_required
# def manage_medicine(request):

#     medicines = Medicine.objects.annotate(
#         total_stock=Coalesce(Sum('batches__quantity'), Value(0))
#     ).order_by('-created_date')

    
#     if request.GET.get('delete'):
#         medicine_id = request.GET.get('delete')
#         medicine = get_object_or_404(Medicine, id=medicine_id)

        
#         if medicine.batches.exists():
#             messages.error(request, "Cannot delete medicine with existing stock (batches).")
#             return redirect('manage_medicine')

#         medicine.delete()
#         messages.success(request, "Medicine deleted successfully.")
#         return redirect('manage_medicine')

#     return render(request, 'manage_medicine.html', {
#         'medicines': medicines
#     })






# @login_required
# def edit_medicine(request, add_id):

#     medicine = get_object_or_404(Medicine, id=add_id)

#     if request.method == "POST":
#         medicine.medicine_name = request.POST.get("medicine_name")
#         medicine.company_name = request.POST.get("company_name")
#         medicine.save()

#         messages.success(request, "Medicine updated successfully.")
#         return redirect("manage_medicine")

#     return render(request, "edit_medicine.html", {
#         "medicine": medicine
#     })



# @login_required
# def expired_medicine(request):

#     today = timezone.now().date()

#     expired_batches = Batch.objects.filter(
#         expiry_date__lt=today,
#         status=True
#     ).select_related('medicine').order_by('expiry_date')

#     return render(request, "expired_medicine.html", {
#         "expired_batches": expired_batches,
#         "today": today
#     })





# from django.shortcuts import get_object_or_404, redirect

# def delete_batch(request, id):
#     batch = get_object_or_404(Batch, id=id)
#     medicine_id = batch.medicine.id
#     batch.delete()

#     return redirect('batch_list', medicine_id)







# from django.shortcuts import render, redirect
# from django.contrib import messages
# from .models import Supplier

# def add_supplier(request):
#     if request.method == 'POST':
#         supplier_name = request.POST.get('supplier_name')
#         company_name = request.POST.get('company_name')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         address = request.POST.get('address')

#         if not supplier_name or not phone:
#             messages.error(request, "Supplier Name and Phone are required!")
#             return redirect('add_supplier')

#         Supplier.objects.create(
#             supplier_name=supplier_name,
#             company_name=company_name,
#             phone=phone,
#             email=email,
#             address=address
#         )

#         messages.success(request, "Supplier Added Successfully!")
#         return redirect('add_supplier')

#     return render(request, 'add_supplier.html')




# def manage_supplier(request):
#     suppliers = Supplier.objects.all()
#     return render(request, 'manage_supplier.html', {'suppliers': suppliers})




# def edit_supplier(request, supplier_id):
#     supplier = get_object_or_404(Supplier, id=supplier_id)

#     if request.method == 'POST':
#         supplier_name = request.POST.get('supplier_name')
#         company_name = request.POST.get('company_name')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         address = request.POST.get('address')

#         if not supplier_name or not phone:
#             messages.error(request, "Supplier Name and Phone are required!")
#             return redirect('manage_supplier')

#         try:
#             supplier.supplier_name = supplier_name
#             supplier.company_name = company_name
#             supplier.phone = phone
#             supplier.email = email
#             supplier.address = address

#             supplier.save()

#             messages.success(request, "Supplier updated successfully.")
#             return redirect('manage_supplier')

#         except Exception as e:
#             messages.error(request, f"Error updating supplier: {str(e)}")
#             return redirect('manage_supplier')

#     return render(request, 'edit_supplier.html', {'supplier': supplier})




# from django.shortcuts import render, redirect
# from django.contrib import messages
# from .models import Medicine, Supplier, Batch, Purchase
# from django.utils import timezone

# def new_purchase(request):
#     medicines = Medicine.objects.all()
#     suppliers = Supplier.objects.all()

#     if request.method == "POST":
#         supplier_id = request.POST.get('supplier')
#         medicine_id = request.POST.get('medicine')
#         batch_no = request.POST.get('batch_no')
#         manufacture_date = request.POST.get('manufacture_date')
#         expiry_date = request.POST.get('expiry_date')
#         quantity = request.POST.get('quantity')
#         buy_price = request.POST.get('buy_price')
#         sell_price = request.POST.get('sell_price')
#         purchase_date = request.POST.get('purchase_date')

#         try:
#             supplier = Supplier.objects.get(id=supplier_id)
#             medicine = Medicine.objects.get(id=medicine_id)

#             # Save Purchase History
#             Purchase.objects.create(
#                 supplier=supplier,
#                 medicine=medicine,
#                 batch_no=batch_no,
#                 manufacture_date=manufacture_date,
#                 expiry_date=expiry_date,
#                 quantity=quantity,
#                 buy_price=buy_price,
#                 sell_price=sell_price,
#                 purchase_date=purchase_date
#             )

#             # Update or Create Batch (Stock)
#             batch, created = Batch.objects.get_or_create(
#                 medicine=medicine,
#                 batch_no=batch_no,
#                 defaults={
#                     'manufacture_date': manufacture_date,
#                     'expiry_date': expiry_date,
#                     'quantity': int(quantity),
#                     'buy_price': buy_price,
#                     'sell_price': sell_price,
#                     'status': True
#                 }
#             )

#             if not created:
#                 # একই batch থাকলে quantity update
#                 batch.quantity += int(quantity)
#                 batch.buy_price = buy_price  # চাইলে আপডেট করা যাবে
#                 batch.sell_price = sell_price
#                 batch.save()

#             messages.success(request, "Purchase added successfully and stock updated.")
#             return redirect('new_purchase')

#         except Exception as e:
#             messages.error(request, f"Error: {str(e)}")

#     context = {
#         'medicines': medicines,
#         'suppliers': suppliers
#     }

#     return render(request, 'new_purchase.html', context)




# def purchase_history(request):
#     purchases = Purchase.objects.select_related('supplier', 'medicine').order_by('-purchase_date')

#     context = {
#         'purchases': purchases
#     }
#     return render(request, 'purchase_history.html', context)




# from datetime import date
# from django.contrib.auth.decorators import login_required


# @login_required 
# def batch_list(request):
#     batches = Batch.objects.filter(status=True).select_related('medicine').order_by('-created_at')

#     context = {
#         'batches': batches,
#         'today': date.today()   # আজকের তারিখ template এ পাঠানো
#     }

#     return render(request, 'batch_list.html', context)





# def edit_batch(request, id):
#     batch = Batch.objects.get(id=id)

#     if request.method == "POST":
#         batch.batch_no = request.POST['batch_no']
#         batch.quantity = request.POST['quantity']
#         batch.manufacture_date = request.POST['manufacture_date']
#         batch.expiry_date = request.POST['expiry_date']
#         batch.buy_price = request.POST['buy_price']
#         batch.sell_price = request.POST['sell_price']
#         batch.status = request.POST['status']
#         batch.save()

#         return redirect('batch_list', batch.medicine.id)

#     return render(request, 'edit_batch.html', {'batch': batch})


# from django.shortcuts import render, redirect
# from django.db.models import Sum
# from django.contrib import messages
# from .models import Medicine, Batch, Sale, SaleItem
# from datetime import date
# import random


# def new_sale(request):

#     medicines = Medicine.objects.all()

#     if request.method == "POST":

#         customer_name = request.POST.get("customer_name")
#         medicine_ids = request.POST.getlist('medicine_id[]')
#         batch_ids = request.POST.getlist('batch_id[]')
#         qtys = request.POST.getlist('qty[]')

#         sale_items = []
#         total_amount = 0

#         for med_id, batch_id, qty in zip(medicine_ids, batch_ids, qtys):
#             if not qty or int(qty) <= 0:
#                 continue

#             qty = int(qty)

#             medicine = Medicine.objects.get(id=med_id)

#             batch = Batch.objects.get(
#                 id=batch_id,
#                 medicine=medicine,
#                 quantity__gt=0,
#                 status=True,
#                 expiry_date__gt=date.today()
#             )

#             if qty > batch.quantity:
#                 qty = batch.quantity

#             total = qty * batch.sell_price
#             sale_items.append({
#                 "medicine": medicine,
#                 "batch": batch,
#                 "qty": qty,
#                 "price": batch.sell_price,
#                 "total": total
#             })

#             batch.quantity -= qty
#             batch.save()

#             total_amount += total

#         if sale_items:

#             invoice = "INV" + str(random.randint(10000, 99999))

#             sale = Sale.objects.create(
#                 invoice_no=invoice,
#                 customer_name=customer_name,
#                 total_amount=total_amount
#             )

#             for item in sale_items:

#                 SaleItem.objects.create(
#                     sale=sale,
#                     medicine=item["medicine"],
#                     batch=item["batch"],
#                     price=item["price"],
#                     quantity=item["qty"],
#                     total=item["total"]
#                 )

#             messages.success(request, "Sale completed successfully")
#             return redirect("sales_history")

#         messages.error(request, "Please select at least one medicine")
#         return redirect("new_sale")
    
#     for med in medicines:

#         valid_batches = med.batches.filter(
#             status=True,
#             quantity__gt=0,
#             expiry_date__gt=date.today()
#         ).order_by('expiry_date')

#         med.valid_batches = valid_batches

#         med.total_qty = valid_batches.aggregate(
#             total=Sum('quantity')
#         )['total'] or 0

#     return render(request, "new_sale.html", {
#         "medicines": medicines
#     })



# def sales_history(request):

#     sales = Sale.objects.all().order_by("-created_at")

#     return render(request, "sales_history.html", {
#         "sales": sales
#     })






# # def invoice_list(request):
# #     sales = Sale.objects.all().order_by('-id')
# #     return render(request,'admin/invoice_list.html',{'sales':sales})



# def invoice_print(request, id):

#     sale = Sale.objects.get(id=id)

#     items = SaleItem.objects.filter(sale=sale)

#     return render(request, 'invoice_print.html', {
#         'sale': sale,
#         'items': items
#     })



# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from .models import Customer
# from .forms import CustomerForm


# # Add Customer
# def add_customer(request):
#     if request.method == "POST":
#         form = CustomerForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Customer added successfully")
#             return redirect('manage_customer')
#     else:
#         form = CustomerForm()

#     return render(request, 'add_customer.html', {'form': form})


# # Manage Customer
# def manage_customer(request):
#     customers = Customer.objects.all().order_by('-created_at')
#     return render(request, 'manage_customer.html', {'customers': customers})


# # Edit Customer
# def edit_customer(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)

#     if request.method == "POST":
#         form = CustomerForm(request.POST, instance=customer)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Customer updated successfully")
#             return redirect('manage_customer')
#     else:
#         form = CustomerForm(instance=customer)

#     return render(request, 'edit_customer.html', {'form': form})


# # Delete Customer
# def delete_customer(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)
#     customer.delete()
#     messages.success(request, "Customer deleted successfully")
#     return redirect('manage_customer')





# from django.shortcuts import render
# from django.db.models import Sum, F
# from .models import Sale, SaleItem, Batch, Medicine, Purchase
# import datetime


# def sales_report(request):
#     sales = Sale.objects.all().order_by('-created_at')  # ✅ FIXED

#     total_sales = Sale.objects.aggregate(
#         total=Sum('total_amount')
#     )['total'] or 0

#     context = {
#         'sales': sales,
#         'total_sales': total_sales
#     }
#     return render(request, 'sales_report.html', context)


# def stock_report(request):
#     batches = Batch.objects.select_related('medicine')

#     total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0

#     context = {
#         'batches': batches,
#         'total_stock': total_stock
#     }
#     return render(request, 'stock_report.html', context)


# from django.db.models import F, Sum, ExpressionWrapper, DecimalField

# def purchase_report(request):
#     purchases = Purchase.objects.all().order_by('-purchase_date')

#     # 👉 প্রতি row এর total calculate
#     purchases = purchases.annotate(
#         total=ExpressionWrapper(
#             F('quantity') * F('buy_price'),
#             output_field=DecimalField()
#         )
#     )

#     # 👉 সব purchase এর total sum
#     total_purchase = purchases.aggregate(
#         grand_total=Sum('total')
#     )['grand_total'] or 0

#     return render(request, 'purchase_report.html', {
#         'purchases': purchases,
#         'total_purchase': total_purchase
#     })





# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import update_session_auth_hash
# from django.contrib.auth.forms import PasswordChangeForm



# @login_required
# def pharmacy_settings(request):
#     return render(request, 'settings/pharmacy_settings.html')




# @login_required
# def change_password(request):
#     if request.method == 'POST':
#         form = PasswordChangeForm(user=request.user, data=request.POST)
#         if form.is_valid():
#             user = form.save()
#             update_session_auth_hash(request, user)
#             return redirect('admin-dashboard')
#     else:
#         form = PasswordChangeForm(user=request.user)

#     return render(request, 'settings/change_password.html', {'form': form})







# from .models import PharmacySettings
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages

# @login_required
# def pharmacy_settings(request):

#     settings = PharmacySettings.objects.first()

#     if request.method == "POST":
#         pharmacy_name = request.POST.get('pharmacy_name')
#         owner_name = request.POST.get('owner_name')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         address = request.POST.get('address')
#         tax = request.POST.get('tax')
#         discount = request.POST.get('discount')
#         currency = request.POST.get('currency')

#         if settings:
#             settings.pharmacy_name = pharmacy_name
#             settings.owner_name = owner_name
#             settings.phone = phone
#             settings.email = email
#             settings.address = address
#             settings.tax_percentage = tax
#             settings.discount_percentage = discount
#             settings.currency = currency

#             if request.FILES.get('logo'):
#                 settings.logo = request.FILES.get('logo')

#             settings.save()
#             messages.success(request, "Settings Updated Successfully")

#         else:
#             PharmacySettings.objects.create(
#                 pharmacy_name=pharmacy_name,
#                 owner_name=owner_name,
#                 phone=phone,
#                 email=email,
#                 address=address,
#                 tax_percentage=tax,
#                 discount_percentage=discount,
#                 currency=currency,
#                 logo=request.FILES.get('logo')
#             )
#             messages.success(request, "Settings Saved Successfully")

#         return redirect('pharmacy_settings')

#     return render(request, 'settings/pharmacy_settings.html', {
#         'settings': settings
#     })