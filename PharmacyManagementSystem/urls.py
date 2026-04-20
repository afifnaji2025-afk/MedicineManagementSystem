"""StudenrResultManagementSystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from resultapp.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', admin_login, name='home'),
    path('admin-login/', admin_login, name='admin-login'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    
    path('add-medicine/', add_medicine, name='add_medicine'),
    path('admin_logout/', admin_logout, name='admin_logout'),
    path('manage_medicine/', manage_medicine, name='manage_medicine'),
    path('edit-medicine/<int:add_id>/', edit_medicine, name='edit_medicine'),
    path('expired_medicine/', expired_medicine, name='expired_medicine'),

    path('add_supplier/', add_supplier, name='add_supplier'),
    path('manage_supplier/', manage_supplier, name='manage_supplier'),
    path('edit_supplier/<int:supplier_id>/', edit_supplier, name='edit_supplier'),

    path('new-purchase/', new_purchase, name='new_purchase'),
    path('purchase_history/', purchase_history, name='purchase_history'),

    path('batch_list/', batch_list, name='batch_list'),

    path('new_sale', new_sale, name='new_sale'),
    path('sales_history', sales_history, name='sales_history'),

    path('invoice_print/<int:id>/', invoice_print, name='invoice_print'),



    path('add_customer/', add_customer, name='add_customer'),
    path('manage_customer/', manage_customer, name='manage_customer'),
    path('edit_customer/<int:pk>/', edit_customer, name='edit_customer'),
    path('delete_customer/<int:pk>/', delete_customer, name='delete_customer'),



    path('sales-report/', sales_report, name='sales_report'),
    path('stock-report/', stock_report, name='stock_report'),
    path('purchase-report/', purchase_report, name='purchase_report'),



    # SETTINGS MODULE
    path('pharmacy-settings/', pharmacy_settings, name='pharmacy_settings'),
    path('change-password/', change_password, name='change_password'),
    
]