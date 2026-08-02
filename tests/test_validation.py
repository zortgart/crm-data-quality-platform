# =============================================================
# tests/test_validation.py
# =============================================================

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from organizations.models import Organization
from companies.models import Company
from contacts.models import Contact
from accounts.models import UserRole
from validation.normalizers import (
    normalize_email, normalize_phone, normalize_company_name, normalize_job_title
)
from validation.quality_scorer import calculate_quality_score
from validation.duplicate_detector import detect_duplicates
from validation.models import DuplicatePair

User = get_user_model()


@pytest.fixture
def org_acme(db):
    return Organization.objects.create(name="Acme Corp", slug="acme")


@pytest.fixture
def manager_acme(org_acme):
    return User.objects.create_user(
        email="manager@acme.com", password="pass", role=UserRole.MANAGER, organization=org_acme
    )


@pytest.fixture
def company_acme(org_acme):
    return Company.objects.create(organization=org_acme, name="Acme Inc.")


@pytest.mark.django_db
class TestNormalizers:
    def test_normalize_email(self):
        assert normalize_email(" TEST@EXAMPLE.com ") == "test@example.com"
        assert normalize_email(None) == ""

    def test_normalize_phone_valid_us(self):
        # phonenumbers lib format
        assert normalize_phone("(415) 555-2671") == "+14155552671"
        assert normalize_phone("+44 20 7123 1234", "GB") == "+442071231234"

    def test_normalize_phone_invalid_returns_original(self):
        assert normalize_phone("not-a-phone") == "not-a-phone"

    def test_normalize_company_name(self):
        assert normalize_company_name("Acme Corp.") == "acme"
        assert normalize_company_name("Wayne Enterprises LLC") == "wayne enterprises"

    def test_normalize_job_title(self):
        assert normalize_job_title("Sr. Eng.") == "Senior Engineer"
        assert normalize_job_title("VP of Sales") == "Vice President of Sales"


@pytest.mark.django_db
class TestQualityScorer:
    def test_quality_scorer_max(self, org_acme, company_acme):
        c = Contact(
            organization=org_acme,
            first_name="Tony", last_name="Stark",
            email="tony@stark.com",
            normalized_email="tony@stark.com",
            phone="+14155552671",
            normalized_phone="+14155552671",
            job_title="CEO",
            company=company_acme
        )
        assert calculate_quality_score(c) == 100

    def test_quality_scorer_partial(self, org_acme):
        c = Contact(
            organization=org_acme,
            first_name="Tony",
            # missing last_name = 10 pts
            email="tony@stark.com",
            normalized_email="tony@stark.com", # 30 pts
            job_title="CEO" # 10 pts
            # no company, no phone
        )
        assert calculate_quality_score(c) == 50


@pytest.mark.django_db
class TestDuplicateDetector:
    def test_l1_exact_email(self, org_acme):
        c1 = Contact.objects.create(
            organization=org_acme,
            first_name="Tony", last_name="Stark",
            normalized_email="tony@stark.com"
        )
        c2 = Contact.objects.create(
            organization=org_acme,
            first_name="Anthony", last_name="Stark",
            normalized_email="tony@stark.com"
        )
        
        detect_duplicates(c2)
        
        pair = DuplicatePair.objects.first()
        assert pair is not None
        assert pair.confidence == 100
        assert pair.detection_level == "L1_EXACT_EMAIL"

    def test_l2_exact_phone(self, org_acme):
        c1 = Contact.objects.create(
            organization=org_acme,
            first_name="Tony", last_name="Stark",
            normalized_phone="+14155552671"
        )
        c2 = Contact.objects.create(
            organization=org_acme,
            first_name="Anthony", last_name="Stark",
            normalized_phone="+14155552671"
        )
        
        detect_duplicates(c2)
        
        pair = DuplicatePair.objects.first()
        assert pair.confidence == 80
        assert pair.detection_level == "L2_EXACT_PHONE"


@pytest.mark.django_db
class TestPipelineIntegration:
    def test_create_api_triggers_pipeline(self, manager_acme):
        client = APIClient()
        client.force_authenticate(user=manager_acme)
        
        response = client.post("/api/v1/contacts/", {
            "first_name": "Tony",
            "last_name": "Stark",
            "email": " TONY@stark.com ",
            "phone": "(415) 555-2671",
            "job_title": "Sr. Eng."
        }, format="json")
        
        assert response.status_code == 201
        
        # Verify normalizers ran
        c = Contact.objects.get(id=response.json()["id"])
        assert c.normalized_email == "tony@stark.com"
        assert c.normalized_phone == "+14155552671"
        assert c.job_title == "Senior Engineer"
        
        # Verify quality scorer ran (Email(30)+Phone(20)+Name(20)+Title(10) = 80)
        assert c.quality_score == 80
