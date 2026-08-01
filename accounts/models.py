# =============================================================
# accounts/models.py — Custom User Model
# =============================================================
#
# WHY a Custom User model?
#   Django's built-in User uses `username` as the login field.
#   Modern apps use EMAIL as the login field.
#   We also need to attach a `role` (ADMIN/MANAGER/ANALYST)
#   and link the user to an Organization (tenant).
#
# WHY do this NOW, in Phase 2, before anything else?
#   Django's AUTH_USER_MODEL CANNOT be easily changed after
#   the first migration is applied. This is a one-way door.
#   Always set up CustomUser FIRST — before any real migrations.
#
# WHICH base class to use?
#
#   AbstractUser      → extends Django's built-in user (keeps username,
#                        first_name, last_name etc.) — easier but less control
#
#   AbstractBaseUser  → bare minimum: only password + is_active.
#                        You define EVERY field yourself. Full control.
#                        We use this because we want email as login field
#                        and we don't want the username field at all.
#
# Java equivalent:
#   Spring Security UserDetails interface
#   + a @Entity User class implementing it
#   + a UserDetailsService for loading users
# =============================================================

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from common.models import TimeStampedModel


# =============================================================
# ROLES
# =============================================================
class UserRole(models.TextChoices):
    """
    RBAC roles for the platform.

    TextChoices creates an enum-like class where:
      UserRole.ADMIN         → the Python constant
      UserRole.ADMIN.value   → "ADMIN" (stored in DB)
      UserRole.ADMIN.label   → "Admin" (displayed in UI/admin)

    Java equivalent:
      public enum UserRole { ADMIN, MANAGER, ANALYST }
      with @Enumerated(EnumType.STRING) on the field
    """
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    ANALYST = "ANALYST", "Analyst"


# =============================================================
# CUSTOM USER MANAGER
# =============================================================
class UserManager(BaseUserManager):
    """
    Manager tells Django HOW to create users.
    Required when using AbstractBaseUser.

    Java equivalent:
      A UserService/UserRepository that handles user creation.
      Spring Security's UserDetailsService.loadUserByUsername()
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Standard user creation.
        Called when registering a normal user.
        """
        if not email:
            raise ValueError("Email address is required.")
        # normalize_email lowercases the domain part:
        # "User@GMAIL.COM" → "User@gmail.com"
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password hashes the password using PBKDF2 + SHA256.
        # NEVER store plain text passwords.
        # Java equivalent: BCryptPasswordEncoder.encode(password)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates a superuser (Django admin access).
        Used by: python manage.py createsuperuser
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        return self.create_user(email, password, **extra_fields)


# =============================================================
# CUSTOM USER MODEL
# =============================================================
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Our application's User model.

    Replaces Django's built-in auth.User entirely.
    Configured via: AUTH_USER_MODEL = 'accounts.User'

    Key differences from Django's default User:
      - UUID primary key (not integer)
      - Email as login field (not username)
      - No username field at all
      - Has role field (ADMIN/MANAGER/ANALYST)
      - Linked to Organization (tenant)
      - created_at / updated_at via TimeStampedModel

    AbstractBaseUser provides:
      - password field (hashed)
      - last_login field
      - set_password() method
      - check_password() method

    PermissionsMixin provides:
      - is_superuser field
      - groups, user_permissions (Django's permission system)

    Java equivalent:
      @Entity
      public class User implements UserDetails {
          @Id UUID id;
          String email;
          String passwordHash;
          UserRole role;
          @ManyToOne Organization organization;
      }
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        # unique=True → PostgreSQL UNIQUE constraint on email column
        # Attempting to create duplicate email → IntegrityError
        help_text="Used as the login identifier. Must be unique."
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ANALYST,
        # New users default to ANALYST (least privileged).
        # Principle of least privilege — important security concept.
        # Java equivalent: @Column with @Enumerated(EnumType.STRING)
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        # String reference "organizations.Organization" instead of
        # direct import — avoids circular import issues.
        on_delete=models.CASCADE,
        # CASCADE: if Organization is deleted → all its Users are deleted too
        # Other options: SET_NULL, PROTECT (prevents deletion if users exist)
        null=True,
        blank=True,
        # null=True: organization_id can be NULL in DB (for superusers with no org)
        related_name="users",
        # Allows: organization.users.all() → get all users of an org
        # Java equivalent: @OneToMany(mappedBy="organization") List<User> users
    )

    is_active = models.BooleanField(default=True)
    # is_active=False → user cannot log in (soft disable, not deleted)

    is_staff = models.BooleanField(default=False)
    # is_staff=True → user can access Django admin (/admin/)

    # Tell Django: "use email to log in, not username"
    USERNAME_FIELD = "email"

    # Fields required when using createsuperuser command (besides email+password)
    REQUIRED_FIELDS = ["first_name", "last_name"]

    # Use our custom manager
    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        ordering = ["email"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """
        Computed property — not stored in DB, calculated on the fly.
        Java equivalent: @Transient String getFullName()
        """
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
