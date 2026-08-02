from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "job_title", "company", "quality_score", "organization", "is_active"]
    list_filter = ["is_active", "organization", "company"]
    search_fields = ["first_name", "last_name", "email", "job_title"]
    readonly_fields = ["id", "quality_score", "normalized_email", "normalized_phone", "created_at", "updated_at"]
