from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Optionally, add any additional configurations here

admin.site.register(CustomUser, CustomUserAdmin)

