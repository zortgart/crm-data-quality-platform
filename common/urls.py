# common/urls.py — URL patterns for common app
from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("ready/", views.readiness_check, name="readiness-check"),
]
