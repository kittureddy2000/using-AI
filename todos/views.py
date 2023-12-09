from django.shortcuts import render,get_object_or_404, redirect
from .models import Task,TaskList
from .forms import TaskForm, TaskListForm, CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import render
from core.utils import get_secrets
from django.core.paginator import Paginator
import google.auth
import os
from django.urls import reverse
from django.utils import timezone
from google.cloud import secretmanager
from django.contrib import messages
from django.http import JsonResponse,  HttpResponse
from django.core import serializers
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

#Get all Taks
def get_all_tasks(request):
    page = request.GET.get('page', 1)
    tasks = Task.objects.all().order_by('due_date')
    paginator = Paginator(tasks, 5)  # Show 10 tasks per page 

    try:
        tasks_page = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer, deliver first page.
        tasks_page = paginator.page(1)
    except EmptyPage:
    # If page is out of range, deliver last page of results.
        tasks_page = paginator.page(paginator.num_pages)

    tasks_data = list(tasks_page.object_list.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','task_image','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task model
    
    return JsonResponse({'tasks': tasks_data,'total_pages': paginator.num_pages,'current_page': page})

#Get All tasks for the list
def get_tasks(request, list_id):
    print("Function: Get Tasks with list id : " + str(list_id))
    tasklist = TaskList.objects.get(id=list_id)
    print("List Name : "  + tasklist.list_name)

    tasks = Task.objects.filter(list_name=tasklist).order_by('due_date')
    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','task_image','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task model
    return JsonResponse({'tasks': tasks_data})
# views.py

#Live Search Tasks
def search_tasks(request):
    query = request.GET.get('q', '')  # Get the search term from the request
    tasks = Task.objects.filter(task_name__icontains=query) | Task.objects.filter(task_description__icontains=query)

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','task_image','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task mode

    return JsonResponse({'tasks': tasks_data})

#Get All Task Lists
def get_lists(request):
    lists = TaskList.objects.all().order_by('-special_list')
    args = {'task_lists': lists}
    return render(request, 'todos/task_dashboard.html', args)

# Function to Add the Task
def add_task(request):
    print("Add Task Function request method : " + request.method)

    if request.method == "POST":
        add_task_form = TaskForm(request.POST)
        print("Inside POST Request for Add Task")
        if add_task_form.is_valid():
            print("Add Task form is Valid")
            try:
                task = Task()

                task.task_name = add_task_form.cleaned_data['task_name']
                task.task_description = add_task_form.cleaned_data['task_description']
                task.due_date = add_task_form.cleaned_data['due_date']

                print(" Task Name : " + task.task_name)
                print(" task_description : " + task.task_description)
                print(" due_date : " + task.due_date.strftime("%m:%d:%Y"))
                
                list_name = add_task_form.cleaned_data['list_name']
                print(list_name)
                #list_item = TaskList.objects.get(list_name=list_name)
                task.list_name = list_name
                print(task.list_name)

                print(request.user.username)
                print(request.user.id)

                task.reminder_Time = timezone.now()
                task.task_completed = False
                task.assigned_to = request.user.username
                task.creation_date = timezone.now()
                task.last_update_date = timezone.now()

                task.save()
                print("After Saving Task")
                #return redirect('todos:get_lists')
                return JsonResponse({'Saved': True, 'task_name': task.task_name})

            except Exception as e:
                    # Log the error message or print it to the console
                    print(f"Error occurred: {e}")
                    # Optionally, return an error response
                    return HttpResponse(f"Error occurred: {e}", status=500)
        else:
            print("Add Task form is not Valid")
            print(add_task_form.errors)  # Add this line for debugging

    else:
        print("This is GET Request in Add Task :")

    form = TaskForm()
    context = {'add_task_form': form}

    return render(request, "todos/add_task.html", context)

# views.py


def create_task_list(request):
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('todos:get_lists')
    else:
        form = TaskListForm()  # An unbound form

    return render(request, 'todos/task_lists.html', {'form': form})


def complete_task(request):
    task_id = request.POST.get('id')
    task = Task.objects.get(id=task_id)
    task_name = task.task_name
    task.task_completed = True
    task.save()
    return JsonResponse({'completed': True, 'task_name': task_name})

def mark_favorite(request):
    task_id = request.POST.get('id')
    task = Task.objects.get(id=task_id)
    task_name = task.task_name
    print("Mark Favorite : " + task_name)
    
    if task.important :
        task.important = False
    else : 
        task.important = True    
    task.save()

    print("Task Saved in Mark_Favorite : " )
    if(task.important) : 
        print("Task is important True ")
    else : 
        print("Task important : False ")
    
    return JsonResponse({'Important': task.important , 'task_name': task_name, 'task_id' : task_id})

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    print("Edit Task Method :  "+request.method +  " ; Task id in Edit Task : " + str(task_id) )
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        try :
            if form.is_valid():
                form.save()
                return JsonResponse({    'task_id': task.id,
                    'task_name': task.task_name,
                    'task_description': task.task_description,
                    'due_date': task.due_date.strftime('%Y-%m-%d'),  # Adjust date format as needed
                    'important': task.important,
                    'task_completed': task.task_completed})
            
        except Exception as e:
                    # Log the error message or print it to the console
                    print(f"Error occurred: {e}")
                    # Optionally, return an error response
                    return HttpResponse(f"Error occurred: {e}", status=500)   
    elif request.method == 'GET':
        form = TaskForm(instance = task)
        print("Edit Task in Get method ")
                
    return render(request, 'todos/edit_task.html', {'edit_task_form': form})

def profile(request):
    return render(request, 'users/profile.html')  # or redirect to another page

#Register Form
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

