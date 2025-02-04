from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, TaskList, Image, TaskHistory
from .forms import TaskForm, TaskListForm
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from urllib.parse import quote
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import uuid
import logging
from google.cloud import storage
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import logging
from django.views.decorators.http import require_POST
from pathlib import Path
from datetime import datetime, time as dt_time
from googleapiclient.discovery import build
import time
from dateutil import parser as date_parser
from django.shortcuts import redirect
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
from core.models import UserToken  
import msal
from core.utils import refresh_microsoft_token, is_token_expired  # Import the utility functions
import requests




logger = logging.getLogger(__name__)

# def trigger_email_send(request):
#     # Get the secret token from environment variables
#     secret_token = os.environ.get('EMAIL_TRIGGER_SECRET_TOKEN')

#     # Check the provided token against the environment variable
#     request_token = request.headers.get('Authorization')
#     if request_token != secret_token:
#         return JsonResponse({'error': 'Unauthorized'}, status=401)

#     send_recurrent_email()
#     return JsonResponse({'success': 'Email sent'})

# Ensure predefined lists exist for the user
def ensure_predefined_lists(user):
    predefined_lists = [
        {"name": "Past Due", "listcode": "PAST_DUE"},
        {"name": "Important", "listcode": "IMPORTANT"},
        {"name": "All Tasks", "listcode": "ALL_TASKS"},
        {"name": "Google Tasks", "listcode": "GOOGLE_TASKS"},
        {"name": "MS Tasks", "listcode": "MS_TASKS"},
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


# Get all Taks triggered at the start of page load
@login_required
def get_all_tasks(request):
    logger.info("In Get All Tasks function")
    # sync_google_tasks(request)
    # sync_microsoft_tasks(request)
    tasks = Task.objects.filter(user=request.user, task_completed=False).order_by('due_date')

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date', 'reminder_time', 'recurrence',
        'task_completed',
        'important', 'assigned_to', 'creation_date', 'last_update_date'))  # Replace field names with the actual fields of your Task model

    return JsonResponse({'tasks': tasks_data})


# Get All tasks for the given list
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

    tasklist = TaskList.objects.get(id=list_id, user=request.user)
    print("List Name : " + tasklist.list_name)

    if tasklist.special_list:
        if tasklist.list_code == "IMPORTANT":
            tasks = Task.objects.filter(user=request.user, important=True, task_completed=False).order_by(sort_by)
        elif tasklist.list_code == "PAST_DUE":
            tasks = Task.objects.filter(user=request.user, due_date__lt=timezone.now(), task_completed=False).order_by(sort_by)
        elif tasklist.list_code == "ALL_TASKS":
            tasks = Task.objects.filter(user=request.user, task_completed=False).order_by(sort_by)
        elif tasklist.list_code == "GOOGLE_TASKS":
            tasks = Task.objects.filter(user=request.user, source="google", task_completed=False).order_by(sort_by)
        elif tasklist.list_code == "MS_TASKS":
            tasks = Task.objects.filter(user=request.user, task_completed=False,source="microsoft").order_by(sort_by)    
    else:
        tasks = Task.objects.filter(user=request.user, list_name=tasklist, task_completed=False).order_by(sort_by)

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date', 'reminder_time', 'recurrence',
        'task_completed',
        'important', 'assigned_to', 'creation_date', 'last_update_date'))  # Replace field names with the actual fields of your Task model
    return JsonResponse({'tasks': tasks_data})


# views.py

# Live Search Tasks
def search_tasks(request):
    # Get the query and filter parameters from GET
    query = request.GET.get('q', '')
    filter_param = request.GET.get('filter')

    # Choose the base queryset based on the filter.
    # By default, we show only active (not completed) tasks.
    if filter_param == 'completed':
        tasks = Task.objects.filter(user=request.user, task_completed=True)
    elif filter_param == 'all':
        tasks = Task.objects.filter(user=request.user)
    elif filter_param == 'past_due':
        # Show past-due tasks that are not completed.
        tasks = Task.objects.filter(user=request.user, task_completed=False, due_date__lt=timezone.now())
    else:
        # Default: active tasks only (not completed)
        tasks = Task.objects.filter(user=request.user, task_completed=False)

    # If a search query is provided, filter by task name or description.
    if query:
        tasks = tasks.filter(Q(task_name__icontains=query) | Q(task_description__icontains=query))

    # Sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'important':
        tasks = tasks.order_by('-important')
    elif sort_by in ['due_date']:
        tasks = tasks.order_by(sort_by)

    try:
        tasks_data = list(
            tasks.values(
                'id', 
                'task_name', 
                'list_name', 
                'due_date', 
                'task_description',
                'reminder_time', 
                'recurrence', 
                'task_completed',
                'important', 
                'assigned_to', 
                'creation_date', 
                'last_update_date'
            )
        )
        return JsonResponse({'tasks': tasks_data})
    except Exception as e:
        logger.error(f"Error in search_tasks: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

# Get All Task Lists that renders the sidebar:
@login_required
def get_lists(request):
    # Ensure predefined lists are created
    ensure_predefined_lists(request.user)
    # Get all task lists for the user, ordered so that special lists come first.
    task_lists = TaskList.objects.filter(user=request.user).order_by('-special_list', 'list_name')
    
    # Split task lists into special and normal lists
    special_lists = task_lists.filter(special_list=True)
    normal_lists = task_lists.filter(special_list=False)
    
    context = {
        'special_lists': special_lists,
        'normal_lists': normal_lists,
    }
    return render(request, 'task_management/task_dashboard.html', context)



def create_task_list(request):
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            task_list = form.save(commit=False)
            task_list.user = request.user
            task_list.save()

            return redirect('task_management:get_lists')
    else:
        form = TaskListForm()  # An unbound form

    return render(request, 'task_management/task_lists.html', {'form': form})


def complete_task(request):
    task_id = request.POST.get('id')
    print("In Complete Task Function Task ID : " + task_id)

    task = Task.objects.get(id=task_id, user=request.user)
    task.task_completed = True
    task.last_update_date = timezone.now()
    task_name = task.task_name
    if task.recurrence == Task.DAILY:
        print("Task is Daily")
        task.due_date = task.due_date + timedelta(days=1)
        task.reminder_time = task.reminder_time + timedelta(days=1)
    elif task.recurrence == Task.WEEKLY:
        print("Task is Weekly")
        task.due_date = task.due_date + timedelta(days=7)
        task.reminder_time = task.reminder_time + timedelta(days=7)
    elif task.recurrence == Task.MONTHLY:
        print("Task is Monthly")
        task.due_date = task.due_date + relativedelta(months=1)
        task.reminder_time = task.reminder_time + relativedelta(months=1)
    elif task.recurrence == Task.YEARLY:
        print("Task is Yearly")
        task.due_date = task.due_date + relativedelta(years=1)
        task.reminder_time = task.reminder_time + relativedelta(years=1)

    task.save()

    if task.task_completed:
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
            last_update_date=task.last_update_date,
            source_id=task.source_id,
            source=task.source   
        )
        task_history.save()

    return JsonResponse({'completed': True, 'task_completed': task.task_completed, 'task_id': task_id, 'task_name': task_name})


def mark_favorite(request):
    task_id = request.POST.get('id')
    task = Task.objects.get(id=task_id, user=request.user)
    task_name = task.task_name
    print("Marking Task as Favorite : " + task_name)

    if task.important:
        task.important = False
    else:
        task.important = True
    task.save()

    print("Task Saved in Mark_Favorite : ")
    if task.important:
        print("Task is important True ")
    else:
        print("Task important : False ")

    return JsonResponse({'Important': task.important, 'task_name': task_name, 'task_id': task_id})


def get_task_details(request, task_id):
    print("Function: Get Tasks Details " + str(task_id))

    # Use get_object_or_404 to get the task or return a 404 response if not found
    task = get_object_or_404(Task, id=task_id, user=request.user)
    print("Task Name : " + task.task_name)
    print("Task Description : " + task.task_description)
    print("Task Due Date : " + task.due_date.strftime("%m/%d/%Y"))  # Corrected date format

    # Construct the task data dictionary manually
    task_data = {
        'id': task.id,
        'task_name': task.task_name,
        # 'list_name': task.list_name.name if task.list_name else None,  # Assuming list_name is a ForeignKey
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
    task_management_attachments_dir = Path(__file__).resolve().parent / 'attachments'
    task_management_attachments_dir.mkdir(exist_ok=True)

    for image in images:
        if settings.DEBUG:
            # Local storage for development
            file_name = f"{uuid.uuid4()}_{image.name}"
            file_path = task_management_attachments_dir / file_name

            # Save the file locally
            with open(file_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Save the relative file path to the database
            Image.objects.create(
                task=task,
                image_url=f"/task_management/attachments/{file_name}",
                image_name=image.name
            )
        else:
            # Google Cloud Storage for Production
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
            Image.objects.create(task=task, image_url=blob.public_url, image_name=image.name)


@login_required
def add_task(request, list_id):
    print("Add Task Function request method: " + request.method)

    # Fetch the task list or return a 404 error
    task_list = get_object_or_404(TaskList, id=list_id, user=request.user)
    image_data = []

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


                logger.info("Returning success response for Create task id : %s", task.task_name)
                return JsonResponse({
                    'id': task.id,
                    'task_name': task.task_name,
                    'task_description': task.task_description,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'important': task.important,
                    'task_completed': task.task_completed,
                    'images': image_data
                })
            

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
        return render(request, "task_management/add_task.html", {"add_task_form": form})

    # Fallback response to ensure all code paths return a response
    return HttpResponse("Unexpected error occurred.", status=500)


def edit_task(request, task_id):
    logger.info("Edit task Function Task id : %s", task_id)

    task = get_object_or_404(Task, id=task_id, user=request.user)
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
                    task.due_date = datetime.combine(due_date, dt_time(6, 0))  # Combine date with 6:00 AM

                if form.cleaned_data.get('reminder_time'):
                    reminder_time = form.cleaned_data['reminder_time']
                    task.reminder_time = datetime.combine(reminder_time, dt_time(6, 0))  # Combine date with 6:00 AM

                task.save()

                logger.info("Task saved successfully, Task id: %s", task_id)

                # Image Handling
                uploaded_images = request.FILES.getlist('images')
                handle_image_upload(task, uploaded_images)

                logger.info("Returning success response for edit task id : %s", task_id)
                return JsonResponse({
                    'id': task.id,
                    'task_name': task.task_name,
                    'task_description': task.task_description,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
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
            form = TaskForm(instance=task)
            logger.info("Edit Task in Get method id : %s ", task_id)
            image_data = []

            for image in images:
                logger.info("Image URL: %s ; Image ID: %s", image.image_url, image.id)
                image_data.append({'url': image.image_url, 'image_name': image.image_name, 'id': image.id})

            return render(request, 'task_management/edit_task.html', {'edit_task_form': form, 'images': images, 'task_id': task_id})
        except Exception as e:
            logger.error("An unexpected error occurred in GET method for task id %s : Error %s", task_id, e,
                         exc_info=True)
            return HttpResponse(f"An error occurred: {e}", status=500)


def edit_task_in_panel(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    form = TaskForm(instance=task)
    print("Add Task Method :  " + request.method + " ; Task id : " + str(task_id))
    # Render your form template with the form context, and return as HTML
    return render(request, 'task_management/edit_task.html', {'edit_task_form': form})



def completed_tasks(request):
    print("In Completed Tasks : ")
    # Get all completed tasks and render them in the "completed_tasks.html"
    completed_tasks = Task.objects.filter(user=request.user, task_completed=True)
    return render(request, 'task_management/completed_tasks.html', {'completed_tasks': completed_tasks})


# delete tasks
def delete_tasks(request):
    tasks = Task.objects.filter(user=request.user)

    if request.method == 'POST':
        print("In Delete Tasks Function")
        task_ids = request.POST.getlist('selected_tasks')
        Task.objects.filter(user=request.user, id__in=task_ids).delete()
        messages.success(request, 'Selected tasks have been deleted.')

        return redirect('task_management:delete_tasks')

    return render(request, 'task_management/delete_tasks.html', {'tasks': tasks})


def undelete_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user, task_completed=True)
        task.task_completed = False
        task.save()
        return JsonResponse({'status': 'success', 'message': 'Task reactivated successfully.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def serve_attachment(request, path):
    logger.info("Request to serve attachment at path : %s", path)
    task_management_attachments_dir = Path(__file__).resolve().parent / 'attachments'
    file_path = task_management_attachments_dir / path
    logger.info("File Path: %s", file_path)
    if not file_path.exists():
        logger.warning("File does not exist at: %s", file_path)
        raise Http404("File not found.")
    try:
        response = FileResponse(open(file_path, 'rb'))
        return response
    except Exception as e:
        logger.error("Error loading file : %s ; Error : %s", file_path, e, exc_info=True)
        raise Http404(f"Error loading file")


def fetch_google_tasks_and_save(user, creds):
        # Build the Google Tasks API service

        service = build('tasks', 'v1', credentials=creds)
        logger.info("Views:fetch_google_tasks_and_save: Before Getting Tasks.")

        # Get task lists
        tasklists_results = service.tasklists().list().execute()
        task_lists = tasklists_results.get('items', [])

        # Ensure 'All Tasks' list exists in the database
        all_tasks_list, created = TaskList.objects.get_or_create(
            user=user,
            list_name="Google Tasks",
            defaults={'special_list': True, 'list_code': 'GOOGLE_TASKS'}
        )

        # Iterate through task lists and sync tasks
        for task_list in task_lists:
            tasks_results = service.tasks().list(tasklist=task_list['id']).execute()
            tasks = tasks_results.get('items', [])

            for task in tasks:
                google_task_id = task.get('id')
                task_title = task.get('title', 'No Title')
                task_status = task.get('status') == 'completed'
                due_date_raw = task.get('due')
                due_date = None
                logger.info("Views:fetch_google_tasks_and_save: New Task Title: %s", task_title)

                # Parse due date
                if due_date_raw:
                    try:
                        due_date = datetime.fromisoformat(due_date_raw.replace('Z', '+00:00'))
                    except ValueError:
                        due_date = None  # Handle invalid dates gracefully

                # Check if the task exists and update or create
                existing_task = Task.objects.filter(user=user, source_id=google_task_id,source='google').first()
                if existing_task:
                    # Update the task
                    existing_task.task_name = task_title
                    existing_task.task_completed = task_status
                    existing_task.due_date = due_date
                    existing_task.last_update_date = timezone.now()
                    existing_task.source = 'google'
                    existing_task.save()
                    logger.info("Views:fetch_google_tasks_and_save: Existing Task: %s", task_title)
                else:
                    # Create a new task
                    
                    Task.objects.create(
                        user=user,
                        task_name=task_title,
                        task_completed=task_status,
                        due_date=due_date,
                        list_name=all_tasks_list,
                        source_id=google_task_id,
                        source='google',
                        creation_date=timezone.now(),
                        last_update_date=timezone.now()
                    )        

@login_required
def sync_google_tasks(request):
    """
    Example view that explicitly checks token expiration,
    refreshes if needed, and then syncs Google Tasks into Task model.
    """
    user = request.user
    try:
        logger.info("Syncing Google Tasks for user: %s", request.user.username)
        google_token = UserToken.objects.get(user=user, provider='google')
    except UserToken.DoesNotExist:
        # Handle missing token case
        logger.error("No Google Token found for user: %s", user.username)
        return redirect('core:dashboard')  # Redirect to your dashboard view after login

    # 1. Build credentials from stored tokens

    creds = Credentials(
        token=google_token.access_token,
        refresh_token=google_token.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        client_secret=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        scopes=[
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
        ],
    )

    # 2. Explicitly check if expired and refresh if needed
    if creds.expired and creds.refresh_token:
        logger.info("Refreshing Google token for user: %s", user.username)
        try:
            creds.refresh(Request())
        except Exception as e:
            print("Error refreshing Google token:", e)
            # Handle refresh failure (e.g., user revoked access)
            return redirect('core:dashboard')  # Redirect to your dashboard view after login
    
    fetch_google_tasks_and_save(user, creds)

    # 6. If the credentials changed (e.g., new access token), update DB
    if creds.token != google_token.access_token:
        google_token.access_token = creds.token
        google_token.save()

    return JsonResponse({'message': 'Google Tasks synced successfully!'})

@login_required
def connect_microsoft(request):
    """
    Initiates the Microsoft OAuth flow.
    Redirects the user to the Microsoft authorization URL.
    """
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=settings.MICROSOFT_AUTH['AUTHORITY']
    )

    auth_url = msal_app.get_authorization_request_url(
        scopes=settings.MICROSOFT_AUTH['SCOPE'],
        redirect_uri=settings.MICROSOFT_AUTH['REDIRECT_URI'],
        state=request.get_full_path()  # To redirect back after auth
    )
    logger.info(f"Redirecting user {request.user.username} to Microsoft login URL.")
    return redirect(auth_url)

@login_required
def microsoft_callback(request):
    """
    Handles the callback from Microsoft OAuth.
    Exchanges the authorization code for tokens and saves them.
    """
    code = request.GET.get('code')
    logger.info("Microsoft callback code: %s", code)
    if not code:
        error = request.GET.get('error', 'Unknown error')
        error_description = request.GET.get('error_description', 'No description provided.')
        logger.error(f"Microsoft callback error: {error} - {error_description}")
        return HttpResponse(f"Authentication failed: {error_description}", status=400)

    msal_app = _build_msal_app()
    scopes = settings.MICROSOFT_AUTH["SCOPE"]
    redirect_uri = settings.MICROSOFT_AUTH["REDIRECT_URI"]
    logger.info("Exchanging Microsoft authorization code for tokens.")
    logger.info("Code: %s, Scopes: %s, Redirect URI: %s", code, scopes, redirect_uri)

    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=scopes,
        redirect_uri=redirect_uri
    )
    logger.info("Microsoft token exchange result: %s", result)

    if "access_token" in result:
        logger.info("Microsoft access token retrieved successfully.")
        user = request.user
        provider = 'microsoft'
        access_token = result["access_token"]
        refresh_token = result.get("refresh_token")
        token_type = result.get("token_type")
        expires_in = result.get("expires_in")
        logger.info(f"Microsoft tokens: {access_token}, {refresh_token}, {token_type}, {expires_in}")


        # Prepare defaults for update_or_create
        defaults = {
            'access_token': access_token,
            'token_type': token_type,
            'expires_in': expires_in,
        }

        if refresh_token:
            defaults['refresh_token'] = refresh_token
        logger.info(f"Microsoft tokens defaults: {defaults}")
        # Update or create the UserToken
        user_token, created = UserToken.objects.update_or_create(
            user=user,
            provider=provider,
            defaults=defaults
        )
        logger.info(f"Microsoft tokens created: {created}")

        # If no refresh_token was provided and it's not a creation, retain the existing one
        if not refresh_token and not created:
            # No action needed; existing refresh_token remains
            pass  # Placeholder for any additional logic if required

        # Update token expiry
        user_token.set_token_expiry()
        user_token.save()

        logger.info(f"Stored Microsoft tokens for user: {user.username}.")

        # Redirect to your dashboard or desired page
        return redirect('/dashboard/')  # Update as per your routing
    else:
        error = result.get("error", "Unknown error")
        error_description = result.get("error_description", "No description provided.")
        logger.error(f"Could not retrieve access token: {error} - {error_description}")
        return HttpResponse(f"Could not retrieve access token: {error_description}", status=400)

def _build_msal_app(cache=None):
    """
    Helper function to build a ConfidentialClientApplication from MSAL
    """
    authority = settings.MICROSOFT_AUTH['AUTHORITY']
    return msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=authority,
        token_cache=cache,
    )

@login_required
def sync_microsoft_tasks(request):
    """
    Pulls user's Microsoft To Do tasks into our Django Task model.
    Automatically refreshes the access token if expired.
    """
    user = request.user
    logger.info(f"Syncing Microsoft Tasks for user: {user.username}")
    print("Syncing Microsoft Tasks for user: " + user.username)

    # 1) Get the user's Microsoft token
    try:
        ms_token = UserToken.objects.get(user=user, provider='microsoft')
    except UserToken.DoesNotExist:
        logger.error(f"User {user.username} does not have a MicrosoftToken.")
        return JsonResponse(
            {"error": "Microsoft account not connected."},
            status=400
        )

    # 2) Check if the token is expired
    if is_token_expired(ms_token):
        logger.info(f"Access token expired for user {user.username}, attempting to refresh.")
        new_access_token = refresh_microsoft_token(ms_token)
        if not new_access_token:
            return JsonResponse(
                {"error": "Authentication failed. Please reconnect your Microsoft account."},
                status=401
            )
        access_token = new_access_token
    else:
        access_token = ms_token.access_token

    # 3) Fetch and save tasks
    try:
        fetch_microsoft_tasks_and_save(user, access_token)
    except Exception as e:
        logger.exception(f"Error syncing Microsoft Tasks for user {user.username}: {str(e)}")
        return JsonResponse(
            {"error": "Failed to sync Microsoft Tasks."},
            status=500
        )

    return JsonResponse({'message': 'Microsoft Tasks synced successfully!'})


def fetch_microsoft_tasks_and_save(user, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    start_time_total = time.time()  # Start timing the entire process

    todo_lists_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    start_time_lists = time.time()
    response = requests.get(todo_lists_url, headers=headers)
    response.raise_for_status()
    end_time_lists = time.time()
    elapsed_time_lists = end_time_lists - start_time_lists
    logger.info(f"Fetched Microsoft To Do lists in {elapsed_time_lists:.2f} seconds.")


    microsoft_lists = response.json().get("value", [])
    logger.info(f"Fetched {len(microsoft_lists)} Microsoft To Do lists for user: {user.username}")

    for ms_list in microsoft_lists:
        ms_list_id = ms_list["id"]
        ms_list_name = ms_list["displayName"]

        ms_task_list, created = TaskList.objects.get_or_create(
            user=user,
            list_code=ms_list_id,
            defaults={'list_name': ms_list_name, 'special_list': False}
        )
        if created:
            logger.info(f"Created new TaskList for Microsoft list: {ms_list_name}")

        tasks_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{ms_list_id}/tasks"
        all_ms_tasks = []
        next_link = tasks_url

        start_time_list_tasks = time.time() # Start timing for this specific list

        while next_link:
            start_time_page = time.time() # Time each page fetch
            tasks_response = requests.get(next_link, headers=headers)
            tasks_response.raise_for_status()
            end_time_page = time.time()
            elapsed_time_page = end_time_page - start_time_page
            logger.debug(f"Fetched a page of tasks for '{ms_list_name}' in {elapsed_time_page:.2f} seconds.")

            tasks_data = tasks_response.json()
            current_tasks = tasks_data.get("value", [])
            all_ms_tasks.extend(current_tasks)
            next_link = tasks_data.get("@odata.nextLink")

        end_time_list_tasks = time.time()
        elapsed_time_list_tasks = end_time_list_tasks - start_time_list_tasks
        logger.info(f"Fetched {len(all_ms_tasks)} tasks (including pagination) for Microsoft list '{ms_list_name}' in {elapsed_time_list_tasks:.2f} seconds.")
        process_ms_tasks(user, ms_task_list, all_ms_tasks, headers)

    end_time_total = time.time()
    elapsed_time_total = end_time_total - start_time_total
    logger.info(f"Total time to fetch and process Microsoft tasks: {elapsed_time_total:.2f} seconds.")

def process_ms_tasks(user, ms_task_list, ms_tasks, headers):
    for task_item in ms_tasks:
        ms_task_id = task_item["id"]
        title = task_item.get("title", "Untitled")
        status = (task_item.get("status") == 'completed')
        due_date_raw = task_item.get("dueDateTime")
        due_date = None

        if due_date_raw and "dateTime" in due_date_raw:
            try:
                due_date = date_parser.parse(due_date_raw["dateTime"])
            except (ValueError, TypeError): # Handle potential type errors as well
                due_date = None
                logger.warning(f"Invalid or missing due date format for task '{title}': {due_date_raw}")

        existing_task = Task.objects.filter(user=user, source_id=ms_task_id, source='microsoft').first()
        if existing_task:
            existing_task.task_name = title
            existing_task.task_completed = status
            existing_task.due_date = due_date
            existing_task.last_update_date = timezone.now()
            existing_task.list_name = ms_task_list
            existing_task.save()
            logger.debug(f"Updated existing Microsoft task: {title}")
        else:
            Task.objects.create(
                user=user,
                task_name=title,
                task_completed=status,
                due_date=due_date,
                list_name=ms_task_list,
                source='microsoft',
                source_id=ms_task_id,
                creation_date=timezone.now(),
                last_update_date=timezone.now()
            )
            logger.debug(f"Created new Microsoft task: {title}")