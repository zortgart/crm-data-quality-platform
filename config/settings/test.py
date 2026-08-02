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
# Security# Disable password hashing overhead for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Run Celery tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Suppress SQL logging during tests for cleaner output
LOGGING["loggers"]["django.db.backends"]["level"] = "WARNING"  # noqa: F405
