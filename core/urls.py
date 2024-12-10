# core/urls.py

from django.urls import path, include
from . import views
from core.views import CustomSignupView


app_name = 'core'  # Define the namespace

urlpatterns = [

    path('', views.dashboard, name='dashboard'),  # Root URL to render the dashboard view
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('accounts/', include('allauth.urls')),  # Social login routes
    path('dashboard/', views.dashboard, name='dashboard'),  # Named 'dashboard'
    path('profile/', views.profile, name='profile'),


]



