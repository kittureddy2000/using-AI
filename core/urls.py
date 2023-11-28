# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Set as root URL
    # other site-wide URLs
]
