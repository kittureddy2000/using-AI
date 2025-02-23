from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, TaskList, Image, TaskHistory
from .forms import TaskForm, TaskListForm
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import uuid
import os
import logging
from google.cloud import storage
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import logging
from pathlib import Path
from datetime import datetime, time as dt_time
from googleapiclient.discovery import build
from dateutil import parser as date_parser
from django.shortcuts import redirect
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
from core.models import UserToken
import msal
import requests
import json
from django.contrib.auth.models import User
from google.cloud import storage, tasks_v2
from django.views.decorators.csrf import csrf_exempt
from core.utils import send_email
from .models import TaskSyncStatus  # You’ll need to create this model


logger = logging.getLogger(__name__)

# Ensure predefined lists exist for the user
def ensure_predefined_lists(user):
    predefined_lists = [
        {"name": "Past Due", "listcode": "PAST_DUE"},
        {"name": "Important", "listcode": "IMPORTANT"},
        {"name": "All Tasks", "listcode": "ALL_TASKS"},
        {"name": "Google Tasks", "listcode": "GOOGLE_TASKS"},
        {"name": "MS Tasks", "listcode": "MS_TASKS"},
    ]
    logger.info("Inside ensure_predefined_lists")
    logger.info(predefined_lists)

    # Get existing predefined lists for the user
    existing_names = TaskList.objects.filter(
        user=user,
        list_name__in=[predefined["name"] for predefined in predefined_lists],
        special_list=True
    ).values_list('list_name', flat=True)

    logger.info([field.name for field in TaskList._meta.get_fields()])

    # Create any missing predefined lists
    for predefined in predefined_lists:
        if predefined["name"] not in existing_names:
            logger.info("Creating Predefined List : " + predefined["name"])
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

    tasks = Task.objects.filter(user=request.user, task_completed=False).order_by('due_date')

    tasks_data = list(tasks.values(
        'id', 'task_name', 'list_name', 'due_date', 'task_description', 'due_date', 'reminder_time', 'recurrence',
        'task_completed',
        'important', 'assigned_to', 'creation_date', 'last_update_date'))  # Replace field names with the actual fields of your Task model

    return JsonResponse({'tasks': tasks_data})

# Get All tasks for the given list
@login_required
def get_tasks_by_list(request, list_id):
    logger.info("Function: Get Tasks with list id : " + str(list_id))

    sort_by = request.GET.get('sort', 'due_date')  # Replace 'default_field' with your default sort field
    order = request.GET.get('order', 'asc')
    if order == 'desc':
        sort_by = '-' + sort_by

    logger.info("Sort By : " + sort_by)
    if sort_by == 'important':
        sort_by = '-important'
    elif sort_by not in ['due_date']:
        sort_by = 'due_date'

    tasklist = TaskList.objects.get(id=list_id, user=request.user)
    logger.info("List Name : " + tasklist.list_name)

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
    logger.info("In Complete Task Function Task ID : " + task_id)

    task = Task.objects.get(id=task_id, user=request.user)
    task.task_completed = True
    task.last_update_date = timezone.now()
    task_name = task.task_name
    if task.recurrence == Task.DAILY:
        logger.info("Task is Daily")
        task.due_date = task.due_date + timedelta(days=1)
        task.reminder_time = task.reminder_time + timedelta(days=1)
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

def handle_image_upload(task, images):
    task_management_attachments_dir = Path(__file__).resolve().parent / 'attachments'
    task_management_attachments_dir.mkdir(exist_ok=True)

    for image in images:
        if settings.ENVIRONMENT == 'development':
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

# Fetch and save Google Tasks
def fetch_google_tasks_and_save(user, creds):
    service = build('tasks', 'v1', credentials=creds)
    logger.info("fetch_google_tasks_and_save: Google Tasks Service Created")
    tasklists_results = service.tasklists().list().execute()
    task_lists = tasklists_results.get('items', [])
    all_tasks_list, _ = TaskList.objects.get_or_create(
        user=user, list_name="Google Tasks", defaults={'special_list': True, 'list_code': 'GOOGLE_TASKS'}
    )
    for task_list in task_lists:
        tasks_results = service.tasks().list(tasklist=task_list['id']).execute()
        tasks = tasks_results.get('items', [])
        for task in tasks:
            google_task_id = task.get('id')
            task_title = task.get('title', 'No Title')
            task_status = task.get('status') == 'completed'
            due_date_raw = task.get('due')
            due_date = datetime.fromisoformat(due_date_raw.replace('Z', '+00:00')) if due_date_raw else None
            existing_task = Task.objects.filter(user=user, source_id=google_task_id, source='google').first()
            if existing_task:
                existing_task.task_name = task_title
                existing_task.task_completed = task_status
                existing_task.due_date = due_date
                existing_task.last_update_date = timezone.now()
                existing_task.source = 'google'
                existing_task.save()
            else:
                Task.objects.create(
                    user=user, task_name=task_title, task_completed=task_status, due_date=due_date,
                    list_name=all_tasks_list, source_id=google_task_id, source='google',
                    creation_date=timezone.now(), last_update_date=timezone.now()
                )

# Fetch and save Microsoft Tasks
def fetch_microsoft_tasks_and_save(user, access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    todo_lists_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    response = requests.get(todo_lists_url, headers=headers)
    logger.info("fetch_microsoft_tasks_and_save: Microsoft Tasks Service Created")
    response.raise_for_status()
    microsoft_lists = response.json().get("value", [])
    for ms_list in microsoft_lists:
        ms_list_id = ms_list["id"]
        ms_list_name = ms_list["displayName"]
        ms_task_list, _ = TaskList.objects.get_or_create(
            user=user, list_code=ms_list_id, defaults={'list_name': ms_list_name, 'special_list': False}
        )
        tasks_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{ms_list_id}/tasks"
        all_ms_tasks = []
        next_link = tasks_url
        while next_link:
            tasks_response = requests.get(next_link, headers=headers)
            tasks_response.raise_for_status()
            tasks_data = tasks_response.json()
            all_ms_tasks.extend(tasks_data.get("value", []))
            next_link = tasks_data.get("@odata.nextLink")
        process_ms_tasks(user, ms_task_list, all_ms_tasks, headers)

def process_ms_tasks(user, ms_task_list, ms_tasks, headers):
    for task_item in ms_tasks:
        ms_task_id = task_item["id"]
        title = task_item.get("title", "Untitled")
        status = task_item.get("status") == 'completed'
        due_date_raw = task_item.get("dueDateTime")
        due_date = date_parser.parse(due_date_raw["dateTime"]) if due_date_raw and "dateTime" in due_date_raw else None
        existing_task = Task.objects.filter(user=user, source_id=ms_task_id, source='microsoft').first()
        if existing_task:
            existing_task.task_name = title
            existing_task.task_completed = status
            existing_task.due_date = due_date
            existing_task.last_update_date = timezone.now()
            existing_task.list_name = ms_task_list
            existing_task.save()
        else:
            Task.objects.create(
                user=user, task_name=title, task_completed=status, due_date=due_date,
                list_name=ms_task_list, source='microsoft', source_id=ms_task_id,
                creation_date=timezone.now(), last_update_date=timezone.now()
            )

# Reusable sync function for both UI and background tasks
def sync_user_tasks(user, provider):
    """Sync tasks for a user from a given provider (google or microsoft)."""
    try:
        logger.info(f"Starting sync for user: {user.username} with provider: {provider}")
        if provider == 'google':
            google_token = UserToken.objects.get(user=user, provider='google')
            creds = Credentials(
                token=google_token.access_token, refresh_token=google_token.refresh_token,
                token_uri='https://oauth2.googleapis.com/token', client_id=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                client_secret=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                scopes=['https://www.googleapis.com/auth/tasks'],
            )
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    google_token.access_token = creds.token
                    google_token.save()
                except Exception as e:
                    logger.error(f"Failed to refresh Google token for {user.username}: {e}")
                    raise Exception(f"Google token refresh failed - please re-authenticate: {e}")
            fetch_google_tasks_and_save(user, creds)
            logger.info(f"Google Tasks synced for user: {user.username}")
        elif provider == 'microsoft':
            ms_token = UserToken.objects.get(user=user, provider='microsoft')
            access_token = ms_token.access_token if not is_token_expired(ms_token) else refresh_microsoft_token(ms_token)
            if not access_token:
                logger.error(f"Microsoft token refresh failed for {user.username}")
                raise Exception("Microsoft token refresh failed - please re-authenticate")
            fetch_microsoft_tasks_and_save(user, access_token)
            logger.info(f"Microsoft Tasks synced for user: {user.username}")
        
        # Mark sync as complete in TaskSyncStatus
        TaskSyncStatus.objects.update_or_create(
            user=user, provider=provider, defaults={'is_complete': True}
        )

        # Send email only in production, skip in development
        if settings.ENVIRONMENT != 'development':
            send_email(
                subject=f"Task Sync Completed for {provider.capitalize()}",
                message=f"Your {provider.capitalize()} tasks have been synced successfully.",
                recipient_list=[user.email],
            )
            logger.info(f"Email notification sent to user: {user.username} for {provider} sync completion")
        else:
            logger.info(f"Skipping email notification in development for user: {user.username} and provider: {provider}")
    except Exception as e:
        logger.error(f"Error syncing {provider} tasks for user {user.username}: {e}")
        raise# UI-triggered syncs
    
@login_required
def sync_google_tasks(request):
    sync_user_tasks(request.user, 'google')
    return JsonResponse({'message': 'Google Tasks synced successfully!'})

@login_required
def sync_microsoft_tasks(request):
    sync_user_tasks(request.user, 'microsoft')
    return JsonResponse({'message': 'Microsoft Tasks synced successfully!'})

# Background task endpoint triggered by Cloud Scheduler
@csrf_exempt
def trigger_background_sync(request):
    """Endpoint triggered by Cloud Scheduler to enqueue sync tasks."""
    logger.info("Triggering background sync")
    if request.method != 'POST':
        logger.warning("Method not allowed: %s", request.method)
        return HttpResponse("Method not allowed", status=405)
    
    # Local testing override
    if settings.ENVIRONMENT == 'development':
        from django.test import Client
        client_http = Client()
        logger.info("Using local test client for Cloud Tasks")
    else:
        # Only initialize Cloud Tasks client in production
        client = tasks_v2.CloudTasksClient()
        project = os.environ.get('PROJECT_ID')  # e.g., 'my-project'
        location = 'us-west1'  # Adjust as needed
        queue = 'task-sync-queue'
        parent = client.queue_path(project, location, queue)

    users = UserToken.objects.values('user').distinct()
    for user_dict in users:
        user_id = user_dict['user']
        logger.info("Processing user ID: %s", user_id)
        for provider in ['google', 'microsoft']:
            if UserToken.objects.filter(user_id=user_id, provider=provider).exists():
                logger.info("User ID %s has provider %s", user_id, provider)
                if settings.ENVIRONMENT == 'development':
                    # Simulate Cloud Tasks locally
                    logger.info("Simulating Cloud Tasks locally for user ID %s and provider %s", user_id, provider)
                    client_http.post('/task_management/process_sync_task/',
                                     f'{{"user_id": {user_id}, "provider": "{provider}"}}',
                                     content_type='application/json')
                else:
                    # Enqueue task in production
                    task = {
                        'http_request': {
                            'http_method': tasks_v2.HttpMethod.POST,
                            'url': f'{settings.BASE_URL}/task_management/process_sync_task/',
                            'body': f'{{"user_id": {user_id}, "provider": "{provider}"}}'.encode(),
                            'headers': {'Content-Type': 'application/json'},
                        }
                    }
                    client.create_task(request={'parent': parent, 'task': task})
                    logger.info("Enqueued %s sync task for user %s", provider, user_id)
    
    logger.info("Sync tasks enqueued successfully")
    return HttpResponse("Sync tasks enqueued", status=200)
# Process individual sync task
@csrf_exempt
def process_sync_task(request):
    """Endpoint to process an individual sync task."""
    logger.info("Processing sync task")
    if request.method != 'POST':
        logger.warning("Method not allowed: %s", request.method)
        return HttpResponse("Method not allowed", status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        provider = data.get('provider')
        
        logger.info("Sync task for user ID: %s, provider: %s", user_id, provider)
        
        user = User.objects.get(id=user_id)
        sync_user_tasks(user, provider)
        
        logger.info("%s sync completed for user ID: %s", provider.capitalize(), user_id)
        return HttpResponse(f"{provider.capitalize()} sync completed for user {user_id}", status=200)
    except Exception as e:
        logger.error("Error processing sync task for user ID: %s, provider: %s, Error: %s", user_id, provider, e, exc_info=True)
        return HttpResponse(f"Error processing sync task: {e}", status=500)

# Microsoft OAuth handlers (unchanged)
@login_required
def connect_microsoft(request):
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=settings.MICROSOFT_AUTH['AUTHORITY']
    )
    auth_url = msal_app.get_authorization_request_url(
        scopes=settings.MICROSOFT_AUTH['SCOPE'],
        redirect_uri=settings.MICROSOFT_AUTH['REDIRECT_URI'],
        state=request.get_full_path()
    )
    return redirect(auth_url)

@login_required
def microsoft_callback(request):
    code = request.GET.get('code')
    if not code:
        error = request.GET.get('error', 'Unknown error')
        error_description = request.GET.get('error_description', 'No description provided.')
        logger.error(f"Microsoft callback error: {error} - {error_description}")
        return HttpResponse(f"Authentication failed: {error_description}", status=400)

    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=settings.MICROSOFT_AUTH['AUTHORITY']
    )
    result = msal_app.acquire_token_by_authorization_code(
        code=code, scopes=settings.MICROSOFT_AUTH["SCOPE"],
        redirect_uri=settings.MICROSOFT_AUTH["REDIRECT_URI"]
    )
    if "access_token" in result:
        user = request.user
        defaults = {
            'access_token': result["access_token"],
            'token_type': result.get("token_type"),
            'expires_in': result.get("expires_in"),
        }
        if "refresh_token" in result:
            defaults['refresh_token'] = result["refresh_token"]
        user_token, _ = UserToken.objects.update_or_create(
            user=user, provider='microsoft', defaults=defaults
        )
        user_token.set_token_expiry()
        user_token.save()
        return redirect('/dashboard/')
    error = result.get("error", "Unknown error")
    error_description = result.get("error_description", "No description provided.")
    return HttpResponse(f"Could not retrieve access token: {error_description}", status=400)

def refresh_microsoft_token(user_token):
    """
    Refreshes the Microsoft access token using the refresh token.
    Updates the UserToken model with the new access token and expiry.
    Returns the new access token or None if refresh fails.
    """
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_AUTH['CLIENT_ID'],
        client_credential=settings.MICROSOFT_AUTH['CLIENT_SECRET'],
        authority=settings.MICROSOFT_AUTH['AUTHORITY']
    )

    result = msal_app.acquire_token_by_refresh_token(
        refresh_token=user_token.refresh_token,
        scopes=settings.MICROSOFT_AUTH["SCOPE"]
    )

    if "access_token" in result:
        user_token.access_token = result["access_token"]
        user_token.expires_in = result.get("expires_in")
        user_token.token_type = result.get("token_type")
        if "refresh_token" in result:
            user_token.refresh_token = result["refresh_token"]
        user_token.set_token_expiry()
        user_token.save()
        logger.info(f"Refreshed Microsoft token for user: {user_token.user.username}")
        return result["access_token"]
    else:
        logger.error(f"Failed to refresh Microsoft token for user {user_token.user.username}: {result.get('error_description')}")
        return None

def is_token_expired(user_token):
    """
    Checks if the access token is expired.
    Returns True if expired, False otherwise.
    """
    if user_token.token_expires_at:
        return timezone.now() >= user_token.token_expires_at
    return False  # If no expiry info, assume not expired (adjust as needed)

@csrf_exempt
@login_required
def trigger_user_sync(request):
    """Endpoint triggered from UI to enqueue sync tasks for the current user."""
    logger.info(f"Triggering user sync for user: {request.user.username}")
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    if settings.ENVIRONMENT == 'development':
        from django.test import Client
        client_http = Client()
        for provider in ['google', 'microsoft']:
            if UserToken.objects.filter(user=request.user, provider=provider).exists():
                logger.info(f"Simulating sync for user {request.user.username} and provider {provider}")
                client_http.post('/task_management/process_sync_task/',
                                 f'{{"user_id": {request.user.id}, "provider": "{provider}"}}',
                                 content_type='application/json')
    else:
        client = tasks_v2.CloudTasksClient()
        project = os.environ.get('PROJECT_ID')
        location = 'us-west1'
        queue = 'task-sync-queue'
        parent = client.queue_path(project, location, queue)

        for provider in ['google', 'microsoft']:
            if UserToken.objects.filter(user=request.user, provider=provider).exists():
                task = {
                    'http_request': {
                        'http_method': tasks_v2.HttpMethod.POST,
                        'url': f'{settings.BASE_URL}/task_management/process_sync_task/',
                        'body': f'{{"user_id": {request.user.id}, "provider": "{provider}"}}'.encode(),
                        'headers': {'Content-Type': 'application/json'},
                    }
                }
                client.create_task(request={'parent': parent, 'task': task})
                logger.info(f"Enqueued {provider} sync task for user {request.user.username}")

    return JsonResponse({'message': 'Sync tasks enqueued for user'})

# View to check sync status
@csrf_exempt  # Optional, depending on your needs; remove if UI uses CSRF
def check_sync_status(request):
    """
    Check the status of a sync operation for a user and provider.
    Returns JSON: {'completed': bool}.
    """
    logger.info("Checking sync status for request")
    if request.method != 'GET':
        return HttpResponse("Method not allowed", status=405)

    provider = request.GET.get('provider')
    user_id = request.GET.get('user_id')

    if not provider or not user_id:
        return JsonResponse({'error': 'Provider and user_id are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # Check if sync is complete for this user/provider
    sync_status, created = TaskSyncStatus.objects.get_or_create(
        user=user, provider=provider, defaults={'is_complete': False}
    )

    # Simulate checking if sync is complete (you can modify this logic)
    # In practice, update TaskSyncStatus in sync_user_tasks when sync completes
    is_complete = sync_status.is_complete

    return JsonResponse({'completed': is_complete})