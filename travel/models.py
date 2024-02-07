from django.db import models

# Create your models here.
from django.db import models

class Airport(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=200)
    city_code = models.CharField(max_length=10, blank=True, null=True)
    country_id = models.CharField(max_length=10, blank=True, null=True)
    icao = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
