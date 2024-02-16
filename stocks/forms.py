from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['symbol', 'name', 'quantity', 'date_purchased', 'date_sold', 'purchase_price', 'sold_price', 'comments']
        widgets = {
            'date_purchased': forms.DateInput(attrs={'type': 'date'}),
            'date_sold': forms.DateInput(attrs={'type': 'date'}),
        }
