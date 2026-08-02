from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "domain", "industry", "size", "city", "organization", "is_active"]
    list_filter = ["size", "is_active", "organization"]
    search_fields = ["name", "domain", "industry"]
    readonly_fields = ["id", "created_at", "updated_at"]
