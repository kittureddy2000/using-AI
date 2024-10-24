# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import CustomSignupForm,CustomUserUpdateForm  # Custom forms
from allauth.account.views import SignupView
from core.utils import get_logger


logger = get_logger(__name__)

def dashboard(request):
    return render(request, 'core/dashboard.html')

class CustomSignupView(SignupView):
    template_name = 'account/signup.html'
    logger.info('Log : CustomSignupView template_name')

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Log : CustomSignupView form_valid")
        username = form.cleaned_data.get('username')
        logger.info("User" + username + "signed up successfully.")
        return response

    def form_invalid(self, form):
        user_input = {
            'username': form.cleaned_data.get('username', ''),
            'email': form.cleaned_data.get('email', ''),
            # Include other fields as needed
        }
        logger.info("Signup form is invalid.")

        for field, errors in form.errors.items():
            for error in errors:
                logger.info(f"Error in {field}: {error}")

        print(f"Form errors: {form.errors.as_json()}")

        return super().form_invalid(form)


@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:dashboard')  # Redirect to the same profile page after successful update
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserUpdateForm(instance=request.user)  # Pre-fill form with the current user’s data

    return render(request, 'core/dashboard.html', {'form': form})  # Render profile.html in the 'account' folder
