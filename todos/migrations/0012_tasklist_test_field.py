# Generated by Django 4.2.7 on 2023-12-27 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0011_remove_task_task_image_alter_task_recurrence_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasklist',
            name='test_field',
            field=models.CharField(max_length=100, null=True),
        ),
    ]