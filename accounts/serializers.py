# =============================================================
# accounts/serializers.py — Request/Response Shape Definitions
# =============================================================
# Serializers in DRF serve two purposes:
#   1. DESERIALIZATION: Validate incoming request data (like @RequestBody in Java)
#   2. SERIALIZATION: Convert model instances to JSON (like @JsonView or DTO)
#
# Java equivalent:
#   - Input validation: @Valid + DTO + Bean Validation (@NotNull, @Email)
#   - Output: Jackson ObjectMapper / @JsonProperty
# =============================================================

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# =============================================================
# CUSTOM JWT TOKEN SERIALIZER
# Adds extra claims to the JWT payload
# =============================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends simplejwt's default token serializer to:
    1. Add custom claims to the JWT payload (role, org_id)
    2. Return a richer login response (user info alongside tokens)

    WHY add claims to the token?
      The client (React, mobile app) can decode the JWT and immediately
      know the user's role and organization WITHOUT a separate API call.
      JWT payload is Base64-encoded — not encrypted, but signed.

    Java equivalent:
      JwtTokenProvider.createToken() that adds custom claims
      via Claims.put("role", user.getRole())
    """

    @classmethod
    def get_token(cls, user):
        """
        This method builds the JWT payload.
        Called when a user logs in successfully.
        """
        token = super().get_token(user)

        # Add custom claims to the JWT payload
        # These are readable by the client (Base64 decoded)
        # but the signature prevents tampering
        token["email"] = user.email
        token["role"] = user.role
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["organization_id"] = str(user.organization_id) if user.organization_id else None

        return token

    def validate(self, attrs):
        """
        Called during login. Validates credentials and returns tokens + user info.
        """
        # Let simplejwt do its email + password validation
        data = super().validate(attrs)

        # Add user info to the login response body
        # The client gets tokens + user details in one request
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "full_name": self.user.full_name,
            "role": self.user.role,
            "organization_id": str(self.user.organization_id) if self.user.organization_id else None,
        }
        return data


# =============================================================
# USER SERIALIZER — for GET /auth/me/ response
# =============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the current user's profile.
    Used by GET /api/v1/auth/me/

    Java equivalent:
      A UserDTO / UserResponse record with @JsonProperty fields
    """
    full_name = serializers.CharField(read_only=True)
    organization_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "organization_id",
            "is_active",
            "created_at",
        ]
        # read_only_fields: these are NEVER accepted as input, only returned
        read_only_fields = fields
