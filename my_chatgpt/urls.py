from django.contrib import admin
from django.urls import path
from my_chatgpt import views

app_name = 'my_chatgpt'  # Set the app namespace

urlpatterns = [
    path('chat_gpt/', views.chat_gpt, name='chat_gpt'),
    path('chatgpt-response/', views.chatgpt_response, name='chatgpt_response'),
]
