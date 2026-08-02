import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from accounts.models import User
from organizations.models import Organization

def create_test_users():
    # Ensure an organization exists
    org, _ = Organization.objects.get_or_create(
        name="Test Organization",
        defaults={"slug": "test-org"}
    )

    email = "admin@example.com"
    password = "password123"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": "Test",
            "last_name": "Admin",
            "role": "ADMIN",
            "organization": org,
            "is_staff": True,
            "is_superuser": True
        }
    )

    if not created:
        # Update password just to be 100% sure we know what it is
        user.set_password(password)
        user.save()
        print(f"Updated password for {email}")
    else:
        user.set_password(password)
        user.save()
        print(f"Created user {email}")

if __name__ == "__main__":
    create_test_users()
