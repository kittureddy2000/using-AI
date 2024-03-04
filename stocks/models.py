from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Stock(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.IntegerField()
    date_purchased = models.DateField(null=True, blank=True)
    date_sold = models.DateField(null=True, blank=True)  # Optional
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Optional
    source = models.CharField(max_length=100, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)  # Optional

    def __str__(self):
        return f"{self.symbol} - {self.name}"
