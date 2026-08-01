# =============================================================
# config/settings/development.py
# =============================================================
# DEVELOPMENT SETTINGS — local Windows machine only
#
# This file extends base.py and adds development-specific config.
# Never use this in production.
#
# How Django knows to use this file:
#   Set DJANGO_SETTINGS_MODULE=config.settings.development
#   in your .env file or environment.
# =============================================================

from .base import *  # noqa: F401, F403
from decouple import config

# =============================================================
# SECURITY
# DEBUG=True enables:
#   - Detailed error pages with stack traces
#   - Browsable API in DRF
#   - Relaxed ALLOWED_HOSTS
# NEVER set DEBUG=True in production.
# =============================================================
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# =============================================================
# DRF: Enable Browsable API in development
# Overrides base.py which only has JSONRenderer
# =============================================================
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # Inherit base config
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # Dev only
    ],
}

# =============================================================
# DATABASE LOGGING
# Log all SQL queries to console during development.
# Useful for catching N+1 problems.
# WARNING: Very verbose — comment out when not needed.
# =============================================================
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"  # noqa: F405

# =============================================================
# DJANGO EXTENSIONS
# Adds useful management commands: shell_plus, runserver_plus, etc.
# shell_plus auto-imports all models — very handy during dev.
# =============================================================
INSTALLED_APPS = INSTALLED_APPS + ["django_extensions"]  # noqa: F405
