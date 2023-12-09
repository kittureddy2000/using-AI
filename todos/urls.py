from django.urls import path,include
from . import views
from .views import register

app_name = 'todos'
urlpatterns = [
    path('', views.get_lists, name='get_lists'),
    path('add/', views.add_task, name='add_task'),
    path('get_all_tasks/', views.get_all_tasks, name='get_all_tasks'),
    path('get_lists/', views.get_lists, name='get_lists'),
    path('complete_task/', views.complete_task, name='complete_task'),
    path('mark_favorite/', views.mark_favorite, name='mark_favorite'),   
    path('edit_task/<int:task_id>/', views.edit_task, name='edit_task'),   
    path('search_tasks/', views.search_tasks, name='search_tasks'),   
    path('create_task_list/', views.create_task_list, name='create_task_list'),
    path('get_tasks/<int:list_id>/', views.get_tasks, name='get_tasks'),
    path('register/', register, name='register'),
]