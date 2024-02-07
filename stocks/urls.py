from django.urls import path,include
from . import views

app_name = 'stocks'  # Set the app namespace

urlpatterns = [
    path('', views.stocks, name='stocks'),
]