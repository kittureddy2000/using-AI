from django.urls import path,include

from . import views

app_name = 'travel'  # Set the app namespace

urlpatterns = [
    path('', views.travel, name='travel'),
    path('filter-sort/', views.filter_sort, name='filter_sort'),
    path('validate-airport-code/', views.validate_airport_code, name='validate_airport_code'),
    path('get-airport-code/<str:airport_code>/', views.get_airport_code, name='get_airport_code'),
]