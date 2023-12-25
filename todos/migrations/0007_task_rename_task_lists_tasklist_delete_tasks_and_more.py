# Generated by Django 4.2.7 on 2023-12-04 23:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('todos', '0006_alter_tasks_creation_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(max_length=200)),
                ('task_description', models.CharField(max_length=2000)),
                ('due_date', models.DateTimeField()),
                ('reminder_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('recurrence', models.CharField(blank=True, max_length=100)),
                ('task_completed', models.BooleanField(default=False)),
                ('important', models.BooleanField(default=False)),
                ('assigned_to', models.CharField(blank=True, max_length=100, null=True)),
                ('task_image', models.FileField(blank=True, null=True, upload_to='')),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_update_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
        migrations.RenameModel(
            old_name='task_Lists',
            new_name='TaskList',
        ),
        migrations.DeleteModel(
            name='tasks',
        ),
        migrations.AddField(
            model_name='task',
            name='task_list',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='todos.tasklist'),
        ),
        migrations.AddField(
            model_name='task',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]