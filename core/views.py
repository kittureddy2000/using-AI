# core/views.py (assuming 'core' is one of your apps)

from django.shortcuts import render
from .utils import get_secrets

def dashboard(request):

   project_id = 'using-ai-405105'
   secret_ids = ['PROD_SECRET_KEY', 'DB_NAME','DB_USER', 'DB_HOST','DB_PORT']  # Add your secret IDs

   secrets = get_secrets(project_id,secret_ids)

   context = {
        'secrets': secrets,
   }

   return render(request, 'dashboard.html',context)

