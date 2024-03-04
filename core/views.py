# core/views.py (assuming 'core' is one of your apps)
import os
from django.shortcuts import render
from .utils import get_secrets
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm

def dashboard(request):
    return render(request, 'dashboard.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('core:login')  # Assuming your app's namespace is 'todos'
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('/')  # Redirect to a new URL for confirmation or back to the profile
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'core/profile_update.html', {'form': form})