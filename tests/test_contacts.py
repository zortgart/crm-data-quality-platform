# =============================================================
# tests/test_contacts.py
# =============================================================

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization
from companies.models import Company
from contacts.models import Contact
from accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org_acme(db):
    return Organization.objects.create(name="Acme Corp", slug="acme")


@pytest.fixture
def org_globex(db):
    return Organization.objects.create(name="Globex", slug="globex")


@pytest.fixture
def manager_acme(org_acme):
    return User.objects.create_user(
        email="manager@acme.com", password="pass", role=UserRole.MANAGER, organization=org_acme
    )


@pytest.fixture
def company_acme(org_acme):
    return Company.objects.create(organization=org_acme, name="Stark Industries")


@pytest.fixture
def company_globex(org_globex):
    return Company.objects.create(organization=org_globex, name="Wayne Enterprises")


@pytest.fixture
def contact_acme(org_acme, company_acme):
    return Contact.objects.create(
        organization=org_acme, company=company_acme, first_name="Tony", last_name="Stark", email="tony@stark.com"
    )


@pytest.fixture
def contact_globex(org_globex, company_globex):
    return Contact.objects.create(
        organization=org_globex, company=company_globex, first_name="Bruce", last_name="Wayne", email="bruce@wayne.com"
    )


@pytest.mark.django_db
class TestContactEndpoints:

    def test_list_contacts_tenant_isolation(self, api_client, manager_acme, contact_acme, contact_globex):
        """User should only see contacts in their organization."""
        api_client.force_authenticate(user=manager_acme)
        response = api_client.get("/api/v1/contacts/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"] if "results" in response.json() else response.json()
        
        assert len(data) == 1
        assert data[0]["email"] == "tony@stark.com"

    def test_create_contact_success(self, api_client, manager_acme, company_acme):
        """Manager can create a contact."""
        api_client.force_authenticate(user=manager_acme)
        response = api_client.post("/api/v1/contacts/", {
            "first_name": "Pepper",
            "last_name": "Potts",
            "email": "pepper@stark.com",
            "company": str(company_acme.id)
        }, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Contact.objects.filter(email="pepper@stark.com").exists()

    def test_create_contact_cross_tenant_company_rejected(self, api_client, manager_acme, company_globex):
        """User cannot assign a contact to a company from another org."""
        api_client.force_authenticate(user=manager_acme)
        response = api_client.post("/api/v1/contacts/", {
            "first_name": "Spy",
            "last_name": "Agent",
            "email": "spy@stark.com",
            "company": str(company_globex.id)
        }, format="json")
        
        # 400 because the serializer validation catches it
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "company" in response.json()
