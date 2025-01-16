from django.shortcuts import render,get_object_or_404, redirect
from .models import Task,TaskList,Image, TaskHistory
from .forms import TaskForm, TaskListForm
from django.contrib.auth import login
from django.shortcuts import render
from core.utils import get_secrets
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Task
from .models import Task
from django.contrib.auth.decorators import login_required
import os
from django.http import FileResponse, Http404
from urllib.parse import quote
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import uuid
import logging
from google.cloud import storage
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse,  HttpResponse
import logging
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from pathlib import Path
from datetime import datetime, time


logger = logging.getLogger(__name__)

def send_recurrent_email():
    send_mail(
        'Subject here',
        'Here is the message.',
        'samaanaiapps@gmail.com',  # From email
        ['kittureddy2000@gmail.com'],  # To email list
        fail_silently=False,
    )

@require_POST  # Or @require_GET, depending on your setup
def trigger_email_send(request):
    # Get the secret token from environment variables
    secret_token = os.environ.get('EMAIL_TRIGGER_SECRET_TOKEN')

    # Check the provided token against the environment variable
    request_token = request.headers.get('Authorization')
    if request_token != secret_token:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    send_recurrent_email()
    return JsonResponse({'success': 'Email sent'})

def ensure_predefined_lists(user):
    predefined_lists = [
        {"name": "Past Due", "listcode": "PAST_DUE"},
        {"name": "Important", "listcode": "IMPORTANT"},
        {"name": "All Tasks", "listcode": "ALL_TASKS"},
    ]
    print("Inside ensure_predefined_lists")
    print(predefined_lists)

    # Get existing predefined lists for the user
    existing_names = TaskList.objects.filter(
        user=user, 
        list_name__in=[predefined["name"] for predefined in predefined_lists], 
        special_list=True
    ).values_list('list_name', flat=True)

    print([field.name for field in TaskList._meta.get_fields()])

    # Create any missing predefined lists
    for predefined in predefined_lists:
        if predefined["name"] not in existing_names:
            print("Creating Predefined List : " + predefined["name"])
            TaskList.objects.create(
                user=user,
                list_name=predefined["name"],
                list_code=predefined["listcode"],
                special_list=True
            )

#Get all Taks``
@login_required
def get_all_tasks(request):
    tasks = Task.objects.all().order_by('due_date')

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date','reminder_time','recurrence','task_completed',
        'important','assigned_to','creation_date','last_update_date'))  # Replace field names with the actual fields of your Task model
    
    return JsonResponse({'tasks': tasks_data})

#Get All tasks for the list
@login_required
def get_tasks_by_list(request, list_id):
    print("Function: Get Tasks with list id : " + str(list_id))
    
    sort_by = request.GET.get('sort', 'due_date')  # Replace 'default_field' with your default sort field
    order = request.GET.get('order', 'asc')
    if order == 'desc':
        sort_by = '-' + sort_by
    
    print("Sort By : " + sort_by)    
    if sort_by == 'important':
        sort_by = '-important'
    elif sort_by not in ['due_date']:
        sort_by = 'due_date'

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

    # logger.info(f"Search query: {query}, Completed: {completed}, Sort By: {sort_by}")
    
    tasks = Task.objects.filter(user=request.user)

    if query := request.GET.get('q', ''):
        tasks = tasks.filter(Q(task_name__icontains=query) | Q(task_description__icontains=query))


    filter = request.GET.get('filter')

    if filter == 'completed':
        tasks = tasks.filter(task_completed=True)
    elif filter == 'past_due':
        tasks = tasks.filter(due_date__lt=timezone.now())
    elif filter == 'all':
        tasks = tasks.all()

    sort_by = request.GET.get('sort_by')
 
    if sort_by == 'important':
        tasks = tasks.order_by('-important')
    elif sort_by in ['due_date']:
        tasks = tasks.order_by(sort_by)


    try:
        tasks_data = list(tasks.values(
            'id', 'task_name', 'list_name', 'due_date', 'task_description', 
            'reminder_time', 'recurrence', 'task_completed', 
            'important', 'assigned_to', 'creation_date', 'last_update_date'
        ))
        return JsonResponse({'tasks': tasks_data})
    except Exception as e:
        logger.error(f"Error in search_tasks: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)


#Get All Task Lists
@login_required
def get_lists(request):
    ensure_predefined_lists(request.user)

    lists = TaskList.objects.all().order_by('-special_list')
    print("List Count : " + str(lists.count()))
    args = {'task_lists': lists}
    
    return render(request, 'todos/task_dashboard.html', args)

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
    print("Task description : " + task.task_description )    

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

    
    return JsonResponse({'completed': True,'task_completed': task.task_completed, 'task_id': task_id, 'task_name': task_name})

def mark_favorite(request):
    task_id = request.POST.get('id')
    task = Task.objects.get(id=task_id)
    task_name = task.task_name
    print("Marking Task as Favorite : " + task_name)
    
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

logger = logging.getLogger(__name__)

def handle_image_upload(task, images):
  todos_attachments_dir = Path(__file__).resolve().parent / 'attachments'
  todos_attachments_dir.mkdir(exist_ok=True)

  for image in images:
        if settings.DEBUG:
            # Local storage for development
            file_name = f"{uuid.uuid4()}_{image.name}"
            file_path = todos_attachments_dir / file_name

            # Save the file locally
            with open(file_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Save the relative file path to the database
            Image.objects.create(
                task=task,
                image_url=f"/todos/attachments/{file_name}",
                image_name=image.name
            )
        else:
            #Google Cloud Storage for Production
            client = storage.Client()
            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            logger.info("Bucket Name : %s", settings.GS_BUCKET_NAME)
            
            # Create a unique filename for each image
            blob = bucket.blob(str(uuid.uuid4()))
            logger.info("Uploading image to GCS, local name: %s, GCS name: %s", image.name, blob.name)
            # Upload the image to Google Cloud Storage
            blob.upload_from_file(image, content_type=image.content_type)
            blob.make_public()
            logger.info("Image uploaded to GCS, URL: %s", blob.public_url)

            # Save the image URL in the database
            Image.objects.create(task=task, image_url=blob.public_url,image_name=image.name)


@login_required
def add_task(request, list_id):
    print("Add Task Function request method: " + request.method)

    # Fetch the task list or return a 404 error
    task_list = get_object_or_404(TaskList, id=list_id)

    if request.method == "POST":
        add_task_form = TaskForm(request.POST, request.FILES)
        print("Inside POST Request for Add Task")

        if add_task_form.is_valid():
            print("Add Task form is Valid")
            try:
                task = Task(
                    user=request.user,
                    task_name=add_task_form.cleaned_data['task_name'],
                    task_description=add_task_form.cleaned_data['task_description'],
                    due_date=add_task_form.cleaned_data['due_date'],
                    list_name=task_list,
                    reminder_time=add_task_form.cleaned_data['reminder_time'],
                    task_completed=False,
                    assigned_to=request.user.username,
                    creation_date=timezone.now(),
                    last_update_date=timezone.now(),
                )
                task.save()
                print("Task Saved")
                # Image Handling
                images = request.FILES.getlist('images')
                handle_image_upload(task, images)

                print("Task and images saved successfully.")
                return JsonResponse({'Saved': True, 'task_name': task.task_name})

            except Exception as e:
                print(f"Error occurred: {e}")
                return HttpResponse(f"Error occurred: {e}", status=500)
        else:
            print("Add Task form is not valid")
            print(add_task_form.errors)  # Debugging purpose
            return HttpResponse("Invalid form submission.", status=400)

    # Handle GET request or other methods
    else:
        print("This is a GET Request for Add Task")
        form = TaskForm(initial={'list_name': list_id})
        return render(request, "todos/add_task.html", {"add_task_form": form})

    # Fallback response to ensure all code paths return a response
    return HttpResponse("Unexpected error occurred.", status=500)

def edit_task(request, task_id):
    logger.info("Edit task Function Task id : %s", task_id)

    task = get_object_or_404(Task, id=task_id)
    images = task.images.all()
    image_data = []

    if request.method == 'POST':
        try:
            form = TaskForm(request.POST, request.FILES, instance=task)
            logger.info("Received POST request, Task id: %s", task_id)

            if form.is_valid():
                logger.info("Task form is valid, Task id: %s", task_id)
                task = form.save(commit=False)

                # Add 6:00 AM to due_date and reminder_time
                if form.cleaned_data.get('due_date'):
                    due_date = form.cleaned_data['due_date']
                    task.due_date = datetime.combine(due_date, time(6, 0))  # Combine date with 6:00 AM

                if form.cleaned_data.get('reminder_time'):
                    reminder_time = form.cleaned_data['reminder_time']
                    task.reminder_time = datetime.combine(reminder_time, time(6, 0))  # Combine date with 6:00 AM

                task.save()

                logger.info("Task saved successfully, Task id: %s", task_id)
                
                # Image Handling
                uploaded_images = request.FILES.getlist('images')
                handle_image_upload(task, uploaded_images)


                logger.info("Returning success response for edit task id : %s", task_id)
                return JsonResponse({
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'task_description': task.task_description,
                    'due_date': task.due_date.strftime('%Y-%m-%d'),
                    'important': task.important,
                    'task_completed': task.task_completed,
                    'images': image_data
                })
            else:
                logger.warning("Task form is invalid, Task id: %s", task_id)
                for field, errors in form.errors.items():
                    logger.warning("Form Field: %s,  Errors: %s", field, errors)
                return JsonResponse({'errors': form.errors}, status=400)

        except Exception as e:
            logger.error("An unexpected error occurred while processing task id : %s, Error: %s", task_id, e, exc_info=True)
            return HttpResponse(f"An error occurred: {e}", status=500)

    elif request.method == 'GET':
       try:
            form = TaskForm(instance = task)
            logger.info("Edit Task in Get method id : %s ", task_id )
            image_data = []

            for image in images:
                logger.info("Image URL: %s ; Image ID: %s", image.image_url, image.id)
                image_data.append({'url': image.image_url,'image_name': image.image_name, 'id': image.id})

            return render(request, 'todos/edit_task.html', {'edit_task_form': form,'images': images, 'task_id': task_id})
       except Exception as e:
           logger.error("An unexpected error occurred in GET method for task id %s : Error %s", task_id, e, exc_info = True)
           return HttpResponse(f"An error occurred: {e}", status=500)

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


def serve_attachment(request, path):
    logger.info("Request to serve attachment at path : %s", path)
    todos_attachments_dir = Path(__file__).resolve().parent / 'attachments'
    file_path = todos_attachments_dir / path
    logger.info("File Path: %s", file_path)
    if not file_path.exists():
        logger.warning("File does not exist at: %s", file_path)
        raise Http404("File not found.")
    try:
        response = FileResponse(open(file_path, 'rb'))
        return response
    except Exception as e:
        logger.error("Error loading file : %s ; Error : %s", file_path, e, exc_info = True)
        raise Http404(f"Error loading file")