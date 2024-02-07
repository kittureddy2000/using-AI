# In your_app/utils.py
from django.core.cache import cache
from .models import Airport

def load_airport_codes_into_cache():
    from .models import Airport
    print("Inside Utils.load_airport_codes_into_cache")
    codes = list(Airport.objects.values_list('code', flat=True))
    cache.set('airport_codes', codes, timeout=None)  # 'None' for indefinite caching
