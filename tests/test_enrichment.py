import pytest
from rest_framework.test import APIClient
from accounts.models import UserRole
from companies.models import Company
from contacts.models import Contact
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
def manager_client(api_client, org_acme):
    user = User.objects.create_user(
        email="manager@test.com", password="pwd", role=UserRole.MANAGER, organization=org_acme
    )
    api_client.force_authenticate(user=user)
    return api_client, user, org_acme

@pytest.fixture
def analyst_client(api_client, org_acme):
    user = User.objects.create_user(
        email="analyst@test.com", password="pwd", role=UserRole.ANALYST, organization=org_acme
    )
    api_client.force_authenticate(user=user)
    return api_client, user, org_acme

@pytest.mark.django_db
class TestEnrichmentEndpoints:
    def test_enrich_company(self, manager_client):
        client, _, org = manager_client
        company = Company.objects.create(
            organization=org,
            name="Apple",
            domain="apple.com"
        )
        
        # Test the enrich endpoint
        response = client.post(f"/api/v1/companies/{company.id}/enrich/")
        assert response.status_code == 200
        
        # The mock provider sets industry=Technology, size=ENTERPRISE, description=Apple is a leading...
        company.refresh_from_db()
        assert company.industry == "Technology"
        assert company.size == "ENTERPRISE"
        assert "leading technology company" in company.description

    def test_enrich_company_permission_denied_for_analyst(self, analyst_client):
        client, _, org = analyst_client
        company = Company.objects.create(organization=org, name="Google", domain="google.com")
        
        response = client.post(f"/api/v1/companies/{company.id}/enrich/")
        assert response.status_code == 403

    def test_enrich_contact(self, manager_client):
        client, _, org = manager_client
        company = Company.objects.create(organization=org, name="Microsoft", domain="microsoft.com")
        contact = Contact.objects.create(
            organization=org,
            company=company,
            first_name="Satya",
            last_name="Nadella",
            email="satya@microsoft.com"
        )
        
        response = client.post(f"/api/v1/contacts/{contact.id}/enrich/")
        assert response.status_code == 200
        
        contact.refresh_from_db()
        # Mock provider returns job_title="Senior Software Engineer"
        assert contact.job_title == "Senior Software Engineer"
        assert "satya-nadella" in contact.linkedin_url
