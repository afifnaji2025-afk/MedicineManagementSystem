from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def admin_login(request):

    if request.user.is_authenticated:
        return redirect('admin-dashboard')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user and user.groups.filter(name='Admin').exists():
            login(request, user)
            return redirect('admin-dashboard')

        messages.error(request, "Invalid Admin credentials")

    return render(request, 'auth/admin_login.html')