from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class TaskList(models.Model):
    list_name = models.CharField(max_length=2000)
    list_code = models.CharField(max_length=100, null=True)
    special_list = models.BooleanField(default=False)
    color = models.CharField(max_length=100)

    def __str__(self):
        return self.list_name

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,default=3)
    task_name = models.CharField(max_length=200)
    list_name = models.ForeignKey(TaskList, on_delete=models.SET_DEFAULT, default=1, blank=True)
    task_description = models.CharField(max_length=2000)
    due_date = models.DateTimeField()
    reminder_time = models.DateTimeField(default=timezone.now , blank = True)
    recurrence = models.CharField(max_length=100, blank=True)
    task_completed = models.BooleanField(default=False)
    important = models.BooleanField(default=False)
    assigned_to = models.CharField(max_length=100, null=True, blank=True)
    task_image = models.FileField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name

    class Meta:
        ordering = ['-creation_date']
