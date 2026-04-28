from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from resultapp.views import *

urlpatterns = [

    path('', index, name='home'),
    path('admin-login/', admin_login, name='admin-login'),  # ❌ duplicate টা মুছে ফেলা হয়েছে
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin-logout/', admin_logout, name='admin_logout'),

    # Pharmacist
    path('pharmacist/login/', pharmacist_login, name='pharmacist-login'),
    path('pharmacist/dashboard/', pharmacist_dashboard, name='pharmacist-dashboard'),

    # Customer
    path('customer/login/', customer_login, name='customer-login'),
    path('customer/register/', register_customer, name='customer-register'),
    path('customer/dashboard/', customer_dashboard, name='customer-dashboard'),

    # Logout
    path('logout/', user_logout, name='logout'),

    # Medicine
    path('add-medicine/', add_medicine, name='add_medicine'),
    path('manage-medicine/', manage_medicine, name='manage_medicine'),
    path('edit-medicine/<int:add_id>/', edit_medicine, name='edit_medicine'),
    path('expired-medicine/', expired_medicine, name='expired_medicine'),

    # Supplier
    path('add-supplier/', add_supplier, name='add_supplier'),
    path('manage-supplier/', manage_supplier, name='manage_supplier'),
    path('edit-supplier/<int:supplier_id>/', edit_supplier, name='edit_supplier'),

    # Purchase
    path('new-purchase/', new_purchase, name='new_purchase'),
    path('purchase-history/', purchase_history, name='purchase_history'),

    # Stock / Batch
    path('batch-list/', batch_list, name='batch_list'),
    path('edit-batch/<int:id>/', edit_batch, name='edit_batch'),

    # Sales
    path('new-sale/', new_sale, name='new_sale'),           # ❌ slash missing ছিল
    path('sales-history/', sales_history, name='sales_history'),  # ❌ slash missing ছিল
    path('invoice-print/<int:id>/', invoice_print, name='invoice_print'),

    # Customer
    path('add-customer/', add_customer, name='add_customer'),
    path('manage-customer/', manage_customer, name='manage_customer'),
    path('edit-customer/<int:pk>/', edit_customer, name='edit_customer'),
    path('delete-customer/<int:pk>/', delete_customer, name='delete_customer'),

    # Reports
    path('sales-report/', sales_report, name='sales_report'),
    path('stock-report/', stock_report, name='stock_report'),
    path('purchase-report/', purchase_report, name='purchase_report'),

    # Settings
    path('pharmacy-settings/', pharmacy_settings, name='pharmacy_settings'),
    path('change-password/', change_password, name='change_password'),
    path('invoice-settings/', invoice_settings_view, name='invoice_settings'),

    path('add-user/', add_user, name='add_user'),
    path('manage-users/', manage_users, name='manage_users'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






# """StudenrResultManagementSystem URL Configuration

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/3.2/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path
# from resultapp.views import *


# urlpatterns = [


#     path('', index, name='home'),   # ✅ home page (your design)
#     path('admin-login/', admin_login, name='admin-login'),
#     path('admin-login/', admin_login, name='admin-login'),
#     path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),


      
#     # Pharmacist
#     path('pharmacist/login/', pharmacist_login, name='pharmacist-login'),
#     path('pharmacist/dashboard/', pharmacist_dashboard, name='pharmacist-dashboard'),

#     # Customer
#     path('customer/login/', customer_login, name='customer-login'),
#     path('customer/register/', register_customer, name='customer-register'),
#     path('customer/dashboard/', customer_dashboard, name='customer-dashboard'),

#     # Logout
#     path('logout/', user_logout, name='logout'),



    
#     path('add-medicine/', add_medicine, name='add_medicine'),
#     path('admin_logout/', admin_logout, name='admin_logout'),
#     path('manage_medicine/', manage_medicine, name='manage_medicine'),
#     path('edit-medicine/<int:add_id>/', edit_medicine, name='edit_medicine'),
#     path('expired_medicine/', expired_medicine, name='expired_medicine'),

#     path('add_supplier/', add_supplier, name='add_supplier'),
#     path('manage_supplier/', manage_supplier, name='manage_supplier'),
#     path('edit_supplier/<int:supplier_id>/', edit_supplier, name='edit_supplier'),

#     path('new-purchase/', new_purchase, name='new_purchase'),
#     path('purchase_history/', purchase_history, name='purchase_history'),

#     path('batch_list/', batch_list, name='batch_list'),

#     path('new_sale', new_sale, name='new_sale'),
#     path('sales_history', sales_history, name='sales_history'),

#     path('invoice_print/<int:id>/', invoice_print, name='invoice_print'),



#     path('add_customer/', add_customer, name='add_customer'),
#     path('manage_customer/', manage_customer, name='manage_customer'),
#     path('edit_customer/<int:pk>/', edit_customer, name='edit_customer'),
#     path('delete_customer/<int:pk>/', delete_customer, name='delete_customer'),



#     path('sales-report/', sales_report, name='sales_report'),
#     path('stock-report/', stock_report, name='stock_report'),
#     path('purchase-report/', purchase_report, name='purchase_report'),



#     # SETTINGS MODULE
#     path('pharmacy-settings/', pharmacy_settings, name='pharmacy_settings'),
#     path('change-password/', change_password, name='change_password'),
    
# ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)