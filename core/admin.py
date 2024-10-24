from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import Profile


# Register your models here.
admin.site.register(CustomUser, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture')  # Customize this as per your `Profile` model fields
    search_fields = ('user__username', 'user__email')  # Allow search by username and email
