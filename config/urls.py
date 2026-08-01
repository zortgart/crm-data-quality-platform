# =============================================================
# config/urls.py — Root URL Configuration
# =============================================================
# This is the entry point for ALL HTTP requests.
# Django matches URL patterns top-to-bottom and stops at first match.
#
# Java/Spring Boot equivalent: @RequestMapping at the controller level
# but centralized in web.xml or WebMvcConfigurer.
#
# URL patterns are added phase by phase:
#   Phase 1: health + ready endpoints only
#   Phase 3: auth endpoints
#   Phase 4: companies, contacts
#   Phase 7: imports
#   Phase 9: audit, dashboard
# =============================================================

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin — useful for exploring data during development
    # Phase 3: we will restrict this or add custom admin
    path("admin/", admin.site.urls),

    # =========================================================
    # Health / Readiness Checks
    # Phase 1: liveness + readiness
    # These are unauthenticated by design — load balancers call them.
    # =========================================================
    path("", include("common.urls")),

    # =========================================================
    # API v1 — All application endpoints live under /api/v1/
    # Added phase by phase:
    # path("api/v1/", include("config.api_urls")),
    # =========================================================
]
