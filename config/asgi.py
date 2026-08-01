# =============================================================
# config/asgi.py — ASGI Application Entry Point
# =============================================================
# ASGI = Asynchronous Server Gateway Interface
# The modern successor to WSGI, supporting async/WebSockets.
# Django 5.x supports async views natively.
#
# We configure this now but won't use async features until later phases.
# =============================================================

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_asgi_application()
