# Generated by Django 4.2.7 on 2024-01-12 20:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0015_remove_taskhistory_task_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='reminder_time',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
