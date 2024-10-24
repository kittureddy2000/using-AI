# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    profile_picture = forms.ImageField(required=False, label="Profile Picture")

    def save(self, request):
        user = super().save(request)
        # Access the Profile instance created by the signal
        profile = user.profile
        profile.profile_picture = self.cleaned_data.get('profile_picture')
        profile.save()
        return user

class CustomUserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_image']  # Add the fields you want to be editable in the profile

    # Customize widgets if you want to style the fields
    profile_image = forms.ImageField(required=False, widget=forms.ClearableFileInput)

    # Additional form validation or customization can go here    
