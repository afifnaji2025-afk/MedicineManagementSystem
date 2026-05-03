from django.db import models
from django.utils.crypto import get_random_string
from django.db import models
from django.contrib.auth.models import User




class Medicine(models.Model):
    medicine_name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    company_name = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.medicine_name


class Supplier(models.Model):
    supplier_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name


class Batch(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_no = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    quantity = models.IntegerField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.medicine.medicine_name} - {self.batch_no}"


class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch_no = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    quantity = models.IntegerField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medicine.medicine_name} - {self.batch_no}"


class Sale(models.Model):
    invoice_no = models.CharField(max_length=50, unique=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            self.invoice_no = 'INV' + get_random_string(6).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_no


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.medicine.medicine_name



class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    




from django.db import models

class PharmacySettings(models.Model):
    pharmacy_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)  # ✅ fixed
    address = models.TextField()
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='tk')
    logo = models.ImageField(upload_to='pharmacy_logo/', blank=True, null=True)

    def __str__(self):
        return self.pharmacy_name  # ✅ আপনার লেখায় link ছিল, সেটাও ঠিক করুন




class InvoiceSetting(models.Model):
    invoice_prefix = models.CharField(max_length=20, default='INV-')
    
    PAPER_SIZE_CHOICES = (
        ('80mm', 'POS Thermal (80mm)'),
        ('58mm', 'POS Thermal (58mm)'),
        ('A4', 'Standard A4'),
    )
    paper_size = models.CharField(max_length=10, choices=PAPER_SIZE_CHOICES, default='80mm')
    
    terms_conditions = models.TextField(blank=True, null=True, default='Goods once sold are not returnable.')
    footer_note = models.TextField(blank=True, null=True, default='Thank you for your business!')
    show_discount = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice Settings (Prefix: {self.invoice_prefix})"