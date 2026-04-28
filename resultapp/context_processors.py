# resultapp/context_processors.py

from .models import PharmacySettings

def pharmacy_info(request):
    return {
        'pharmacy_info': PharmacySettings.objects.first()
    }