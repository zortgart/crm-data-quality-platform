# core/models.py
import uuid
from django.db import models
from django.conf import settings
from organizations.models import Organization

class AuditLog(models.Model):
    """
    Tracks all CUD (Create, Update, Delete) operations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50) # CREATE, UPDATE, DELETE
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    payload = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} {self.path} at {self.timestamp}"
