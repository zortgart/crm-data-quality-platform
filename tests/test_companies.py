# =============================================================
# tests/test_companies.py
# =============================================================

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization
from companies.models import Company, CompanySize
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
def analyst_acme(org_acme):
    return User.objects.create_user(
        email="analyst@acme.com", password="pass", role=UserRole.ANALYST, organization=org_acme
    )


@pytest.fixture
def manager_globex(org_globex):
    return User.objects.create_user(
        email="manager@globex.com", password="pass", role=UserRole.MANAGER, organization=org_globex
    )


@pytest.fixture
def company_acme(org_acme):
    return Company.objects.create(
        organization=org_acme, name="Stark Industries", domain="stark.com"
    )


@pytest.fixture
def company_globex(org_globex):
    return Company.objects.create(
        organization=org_globex, name="Wayne Enterprises", domain="wayne.com"
    )


@pytest.mark.django_db
class TestCompanyEndpoints:

    def test_list_companies_tenant_isolation(self, api_client, manager_acme, company_acme, company_globex):
        """User should only see companies in their organization."""
        api_client.force_authenticate(user=manager_acme)
        response = api_client.get("/api/v1/companies/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"] if "results" in response.json() else response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "Stark Industries"

    def test_create_company_injects_organization(self, api_client, manager_acme):
        """Manager can create a company, and organization is auto-injected."""
        api_client.force_authenticate(user=manager_acme)
        response = api_client.post("/api/v1/companies/", {
            "name": "Oscorp",
            "domain": "oscorp.com"
        }, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Company.objects.filter(name="Oscorp").exists()
        company = Company.objects.get(name="Oscorp")
        assert company.organization == manager_acme.organization

    def test_analyst_cannot_create_company(self, api_client, analyst_acme):
        """Analyst role should get 403 when trying to write."""
        api_client.force_authenticate(user=analyst_acme)
        response = api_client.post("/api/v1/companies/", {
            "name": "Oscorp",
        }, format="json")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_company(self, api_client, analyst_acme, company_acme):
        """Analyst can retrieve a company in their org."""
        api_client.force_authenticate(user=analyst_acme)
        response = api_client.get(f"/api/v1/companies/{company_acme.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == company_acme.name

    def test_retrieve_company_cross_tenant_returns_404(self, api_client, analyst_acme, company_globex):
        """User gets 404 (not 403) when trying to retrieve another org's company via ID."""
        api_client.force_authenticate(user=analyst_acme)
        response = api_client.get(f"/api/v1/companies/{company_globex.id}/")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
