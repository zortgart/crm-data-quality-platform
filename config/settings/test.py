# =============================================================
# config/settings/test.py
# =============================================================
# TEST SETTINGS
#
# Used by pytest when running the test suite.
# Optimized for speed — no debug output, in-memory friendly.
# =============================================================

from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False

# Use a separate test database to avoid polluting dev data.
# pytest-django creates/destroys it automatically.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("TEST_DATABASE_NAME", default="crm_platform_test"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="5432"),
    }
}

# Faster password hashing in tests (MD5 vs PBKDF2)
# Security is NOT needed in test environment
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Suppress SQL logging during tests for cleaner output
LOGGING["loggers"]["django.db.backends"]["level"] = "WARNING"  # noqa: F405
