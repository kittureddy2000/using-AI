# core/views.py (assuming 'core' is one of your apps)
import os
from django.shortcuts import render
from .utils import get_secrets
import google.auth
from google.cloud import secretmanager


def dashboard(request):


    return render(request, 'dashboard.html')

