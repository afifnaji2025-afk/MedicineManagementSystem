from django.contrib import admin
from django.urls import path
from resultapp.views import *
from resultapp import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home - role selection page
    path('', views.home, name='home'),

    # Admin
    path('admin-login/', views.admin_login, name='admin-login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),

    # Employee
    path('employee-login/', views.employee_login, name='employee_login'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),

    # Buyer
    path('buyer-login/', views.buyer_login, name='buyer_login'),
    path('buyer-signup/', views.buyer_signup, name='buyer_signup'),
    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),

    # Medicine
    path('add-medicine/', views.add_medicine, name='add_medicine'),
    path('manage_medicine/', views.manage_medicine, name='manage_medicine'),
    path('edit-medicine/<int:add_id>/', views.edit_medicine, name='edit_medicine'),
    path('expired_medicine/', views.expired_medicine, name='expired_medicine'),

    # Supplier
    path('add_supplier/', views.add_supplier, name='add_supplier'),
    path('manage_supplier/', views.manage_supplier, name='manage_supplier'),
    path('edit_supplier/<int:supplier_id>/', views.edit_supplier, name='edit_supplier'),

    # Purchase
    path('new-purchase/', views.new_purchase, name='new_purchase'),
    path('purchase_history/', views.purchase_history, name='purchase_history'),

    # Batch
    path('batch_list/', views.batch_list, name='batch_list'),

    # Sales
    path('new_sale/', views.new_sale, name='new_sale'),
    path('sales_history/', views.sales_history, name='sales_history'),
    path('invoice_print/<int:id>/', views.invoice_print, name='invoice_print'),

    # Customer
    path('add_customer/', views.add_customer, name='add_customer'),
    path('manage_customer/', views.manage_customer, name='manage_customer'),
    path('edit_customer/<int:pk>/', views.edit_customer, name='edit_customer'),
    path('delete_customer/<int:pk>/', views.delete_customer, name='delete_customer'),

    # Reports
    path('sales-report/', views.sales_report, name='sales_report'),
    path('stock-report/', views.stock_report, name='stock_report'),
    path('purchase-report/', views.purchase_report, name='purchase_report'),

    # Settings
    path('pharmacy-settings/', views.pharmacy_settings, name='pharmacy_settings'),
    path('change-password/', views.change_password, name='change_password'),
]