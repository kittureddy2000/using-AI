# Generated by Django 4.2.7 on 2023-12-02 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0003_task_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='test',
            field=models.TextField(blank=True),
        ),
    ]