from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "role", "is_active", "is_staff")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (("Skelo", {"fields": ("role", "phone", "is_email_verified")} ),)
