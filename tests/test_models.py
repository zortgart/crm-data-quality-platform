# =============================================================
# tests/test_models.py — Phase 2: Model Tests
# =============================================================

import pytest
from django.contrib.auth import get_user_model
from organizations.models import Organization
from accounts.models import UserRole

User = get_user_model()


# =============================================================
# ORGANIZATION TESTS
# =============================================================
@pytest.mark.django_db
class TestOrganizationModel:

    def test_create_organization(self):
        """Organization can be created with required fields."""
        org = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        assert org.id is not None        # UUID assigned
        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert org.is_active is True     # default

    def test_organization_str(self):
        """__str__ returns the organization name."""
        org = Organization.objects.create(name="Test Org", slug="test-org")
        assert str(org) == "Test Org"

    def test_organization_slug_is_unique(self):
        """Duplicate slugs must raise an IntegrityError."""
        from django.db import IntegrityError
        Organization.objects.create(name="Org A", slug="same-slug")
        with pytest.raises(IntegrityError):
            Organization.objects.create(name="Org B", slug="same-slug")

    def test_organization_has_timestamps(self):
        """created_at and updated_at are auto-populated."""
        org = Organization.objects.create(name="Timestamped Org", slug="ts-org")
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_id_is_uuid(self):
        """Primary key must be a UUID, not an integer."""
        import uuid
        org = Organization.objects.create(name="UUID Org", slug="uuid-org")
        assert isinstance(org.id, uuid.UUID)


# =============================================================
# USER TESTS
# =============================================================
@pytest.mark.django_db
class TestUserModel:

    def setup_method(self):
        """Create a test organization used by multiple tests."""
        self.org = Organization.objects.create(name="Test Corp", slug="test-corp")

    def test_create_user(self):
        """User can be created with email and password."""
        user = User.objects.create_user(
            email="analyst@example.com",
            password="SecurePass123!",
            first_name="Jane",
            last_name="Doe",
            organization=self.org,
        )
        assert user.email == "analyst@example.com"
        assert user.first_name == "Jane"
        assert user.is_active is True

    def test_password_is_hashed(self):
        """Password must NEVER be stored as plain text."""
        user = User.objects.create_user(
            email="hashed@example.com",
            password="PlainPassword123!",
        )
        # password field stores the HASH, not the plain text
        assert user.password != "PlainPassword123!"
        # But check_password verifies correctly
        assert user.check_password("PlainPassword123!") is True
        assert user.check_password("WrongPassword") is False

    def test_default_role_is_analyst(self):
        """New users default to ANALYST — principle of least privilege."""
        user = User.objects.create_user(email="new@example.com", password="pass")
        assert user.role == UserRole.ANALYST

    def test_email_is_unique(self):
        """Duplicate emails must raise IntegrityError."""
        from django.db import IntegrityError
        User.objects.create_user(email="unique@example.com", password="pass1")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="unique@example.com", password="pass2")

    def test_full_name_property(self):
        """full_name computed property returns first + last name."""
        user = User.objects.create_user(
            email="full@example.com",
            password="pass",
            first_name="John",
            last_name="Smith",
        )
        assert user.full_name == "John Smith"

    def test_user_belongs_to_organization(self):
        """User can be linked to an Organization (tenant)."""
        user = User.objects.create_user(
            email="org@example.com",
            password="pass",
            organization=self.org,
        )
        assert user.organization == self.org
        # Reverse relation: org.users.all()
        assert user in self.org.users.all()

    def test_is_admin_property(self):
        """is_admin property returns True only for ADMIN role."""
        admin = User.objects.create_user(
            email="admin@example.com", password="pass", role=UserRole.ADMIN
        )
        analyst = User.objects.create_user(
            email="analyst2@example.com", password="pass", role=UserRole.ANALYST
        )
        assert admin.is_admin is True
        assert analyst.is_admin is False

    def test_email_normalized_on_create(self):
        """Email domain is lowercased on creation."""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM",
            password="pass",
        )
        assert user.email == "Test@example.com"

    def test_user_id_is_uuid(self):
        """User primary key must be UUID."""
        import uuid
        user = User.objects.create_user(email="uuid@example.com", password="pass")
        assert isinstance(user.id, uuid.UUID)
