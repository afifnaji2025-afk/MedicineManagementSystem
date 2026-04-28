from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect('admin-login')

            # Superuser = Admin
            if role == 'Admin' and request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Group check (Pharmacist / Customer)
            if request.user.groups.filter(name=role).exists():
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden("You are not authorized to view this page")

        return wrapper
    return decorator