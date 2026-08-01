# =============================================================
# config/wsgi.py — WSGI Application Entry Point
# =============================================================
# WSGI = Web Server Gateway Interface
# This is how production web servers (gunicorn, uWSGI) talk to Django.
#
# Java equivalent: web.xml servlet configuration / Tomcat connector
#
# For development we use `manage.py runserver` which uses this internally.
# For production (Phase 9+) we would use gunicorn:
#   gunicorn config.wsgi:application
# =============================================================

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_wsgi_application()
