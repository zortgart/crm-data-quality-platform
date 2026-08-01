# =============================================================
# organizations/apps.py — App Configuration
# =============================================================
# Every Django app has an AppConfig class.
# Django uses it to configure the app during startup.
#
# Java equivalent: @Configuration class or Spring Boot auto-config
# =============================================================

from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "organizations"
    verbose_name = "Organizations"
