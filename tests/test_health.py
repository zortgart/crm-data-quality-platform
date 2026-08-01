# =============================================================
# tests/test_health.py — Phase 1: Health Endpoint Tests
# =============================================================
# These are the first tests in the project.
# They verify the health and readiness endpoints work correctly.
#
# WHY test health endpoints?
#   - Confirms Django is correctly configured
#   - Confirms DRF routing works
#   - Confirms PostgreSQL connection is healthy
#   - Gives us confidence the foundation is solid
#
# HOW pytest-django works:
#   pytest-django creates a fresh test database before tests run
#   and destroys it after. Each test runs in a transaction that
#   is rolled back — so tests never pollute each other.
#
# Java equivalent:
#   @SpringBootTest + MockMvc / WebTestClient
#   @DataJpaTest for database-only tests
# =============================================================

import pytest
from rest_framework.test import APIClient
from rest_framework import status


@pytest.fixture
def api_client():
    """
    Provides a DRF test client.
    Java equivalent: MockMvc / RestTemplate in @SpringBootTest
    """
    return APIClient()


class TestHealthEndpoint:
    """Tests for GET /health/ (liveness check)"""

    def test_health_returns_200(self, api_client):
        """Health endpoint must always return 200 OK."""
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK

    def test_health_returns_correct_body(self, api_client):
        """Health response must contain status=ok and service name."""
        response = api_client.get("/health/")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "crm-data-quality-platform"

    def test_health_requires_no_authentication(self, api_client):
        """
        Health endpoint is unauthenticated by design.
        Load balancers and monitoring tools call it without credentials.
        """
        # No token set — this must still return 200
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK

    def test_health_is_fast(self, api_client):
        """
        Health check should complete very quickly (no DB calls).
        This is a soft check — just verifying it responds.
        """
        import time
        start = time.time()
        response = api_client.get("/health/")
        elapsed = time.time() - start
        assert response.status_code == status.HTTP_200_OK
        # Health check should respond in under 1 second
        assert elapsed < 1.0, f"Health check too slow: {elapsed:.3f}s"


@pytest.mark.django_db
class TestReadinessEndpoint:
    """
    Tests for GET /ready/ (readiness check).

    @pytest.mark.django_db: Required because readiness check queries PostgreSQL.
    Without this marker, Django's test framework would block DB access.
    """

    def test_readiness_returns_200_when_db_available(self, api_client):
        """
        Readiness endpoint returns 200 when PostgreSQL is available.
        pytest-django ensures the test database exists before this runs.
        """
        response = api_client.get("/ready/")
        assert response.status_code == status.HTTP_200_OK

    def test_readiness_returns_ready_status(self, api_client):
        """Readiness response contains status=ready when healthy."""
        response = api_client.get("/ready/")
        data = response.json()
        assert data["status"] == "ready"

    def test_readiness_includes_database_check(self, api_client):
        """Readiness response includes database health check result."""
        response = api_client.get("/ready/")
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
        assert data["checks"]["database"] == "ok"

    def test_readiness_requires_no_authentication(self, api_client):
        """Readiness endpoint is unauthenticated — same reason as health."""
        response = api_client.get("/ready/")
        assert response.status_code == status.HTTP_200_OK
