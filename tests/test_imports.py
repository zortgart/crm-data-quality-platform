# =============================================================
# tests/test_imports.py
# =============================================================

import pytest
import io
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from organizations.models import Organization
from contacts.models import Contact
from imports.models import ImportJob, ImportStatus, ImportRow
from accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org_acme(db):
    return Organization.objects.create(name="Acme Corp", slug="acme")


@pytest.fixture
def manager_acme(org_acme):
    return User.objects.create_user(
        email="manager@acme.com", password="pass", role=UserRole.MANAGER, organization=org_acme
    )


@pytest.fixture
def analyst_acme(org_acme):
    return User.objects.create_user(
        email="analyst@acme.com", password="pass", role=UserRole.ANALYST, organization=org_acme
    )


@pytest.mark.django_db
class TestImportsEndpoints:

    def test_upload_csv_success(self, api_client, manager_acme):
        api_client.force_authenticate(user=manager_acme)
        
        csv_content = b"first_name,last_name,email,phone\nTony,Stark,tony@stark.com,4155552671\nBruce,Wayne,bruce@wayne.com,"
        csv_file = SimpleUploadedFile("contacts.csv", csv_content, content_type="text/csv")
        
        response = api_client.post("/api/v1/imports/", {"file": csv_file}, format="multipart")
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == ImportStatus.COMPLETED
        assert data["processed"] == 2
        assert data["failed"] == 0
        
        # Verify contacts created
        assert Contact.objects.filter(organization=manager_acme.organization).count() == 2
        c = Contact.objects.get(email="tony@stark.com")
        assert c.normalized_phone == "+14155552671" # Normalizer ran!

    def test_upload_csv_missing_headers(self, api_client, manager_acme):
        api_client.force_authenticate(user=manager_acme)
        
        # Missing 'email' header
        csv_content = b"first_name,last_name\nTony,Stark\n"
        csv_file = SimpleUploadedFile("bad.csv", csv_content, content_type="text/csv")
        
        response = api_client.post("/api/v1/imports/", {"file": csv_file}, format="multipart")
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == ImportStatus.FAILED
        assert "Missing required headers" in data["error_message"]

    def test_upload_csv_with_row_errors(self, api_client, manager_acme):
        api_client.force_authenticate(user=manager_acme)
        
        # Row 2 is missing first_name (assuming first_name is required by DRF, wait actually it's default="" in model but DRF might not require it. Let's send an invalid email to trigger a serializer error)
        csv_content = b"first_name,last_name,email\nTony,Stark,tony@stark.com\nBruce,Wayne,not-an-email\n"
        csv_file = SimpleUploadedFile("errors.csv", csv_content, content_type="text/csv")
        
        response = api_client.post("/api/v1/imports/", {"file": csv_file}, format="multipart")
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["status"] == ImportStatus.COMPLETED
        assert data["processed"] == 1
        assert data["failed"] == 1
        
        # Check the errors endpoint
        job_id = data["id"]
        errors_response = api_client.get(f"/api/v1/imports/{job_id}/errors/")
        assert errors_response.status_code == status.HTTP_200_OK
        
        errors_data = errors_response.json()["results"] if "results" in errors_response.json() else errors_response.json()
        assert len(errors_data) == 1
        assert errors_data[0]["row_number"] == 3 # Header is 1, Tony is 2, Bruce is 3
        assert "email" in errors_data[0]["errors"]

    def test_analyst_cannot_upload(self, api_client, analyst_acme):
        api_client.force_authenticate(user=analyst_acme)
        
        csv_content = b"first_name,last_name,email\nTony,Stark,tony@stark.com\n"
        csv_file = SimpleUploadedFile("contacts.csv", csv_content, content_type="text/csv")
        
        response = api_client.post("/api/v1/imports/", {"file": csv_file}, format="multipart")
        
        # Analysts can only GET
        assert response.status_code == status.HTTP_403_FORBIDDEN
