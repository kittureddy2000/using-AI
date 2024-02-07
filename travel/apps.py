from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TravelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'travel'
    
    def ready(self):
        from django.core.cache import cache
        from .models import Airport 
        
        def load_airport_codes(sender, **kwargs):
            codes = Airport.objects.all().values_list('code', flat=True)
            cache.set('airport_codes', list(codes), None)
        
        post_migrate.connect(load_airport_codes, sender=self)