from django import forms
from django.core.cache import cache
from .utils import load_airport_codes_into_cache

# Now you can call load_airport_codes_into_cache() here

class FlightSearchForm(forms.Form):
    TRIP_CHOICES = (
        ('round_trip', 'Round Trip'),
        ('one_way', 'One Way'),
        ('multi_city', 'Multi-City'),
    )

    CLASS_CHOICES = (
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first_class', 'First Class'),
    )
    trip_type = forms.ChoiceField(choices=TRIP_CHOICES, initial='round_trip', widget=forms.Select(attrs={'class': 'form-select'}))
    passengers = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    class_of_service = forms.ChoiceField(choices=CLASS_CHOICES, initial='economy', widget=forms.Select(attrs={'class': 'form-select'}))
    departure_location = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Airport Code'}))
    arrival_location = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where to?'}))
    departure_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    return_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    def clean_airport_code(self):
        code = self.cleaned_data['airport_code'].upper()
        print("Print Inside clean_airport_code  : " + code)
        codes = cache.get('airport_codes')

        if codes is None:
            # Fallback or reload codes into cache if not found
            load_airport_codes_into_cache()
            codes = cache.get('airport_codes')

        if code not in codes:
            raise forms.ValidationError("Please provide a valid airport code.")
        return code