# core/views.py (assuming 'core' is one of your apps)
import os
from django.shortcuts import render
from .utils import get_secrets
import google.auth
from google.cloud import secretmanager


def dashboard(request):

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    print("Inside Google Cloud Project Environment")

    client = secretmanager.SecretManagerServiceClient()
    settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")


    context = {'secrets': secrets}

    return render(request, 'dashboard.html',context)

