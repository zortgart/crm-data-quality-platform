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
    "rest_framework",                            # Django REST Framework
    "rest_framework_simplejwt",                  # JWT authentication (Phase 3)
    "rest_framework_simplejwt.token_blacklist",  # Token blacklist for logout
    # Phase 9+: django_filters, django_ratelimit
]

LOCAL_APPS = [
    "accounts.apps.AccountsConfig",
    "organizations.apps.OrganizationsConfig",
    "companies.apps.CompaniesConfig",
    "contacts.apps.ContactsConfig",
    "validation.apps.ValidationConfig",
    "imports.apps.ImportsConfig",
    "core.apps.CoreConfig",
    "notifications.apps.NotificationsConfig",
    "enrichment.apps.EnrichmentConfig",
    "common",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================
# CUSTOM USER MODEL
# =============================================================
# CRITICAL: Must be set BEFORE the first migration.
# Tells Django to use our custom User instead of auth.User.
# After this is set and migrations applied, changing it is
# extremely painful — this is a one-way door.
#
# Java equivalent:
#   Spring Security's UserDetails implementation class
#   configured in SecurityConfig.userDetailsService()
# =============================================================
AUTH_USER_MODEL = "accounts.User"

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
    "core.middleware.RequestIDMiddleware",
    "core.middleware.AuditLogMiddleware",
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

# CORS settings (Phase 3)
CORS_ALLOW_ALL_ORIGINS = True # For local development
CORS_ALLOW_CREDENTIALS = True

# Celery Configuration (Phase 8)
# We default to memory/dummy for local tests if redis isn't present, but expect redis
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE              # CRITICAL: always use timezone-aware datetimes

# Caching Configuration (Phase 9)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
    }
}

# =============================================================
# STATIC FILES
# =============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================
# DEFAULT PRIMARY KEY
# We will override with UUID on our custom models.
# =============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================
# DJANGO REST FRAMEWORK
# Phase 3: JWT authentication + IsAuthenticated by default
# Phase 4: pagination
# Phase 9: throttling (rate limiting)
#
# Java equivalent: Spring Security's HttpSecurity config
# =============================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle"
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day"
    }
}

# =============================================================
# JWT CONFIGURATION (djangorestframework-simplejwt)
# =============================================================
# Java equivalent: JwtProperties / JwtTokenProvider in Spring Security
# =============================================================
from datetime import timedelta

SIMPLE_JWT = {
    # Access token: short-lived. Sent with every API request.
    # If stolen, attacker can use it for at most 60 minutes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),

    # Refresh token: long-lived. Only sent to /auth/refresh/ endpoint.
    # Stored securely by the client (e.g. httpOnly cookie in production).
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),

    # On each /refresh/ call, issue a new refresh token and
    # blacklist the old one. Prevents refresh token reuse.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,

    # JWT algorithm: HMAC-SHA256 (symmetric)
    # Production upgrade option: RS256 (asymmetric, separate sign/verify keys)
    "ALGORITHM": "HS256",

    # Authorization: Bearer <token>
    "AUTH_HEADER_TYPES": ("Bearer",),

    # Which User field is embedded in the token payload
    # Our User uses UUID id, not integer
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",

    # Custom claims added to the token payload
    # We'll inject role + organization_id in Phase 3 token serializer
    "TOKEN_OBTAIN_SERIALIZER": "accounts.serializers.CustomTokenObtainPairSerializer",
}

# =============================================================
# LOGGING — structured logging
# Phase 9 will enhance this with correlation IDs and JSON format.
# =============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "core.log_filters.RequestIdFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "INFO {asctime} [{correlation_id}] {module}:{filename}:{lineno} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_id"],
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
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
