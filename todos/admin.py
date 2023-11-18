# todo/admin.py

from django.contrib import admin
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'completed', 'created_at')  # Fields to display in the list view
    list_filter = ('completed',)  # Filters
    search_fields = ('title', 'description')  # Searchable fields

admin.site.register(Task, TaskAdmin)
