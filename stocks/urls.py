from django.urls import path,include
from . import views

app_name = 'stocks'  # Set the app namespace

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('add_stock', views.add_stock, name='add_stock'),
]