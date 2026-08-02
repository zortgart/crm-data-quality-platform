# =============================================================
# tests/test_performance.py
# =============================================================
# This file tests database query performance, specifically
# preventing the N+1 query problem.
#
# Java equivalent:
#   Using a tool like Hibernate-Types/vladmihalcea assertSelectCount()
# =============================================================

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test.utils import CaptureQueriesContext
from django.db import connection
from organizations.models import Organization
from companies.models import Company
from contacts.models import Contact
from accounts.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_n_plus_one_data(db):
    """
    Creates an org, a user, 10 companies, and 10 contacts.
    If N+1 is present, fetching 10 contacts will take 11 queries.
    If N+1 is fixed, it will take ~1-2 queries.
    """
    org = Organization.objects.create(name="Acme Corp", slug="acme")
    user = User.objects.create_user(
        email="manager@acme.com", password="pass", role=UserRole.MANAGER, organization=org
    )

    companies = []
    for i in range(10):
        comp = Company.objects.create(organization=org, name=f"Company {i}")
        companies.append(comp)

    for i in range(10):
        Contact.objects.create(
            organization=org,
            company=companies[i],
            first_name="First",
            last_name=f"Last {i}",
            email=f"contact{i}@example.com"
        )
    return user


@pytest.mark.django_db
class TestPerformance:

    def test_contacts_list_no_n_plus_one_queries(self, api_client, setup_n_plus_one_data):
        """
        Verify that fetching contacts uses select_related and avoids N+1 queries.
        Without select_related, this would be 1 query for contacts + 10 queries for companies = 11 queries.
        With select_related, it should be just a few constant queries (auth + pagination + main query).
        """
        user = setup_n_plus_one_data
        api_client.force_authenticate(user=user)

        # We use CaptureQueriesContext to count SQL queries executed
        with CaptureQueriesContext(connection) as ctx:
            response = api_client.get("/api/v1/contacts/")
        
        assert response.status_code == 200
        assert len(response.json()) == 10  # 10 contacts

        # 1 query for the contacts + companies + organizations JOIN.
        # No extra queries for each company's name.
        # Total queries should be very low (usually 1 for the main select).
        assert len(ctx.captured_queries) <= 3, f"Too many queries: {len(ctx.captured_queries)}. Possible N+1!"
