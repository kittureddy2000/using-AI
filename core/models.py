# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    # Add custom fields here if needed
    pass

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='user_images/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    # Add any additional fields here

    def __str__(self):
        return self.user.username

# Signal to create or update the user profile automatically when the user is created or saved
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
