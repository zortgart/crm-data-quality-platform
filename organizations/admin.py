# =============================================================
# organizations/admin.py — Django Admin Registration
# =============================================================
# Registers models with Django's built-in admin interface.
# Admin gives us a free web UI to browse/manage data during development.
#
# Visit: http://localhost:8000/admin/
# Java equivalent: Spring Boot Admin or a custom admin panel
# =============================================================

from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}  # auto-fill slug from name
