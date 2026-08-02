# =============================================================
# accounts/urls.py — Auth URL Patterns
# =============================================================
# All auth endpoints live under /api/v1/auth/
# This file is included in config/api_urls.py
# =============================================================

from django.urls import path
from .views import LoginView, logout_view, RefreshView, me_view

urlpatterns = [
    # POST /api/v1/auth/login/
    # Body: { "email": "...", "password": "..." }
    # Returns: { access, refresh, user }
    path("login/", LoginView.as_view(), name="auth-login"),

    # POST /api/v1/auth/logout/
    # Body: { "refresh": "..." }
    # Blacklists refresh token
    path("logout/", logout_view, name="auth-logout"),

    # POST /api/v1/auth/refresh/
    # Body: { "refresh": "..." }
    # Returns: { access, refresh }
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),

    # GET /api/v1/auth/me/
    # Returns current user profile
    path("me/", me_view, name="auth-me"),
]
