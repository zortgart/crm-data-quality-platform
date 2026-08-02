import pytest
from rest_framework.test import APIClient
from accounts.models import UserRole
from notifications.models import Notification
from imports.models import ImportJob, ImportStatus

from django.contrib.auth import get_user_model
from organizations.models import Organization

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def org_acme(db):
    return Organization.objects.create(name="Acme Corp", slug="acme-corp")

@pytest.fixture
def notifications_client(api_client, org_acme):
    user = User.objects.create_user(
        email="notify@test.com", password="pwd", role=UserRole.MANAGER, organization=org_acme
    )
    api_client.force_authenticate(user=user)
    return api_client, user, org_acme

@pytest.mark.django_db
class TestNotifications:
    def test_import_job_completion_creates_notification(self, org_acme):
        org = org_acme
        user = User.objects.create_user(email="notify2@test.com", password="pwd", role=UserRole.MANAGER, organization=org)
        
        # Create an import job
        job = ImportJob.objects.create(
            organization=org,
            created_by=user,
            filename="test.csv",
            total_rows=100
        )
        
        # Change status to completed
        job.status = ImportStatus.COMPLETED
        job.processed = 100
        job.save()
        
        # Check if notification was created via signals
        assert Notification.objects.filter(user=user).count() == 1
        notif = Notification.objects.filter(user=user).first()
        assert "completed" in notif.message.lower()
        assert "100" in notif.message

    def test_list_notifications(self, notifications_client):
        client, user, _ = notifications_client
        Notification.objects.create(user=user, message="Test notification")
        
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) == 1
        assert results[0]["message"] == "Test notification"
        assert not results[0]["is_read"]

    def test_read_notification(self, notifications_client):
        client, user, _ = notifications_client
        notif = Notification.objects.create(user=user, message="Test notification")
        
        response = client.post(f"/api/v1/notifications/{notif.id}/read/")
        assert response.status_code == 200
        
        notif.refresh_from_db()
        assert notif.is_read

    def test_read_all_notifications(self, notifications_client):
        client, user, _ = notifications_client
        Notification.objects.create(user=user, message="Test 1")
        Notification.objects.create(user=user, message="Test 2")
        
        response = client.post("/api/v1/notifications/read_all/")
        assert response.status_code == 200
        
        assert Notification.objects.filter(user=user, is_read=False).count() == 0
        assert Notification.objects.filter(user=user, is_read=True).count() == 2
