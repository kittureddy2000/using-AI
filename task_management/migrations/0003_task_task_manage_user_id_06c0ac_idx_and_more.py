# Generated by Django 4.2.7 on 2025-02-24 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0002_tasksyncstatus'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['user', 'task_completed', 'due_date'], name='task_manage_user_id_06c0ac_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['source', 'source_id'], name='task_manage_source_13f0ef_idx'),
        ),
    ]
