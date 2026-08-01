# =============================================================
# config/settings/base.py
# =============================================================
# BASE SETTINGS — shared across all environments
#
# Java/Spring Boot equivalent: application.properties / application.yml
# In Django, settings is a Python module, giving us full Python power
# (conditionals, environment reads, computed values).
#
# This file should NOT contain environment-specific values.
# Use development.py, test.py, or production.py for those.
# =============================================================

from pathlib import Path
from decouple import config

# BASE_DIR points to the project root (parent of config/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================
# SECURITY — secret key
# NEVER hardcode. Always read from environment.
# =============================================================
SECRET_KEY = config("DJANGO_SECRET_KEY")

# =============================================================
# INSTALLED APPS
# Django uses this list to discover models, admin, migrations.
# Java equivalent: Spring auto-configuration / @ComponentScan
# =============================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",  # Django REST Framework
]

LOCAL_APPS = [
    # Added phase by phase
    # Phase 1: common only (no models yet)
    "common",
    # Phase 2+: accounts, organizations, companies, contacts, etc.
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================
# MIDDLEWARE
# Processes every request/response pair in order (top = outermost).
# Java equivalent: Servlet Filters / Spring Interceptors
# =============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Phase 9: add RequestIDMiddleware, TenantMiddleware
]

ROOT_URLCONF = "config.urls"

# =============================================================
# TEMPLATES
# =============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# =============================================================
# DATABASE
# psycopg v3 (modern PostgreSQL adapter).
# Java equivalent: DataSource / JDBC URL / JPA persistence.xml
# =============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="5432"),
        "OPTIONS": {
            # Use psycopg v3 driver
            "connect_timeout": 10,
        },
    }
}

# =============================================================
# PASSWORD VALIDATION
# Django validates passwords against these rules on user creation.
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================
# INTERNATIONALIZATION
# =============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"          # Always UTC in backend — convert in client
USE_I18N = True
USE_TZ = True              # CRITICAL: always use timezone-aware datetimes

# =============================================================
# STATIC FILES
# =============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================
# DEFAULT PRIMARY KEY
# We will override with UUID on our custom models.
# =============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================
# DJANGO REST FRAMEWORK — base configuration
# Full config added in Phase 3 (auth) and Phase 4 (pagination)
# =============================================================
REST_FRAMEWORK = {
    # Return JSON by default; disable browsable API HTML in production
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Phase 3: add DEFAULT_AUTHENTICATION_CLASSES (JWT)
    # Phase 3: add DEFAULT_PERMISSION_CLASSES (IsAuthenticated)
    # Phase 4: add DEFAULT_PAGINATION_CLASS
    # Phase 9: add DEFAULT_THROTTLE_CLASSES (rate limiting)
}

# =============================================================
# LOGGING — structured logging
# Phase 9 will enhance this with correlation IDs and JSON format.
# =============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            # Set to DEBUG to log all SQL queries (useful during dev)
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
