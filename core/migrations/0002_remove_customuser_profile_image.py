# Generated by Django 4.2.7 on 2024-10-21 17:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='profile_image',
        ),
    ]
