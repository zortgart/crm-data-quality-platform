# =============================================================
# accounts/views.py — Auth API Endpoints
# =============================================================
# Endpoints:
#   POST /api/v1/auth/login/    → email + password → tokens + user info
#   POST /api/v1/auth/logout/   → blacklist refresh token
#   POST /api/v1/auth/refresh/  → swap refresh token for new access token
#   GET  /api/v1/auth/me/       → current user profile
#
# Java equivalent: AuthController / SecurityController
# =============================================================

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import CustomTokenObtainPairSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)


# =============================================================
# LOGIN
# POST /api/v1/auth/login/
# =============================================================
class LoginView(TokenObtainPairView):
    """
    Login endpoint.

    Accepts: { "email": "...", "password": "..." }
    Returns: {
        "access":  "<short-lived JWT>",
        "refresh": "<long-lived JWT>",
        "user": { id, email, role, full_name, organization_id }
    }

    Uses our custom serializer which:
    - Validates email + password (simplejwt handles this)
    - Adds custom claims (role, org_id) to the JWT payload
    - Adds user info to the response body

    Java equivalent:
      @PostMapping("/auth/login")
      public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request)
    """
    serializer_class = CustomTokenObtainPairSerializer
    # AllowAny: this endpoint is public — user is not logged in yet
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            logger.info("User logged in: %s", request.data.get("email", "unknown"))
        return response


# =============================================================
# LOGOUT
# POST /api/v1/auth/logout/
# =============================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint.

    Accepts: { "refresh": "<refresh_token>" }
    Blacklists the refresh token so it can't be reused.
    The access token will still work until it expires (60 min).

    WHY can't we invalidate the access token?
      JWTs are stateless — there's no server-side session to destroy.
      We can only blacklist the refresh token (which has a DB record).
      This is a known JWT trade-off vs. session-based auth.
      Production mitigation: keep access token lifetime very short (15-60 min).

    Java equivalent:
      POST /auth/logout → invalidate the refresh token in a DB blacklist table
    """
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        logger.info("User logged out: %s", request.user.email)
        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
    except TokenError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


# =============================================================
# REFRESH TOKEN
# POST /api/v1/auth/refresh/
# =============================================================
class RefreshView(TokenRefreshView):
    """
    Token refresh endpoint.

    Accepts: { "refresh": "<refresh_token>" }
    Returns: { "access": "<new_access_token>", "refresh": "<new_refresh_token>" }

    Because ROTATE_REFRESH_TOKENS=True in settings:
    - Old refresh token is blacklisted
    - New refresh token is returned
    This prevents refresh token reuse (important for security).

    Java equivalent:
      POST /auth/refresh → validate refresh token → return new access token
    """
    # Uses simplejwt's built-in TokenRefreshView
    # No customization needed — inherits AllowAny from simplejwt defaults
    pass


# =============================================================
# ME — CURRENT USER PROFILE
# GET /api/v1/auth/me/
# =============================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Returns the currently authenticated user's profile.

    The JWT token is verified by JWTAuthentication middleware.
    request.user is already populated with the User instance.
    No DB query needed for the token verification — it's stateless.
    One DB query to fetch the full user profile.

    Java equivalent:
      @GetMapping("/auth/me")
      public UserDTO getCurrentUser(@AuthenticationPrincipal UserDetails user)
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)
