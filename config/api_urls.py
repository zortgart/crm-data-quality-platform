# =============================================================
# config/api_urls.py — API v1 Router
# =============================================================
# All application API endpoints live under /api/v1/
# This file is included from config/urls.py
#
# Versioning strategy: URL versioning /api/v1/, /api/v2/
# This is the most explicit and client-friendly approach.
# Java equivalent: @RequestMapping("/api/v1")
#
# Added phase by phase:
#   Phase 3: auth endpoints
#   Phase 4: companies, contacts
#   Phase 7: imports
#   Phase 9: audit
# =============================================================

from django.urls import path, include

urlpatterns = [
    # ==========================================================
    # AUTHENTICATION — Phase 3
    # /api/v1/auth/login/
    # /api/v1/auth/logout/
    # /api/v1/auth/refresh/
    # /api/v1/auth/me/
    # ==========================================================
    path("auth/", include("accounts.urls")),

    # ==========================================================
    # COMPANIES — Phase 4
    path("companies/", include("companies.urls")),
    # ==========================================================

    # ==========================================================
    # CONTACTS — Phase 4
    path("contacts/", include("contacts.urls")),
    # ==========================================================

    # ==========================================================
    # IMPORTS — Phase 7
    path("imports/", include("imports.urls")),
    # ==========================================================
]
