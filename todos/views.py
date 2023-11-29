from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm, CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import render
from core.utils import get_secrets
import google.auth
import os
from google.cloud import secretmanager



def task_list(request):
    print("task_list: In Task List")
    tasks = Task.objects.all().order_by('-created_at')
    print("task_list: After getting list of objects")
    for task in tasks:
    print(task)

    return render(request, 'todos/list.html', {'tasks': tasks})

def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('todos:task_list')
    else:
        form = TaskForm()
    return render(request, 'todos/add.html', {'form': form }) 

def profile(request):
    return render(request, 'users/profile.html')  # or redirect to another page


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            print("Log : Register dddd Save")
            # Specify the backend to use
            backend = 'django.contrib.auth.backends.ModelBackend'  # Adjust if using a different backend
            user.backend = backend

            login(request, user, backend=backend)
            return redirect('login')  # Redirect to home or other appropriate page
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

