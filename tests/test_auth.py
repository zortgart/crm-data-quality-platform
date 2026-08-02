# =============================================================
# tests/test_auth.py — Phase 3: Auth + RBAC + Tenant Tests
# =============================================================

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from organizations.models import Organization
from accounts.models import UserRole

User = get_user_model()


# =============================================================
# SHARED FIXTURES
# =============================================================
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org_acme(db):
    return Organization.objects.create(name="Acme Corp", slug="acme-corp")


@pytest.fixture
def org_globex(db):
    return Organization.objects.create(name="Globex Corp", slug="globex-corp")


@pytest.fixture
def admin_user(org_acme):
    return User.objects.create_user(
        email="admin@acme.com", password="StrongPass123!",
        first_name="Alice", last_name="Admin",
        role=UserRole.ADMIN, organization=org_acme,
    )


@pytest.fixture
def manager_user(org_acme):
    return User.objects.create_user(
        email="manager@acme.com", password="StrongPass123!",
        first_name="Bob", last_name="Manager",
        role=UserRole.MANAGER, organization=org_acme,
    )


@pytest.fixture
def analyst_user(org_acme):
    return User.objects.create_user(
        email="analyst@acme.com", password="StrongPass123!",
        first_name="Carol", last_name="Analyst",
        role=UserRole.ANALYST, organization=org_acme,
    )


@pytest.fixture
def globex_user(org_globex):
    return User.objects.create_user(
        email="user@globex.com", password="StrongPass123!",
        first_name="Dave", last_name="Globex",
        role=UserRole.ANALYST, organization=org_globex,
    )


# =============================================================
# LOGIN TESTS
# =============================================================
@pytest.mark.django_db
class TestLoginEndpoint:

    def test_login_success_returns_tokens(self, api_client, analyst_user):
        """Successful login returns access + refresh tokens."""
        response = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "StrongPass123!",
        }, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_returns_user_info(self, api_client, analyst_user):
        """Login response includes user profile in body."""
        response = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "StrongPass123!",
        }, format="json")
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "analyst@acme.com"
        assert data["user"]["role"] == UserRole.ANALYST

    def test_login_wrong_password_returns_401(self, api_client, analyst_user):
        """Wrong password must return 401."""
        response = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "WrongPassword!",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user_returns_401(self, api_client):
        """Non-existent email must return 401."""
        response = api_client.post("/api/v1/auth/login/", {
            "email": "nobody@example.com",
            "password": "AnyPassword123!",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_requires_email_field(self, api_client):
        """Missing email field returns 400."""
        response = api_client.post("/api/v1/auth/login/", {
            "password": "SomePass123!",
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_no_credentials_returns_400(self, api_client):
        """Empty body returns 400."""
        response = api_client.post("/api/v1/auth/login/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================
# ME ENDPOINT TESTS
# =============================================================
@pytest.mark.django_db
class TestMeEndpoint:

    def test_me_returns_profile_when_authenticated(self, api_client, analyst_user):
        """GET /auth/me/ returns user profile when token is valid."""
        # Login to get token
        login_resp = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "StrongPass123!",
        }, format="json")
        token = login_resp.json()["access"]

        # Call /me/ with the token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "analyst@acme.com"
        assert data["role"] == UserRole.ANALYST
        assert "full_name" in data

    def test_me_returns_401_without_token(self, api_client):
        """GET /auth/me/ returns 401 when no token provided."""
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_401_with_invalid_token(self, api_client):
        """GET /auth/me/ returns 401 with a bad token."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================
# LOGOUT TESTS
# =============================================================
@pytest.mark.django_db
class TestLogoutEndpoint:

    def test_logout_blacklists_refresh_token(self, api_client, analyst_user):
        """After logout, the refresh token cannot be used again."""
        # Login
        login_resp = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "StrongPass123!",
        }, format="json")
        tokens = login_resp.json()
        access = tokens["access"]
        refresh = tokens["refresh"]

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_resp = api_client.post("/api/v1/auth/logout/", {
            "refresh": refresh,
        }, format="json")
        assert logout_resp.status_code == status.HTTP_200_OK

        # Try to refresh with the blacklisted token — must fail
        api_client.credentials()
        refresh_resp = api_client.post("/api/v1/auth/refresh/", {
            "refresh": refresh,
        }, format="json")
        assert refresh_resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requires_authentication(self, api_client):
        """Logout without a token returns 401."""
        response = api_client.post("/api/v1/auth/logout/", {
            "refresh": "some-token",
        }, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================
# RBAC PERMISSION TESTS
# =============================================================
@pytest.mark.django_db
class TestRBACPermissions:

    def _get_token(self, api_client, email, password):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": email, "password": password,
        }, format="json")
        return resp.json()["access"]

    def test_admin_role_property(self, admin_user):
        """ADMIN user's is_admin property returns True."""
        assert admin_user.is_admin is True
        assert admin_user.is_manager is True

    def test_manager_role_property(self, manager_user):
        """MANAGER user's is_admin is False, is_manager is True."""
        assert manager_user.is_admin is False
        assert manager_user.is_manager is True

    def test_analyst_role_property(self, analyst_user):
        """ANALYST is neither admin nor manager."""
        assert analyst_user.is_admin is False
        assert analyst_user.is_manager is False

    def test_me_shows_correct_role_for_admin(self, api_client, admin_user):
        """Admin user sees ADMIN role in /me/ response."""
        token = self._get_token(api_client, "admin@acme.com", "StrongPass123!")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.json()["role"] == UserRole.ADMIN

    def test_me_shows_correct_role_for_manager(self, api_client, manager_user):
        """Manager user sees MANAGER role in /me/ response."""
        token = self._get_token(api_client, "manager@acme.com", "StrongPass123!")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.json()["role"] == UserRole.MANAGER


# =============================================================
# TENANT ISOLATION TESTS
# =============================================================
@pytest.mark.django_db
class TestTenantIsolation:

    def test_users_from_different_orgs_are_separate(self, analyst_user, globex_user):
        """Users from different organizations are in different tenants."""
        assert analyst_user.organization != globex_user.organization

    def test_org_users_reverse_lookup(self, org_acme, analyst_user, manager_user, globex_user):
        """org.users.all() only returns users in that org."""
        acme_users = list(org_acme.users.all())
        assert analyst_user in acme_users
        assert manager_user in acme_users
        assert globex_user not in acme_users  # belongs to globex

    def test_user_org_id_in_me_response(self, api_client, analyst_user, org_acme):
        """ME response includes the user's organization_id."""
        login_resp = api_client.post("/api/v1/auth/login/", {
            "email": "analyst@acme.com",
            "password": "StrongPass123!",
        }, format="json")
        token = login_resp.json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.json()["organization_id"] == str(org_acme.id)
