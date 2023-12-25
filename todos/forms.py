from django import forms
from .models import Task, TaskList
from .widget import DatePickerInput, TimePickerInput, DateTimePickerInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

RECURRENCE_CHOICES = [
    ('NO_RECURRENCE', 'No Recurrence'),
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('MONTHLY', 'Monthly'),
    ('YEARLY', 'Yearly'),
]

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['list_name', 'list_code', 'special_list', 'color']
        widgets = {
            'list_name': forms.TextInput(attrs={'class': 'form-control'}),
            'list_code': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            # 'special_list' will use the default checkbox widget
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['task_name', 'task_description', 'list_name', 'due_date',  'reminder_time', 'recurrence', 'task_completed', 'important', 'assigned_to']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control'}),
            'task_description': forms.Textarea(attrs={'class': 'form-control'}),
            'list_name': forms.Select(attrs={'class': 'form-control'}),
            'due_date': DatePickerInput(attrs={'class': 'form-control'}),
            'reminder_time': DatePickerInput(attrs={'class': 'form-control'}),
            # Add other widgets as needed
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['list_name'].queryset = TaskList.objects.all()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')  # Add other fields if needed
