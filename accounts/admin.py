# =============================================================
# accounts/admin.py — Register User in Django Admin
# =============================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for our User model.
    Extends Django's built-in UserAdmin but adapts it for our
    email-based login and role system.
    """
    list_display = ["email", "full_name", "role", "organization", "is_active", "created_at"]
    list_filter = ["role", "is_active", "organization"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login"]
    ordering = ["email"]

    # Fieldsets control the layout of the edit page in admin
    fieldsets = (
        ("Identity", {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Organization & Role", {"fields": ("organization", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_login")}),
    )

    # Fields shown when CREATING a new user in admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2",
                       "organization", "role"),
        }),
    )

    # Required for email-based login
    filter_horizontal = ()
