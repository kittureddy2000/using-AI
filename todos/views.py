from django.shortcuts import render,get_object_or_404, redirect
from .models import Task,TaskList,Image, TaskHistory
from .forms import TaskForm, TaskListForm, CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import render
from core.utils import get_secrets
from django.core.paginator import Paginator
import google.auth
import os
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from django.forms.models import model_to_dict
import uuid
from google.cloud import storage
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from google.cloud import secretmanager
from django.contrib import messages
from django.http import JsonResponse,  HttpResponse
from django.core import serializers
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
import logging

logger = logging.getLogger(__name__)

#Get all Taks``
def get_all_tasks(request):
    page = request.GET.get('page', 1)
    tasks = Task.objects.all().order_by('due_date')
    paginator = Paginator(tasks, 50)  # Show 10 tasks per page 
    logger.info("This is an info log message from get_all_tasks.")

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
        'important','assigned_to','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task model
    
    return JsonResponse({'tasks': tasks_data,'total_pages': paginator.num_pages,'current_page': page})

#Get All tasks for the list
def get_tasks_by_list(request, list_id):
    print("Function: Get Tasks with list id : " + str(list_id))
    
    sort_by = request.GET.get('sort', 'due_date')  # Replace 'default_field' with your default sort field
    order = request.GET.get('order', 'asc')
    if order == 'desc':
        sort_by = '-' + sort_by
    
    print("Sort By : " + sort_by)    
    tasklist = TaskList.objects.get(id=list_id)
    print("List Name : "  + tasklist.list_name)

    if(tasklist.special_list):
        if(tasklist.list_code == "IMPORTANT"):
            tasks = Task.objects.filter(important=True).order_by(sort_by)
        elif(tasklist.list_code == "PAST_DUE"):
            tasks = Task.objects.filter(due_date__lt=timezone.now()).order_by(sort_by)
        elif(tasklist.list_code == "ALL_TASKS"):
            tasks = Task.objects.all().order_by(sort_by)
    else :    
        tasks = Task.objects.filter(list_name=tasklist).order_by(sort_by)
    
    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task model
    return JsonResponse({'tasks': tasks_data})
# views.py

#Live Search Tasks
def search_tasks(request):
    query = request.GET.get('q', '')  # Get the search term from the request
    tasks = Task.objects.filter(task_name__icontains=query) | Task.objects.filter(task_description__icontains=query)

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task mode

    return JsonResponse({'tasks': tasks_data})

#Get All Task Lists
def get_lists(request):
    lists = TaskList.objects.all().order_by('-special_list')
    print("List Count : " + str(lists.count()))
    task = get_object_or_404(Task, id=57)  
    print("Task Name : " + task.task_name)
    form = TaskForm(instance = task)
    images = task.images.all()
    image_data = []
    for image in images:
        image_data.append({'url': image.image_url,'image_name': image.image_name, 'id': image.id})
            
    args = {'task_lists': lists,'edit_task_form': form,'images': images}
    print("After Args")
    
    return render(request, 'todos/task_dashboard.html', args)

# Function to Add the Task
def add_task(request, list_id):
    print("Add Task Function request method : " + request.method)
    
    try:
        task_list = TaskList.objects.get(id=list_id)
        list_name = task_list.list_name
    except TaskList.DoesNotExist:
        list_name = None  # Or handle the case where the list doesn't exist

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
                
                list_name = add_task_form.cleaned_data['list_name']
                task.list_name = list_name
                #print("List Name : " + task.list_name)

                print(request.user.username)
                print(request.user.id)

                task.reminder_time = task.due_date
                task.task_completed = False
                task.assigned_to = request.user.username
                task.creation_date = timezone.now()
                task.last_update_date = timezone.now()
                task.save()

            #Image Handling 
                
                images = request.FILES.getlist('images')
                # Google Cloud Storage setup
                client = storage.Client()
                bucket = client.get_bucket(settings.GS_BUCKET_NAME)
                print("Bucket Name : " + settings.GS_BUCKET_NAME)
                
                for image in images:
                    # Create a unique filename for each image
                    blob = bucket.blob(str(uuid.uuid4()))
                    print("Local image Name :  " + image.name)

                    # Upload the image to Google Cloud Storage
                    blob.upload_from_file(image, content_type=image.content_type)
                    
                        # Make the blob publicly accessible
                    blob.make_public()

                    print("Image Url : " + blob.public_url)
                    # Save the image URL in the database
                    Image.objects.create(task=task, image_url=blob.public_url,image_name=image.name)

                
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
        form = TaskForm(initial={'list_name': list_id})
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
    print("In Complete Task Function Task ID : " + task_id)
    
    task = Task.objects.get(id=task_id)
    task.task_completed = True
    task.last_update_date = timezone.now()    
    task_name = task.task_name
    if(task.recurrence == Task.DAILY):
        print("Task is Daily")
        task.due_date = task.due_date + timedelta(days=1)
        task.reminder_time = task.reminder_time + timedelta(days=1)
    elif(task.recurrence == Task.WEEKLY):
        print("Task is Weekly")
        task.due_date = task.due_date + timedelta(days=7)
        task.reminder_time = task.reminder_time + timedelta(days=7)
    elif(task.recurrence == Task.MONTHLY):
        print("Task is Monthly")
        task.due_date = task.due_date + relativedelta(months=1)
        task.reminder_time = task.reminder_time + relativedelta(months=1)
    elif(task.recurrence == Task.YEARLY):
        print("Task is Yearly")
        task.due_date = task.due_date + relativedelta(years=1)
        task.reminder_time = task.reminder_time + relativedelta(years=1)


    task.save()


    if(task.task_completed ) :
        task_history = TaskHistory(
        user=task.user,
        task_name=task.task_name,
        list_name=task.list_name,
        task_description=task.task_description,
        due_date=task.due_date,
        reminder_time=task.reminder_time,
        recurrence=task.recurrence,
        task_completed=task.task_completed,
        important=task.important,
        assigned_to=task.assigned_to,
        creation_date=task.creation_date,
        last_update_date=task.last_update_date
        )
        task_history.save()

    
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
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Task

def get_task_details(request, task_id):
    print("Function: Get Tasks Details " + str(task_id))

    # Use get_object_or_404 to get the task or return a 404 response if not found
    task = get_object_or_404(Task, id=task_id)
    print("Task Name : " + task.task_name)
    print("Task Description : " + task.task_description)
    print("Task Due Date : " + task.due_date.strftime("%m/%d/%Y"))  # Corrected date format

    # Construct the task data dictionary manually
    task_data = {
        'id': task.id,
        'task_name': task.task_name,
        #'list_name': task.list_name.name if task.list_name else None,  # Assuming list_name is a ForeignKey
        'due_date': task.due_date.strftime("%m/%d/%Y"),
        'task_description': task.task_description,
        'reminder_time': task.reminder_time.strftime("%m/%d/%Y, %H:%M") if task.reminder_time else None,
        'recurrence': task.recurrence,
        'task_completed': task.task_completed,
        'important': task.important,
        'assigned_to': task.assigned_to,
        'creation_date': task.creation_date.strftime("%m/%d/%Y, %H:%M"),
        'last_update_date': task.last_update_date.strftime("%m/%d/%Y, %H:%M"),
    }

    return JsonResponse(task_data)

def edit_task(request, task_id):
    print("Task id : " + str(task_id))
    task = get_object_or_404(Task, id=task_id)
    print("Edit Task Method :  "+request.method +  " ; Task id : " + str(task_id) )
    images = task.images.all()
    image_data = []
        
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        print("Edit Task Method :  "+request.method +  " ; Task id : " + str(task_id) )
        try :
            if form.is_valid():
                form.save()
                print("Task Saved")
                images = request.FILES.getlist('images')
                # Google Cloud Storage setup
                #client = storage.Client()
                #bucket = client.get_bucket(settings.GS_BUCKET_NAME)
                #print("Bucket Name : " + settings.GS_BUCKET_NAME)
                
                #for image in images:
                    # Create a unique filename for each image
                #    blob = bucket.blob(str(uuid.uuid4()))
                #    print("Local image Name :  " + image.name)

                    # Upload the image to Google Cloud Storage
                #    blob.upload_from_file(image, content_type=image.content_type)

                #    print("Image Url : " + blob.public_url)
                    # Save the image URL in the database
                #    Image.objects.create(task=task, image_url=blob.public_url,image_name=image.name)
                    
                return JsonResponse({    'task_id': task.id,
                    'task_name': task.task_name,
                    'task_description': task.task_description,
                    'due_date': task.due_date.strftime('%Y-%m-%d'),  # Adjust date format as needed
                    'important': task.important,
                    'task_completed': task.task_completed,
                    'images': image_data})
            
        except Exception as e:
                    # Log the error message or print it to the console
                    print(f"Error occurred: {e}")
                    # Optionally, return an error response
                    return HttpResponse(f"Error occurred: {e}", status=500)   
    elif request.method == 'GET':
        form = TaskForm(instance = task)
        print("Edit Task in Get method ")
        image_data = []

        for image in images:
            print("Image URL:", image.image_url)  # Print the URL of each image
            print("Image ID:", image.id)         # Print the ID of each image
            image_data.append({'url': image.image_url,'image_name': image.image_name, 'id': image.id})
        
    return render(request, 'todos/edit_task.html', {'edit_task_form': form,'images': images, 'task_id': task_id})


def edit_task_in_panel(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    form = TaskForm(instance=task)
    print("Add Task Method :  "+request.method +  " ; Task id : " + str(task_id) )
    # Render your form template with the form context, and return as HTML
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


from django.shortcuts import render, get_object_or_404, redirect
from .models import Task

def completed_tasks(request):
    print("In Completed Tasks : ")
    # Get all completed tasks and render them in the "completed_tasks.html"
    completed_tasks = Task.objects.filter(task_completed=True)
    return render(request, 'todos/completed_tasks.html', {'completed_tasks': completed_tasks})

#delete tasks
def delete_tasks(request):
    tasks = Task.objects.all()

    if request.method == 'POST':
        print("In Delete Tasks Function")
        task_ids = request.POST.getlist('selected_tasks')
        Task.objects.filter(id__in=task_ids).delete()
        messages.success(request, 'Selected tasks have been deleted.')

        return redirect('todos:delete_tasks')

    return render(request, 'todos/delete_tasks.html', {'tasks': tasks})


def undelete_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, task_completed=True)
        task.task_completed = False
        task.save()
        return JsonResponse({'status': 'success', 'message': 'Task reactivated successfully.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
