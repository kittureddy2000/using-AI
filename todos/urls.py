from django.urls import path,include
from . import views
from .views import register

app_name = 'todos'
urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('add/', views.add_task, name='add_task'),
    path('register/', register, name='register'),
]
