# =============================================================
# accounts/permissions.py — RBAC Permission Classes
# =============================================================
# DRF Permission classes control AUTHORIZATION: "What can you do?"
# They run AFTER authentication (who you are) is established.
#
# HOW permission classes work:
#   1. Request arrives
#   2. JWTAuthentication sets request.user (from token)
#   3. Permission class checks request.user.role
#   4. has_permission() returns True → allow, False → 403 Forbidden
#
# Java equivalent:
#   @PreAuthorize("hasRole('ADMIN')")
#   @Secured("ROLE_MANAGER")
#   HttpSecurity.authorizeHttpRequests()
#       .requestMatchers("/admin/**").hasRole("ADMIN")
#
# USAGE on a view:
#   @permission_classes([IsAdminRole])             → ADMIN only
#   @permission_classes([IsManagerOrAbove])        → ADMIN + MANAGER
#   @permission_classes([IsAnalystOrAbove])        → all logged-in users
#   @permission_classes([AllowAny])                → public (no login needed)
# =============================================================

from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsAdminRole(BasePermission):
    """
    Allows access only to users with ADMIN role.

    Use for:
    - User management endpoints
    - Organization settings
    - Audit log access
    - System configuration

    Java equivalent:
      @PreAuthorize("hasRole('ADMIN')")
    """
    message = "Access denied. Admin role required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsManagerOrAbove(BasePermission):
    """
    Allows access to MANAGER and ADMIN roles.

    Use for:
    - Creating/editing companies and contacts
    - Running enrichment jobs
    - Starting CSV imports
    - Viewing full data quality reports

    Java equivalent:
      @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    """
    message = "Access denied. Manager role or above required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [UserRole.ADMIN, UserRole.MANAGER]
        )


class IsAnalystOrAbove(BasePermission):
    """
    Allows access to all authenticated users (ANALYST, MANAGER, ADMIN).
    Effectively the same as IsAuthenticated but role-explicit.

    Use for:
    - Read-only list/detail endpoints
    - Dashboard and reporting
    - Exporting data

    Java equivalent:
      @PreAuthorize("isAuthenticated()")
    """
    message = "Access denied. Authentication required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
        )


class IsSameOrganization(BasePermission):
    """
    Object-level permission — verifies the object belongs to
    the requesting user's organization.

    This is TENANT ISOLATION enforcement at the object level.
    Prevents IDOR (Insecure Direct Object Reference) attacks.

    IDOR example without this:
      ACME user calls: GET /api/v1/contacts/some-uuid/
      If some-uuid belongs to GLOBEX org → should return 403
      Without this check → data leak!

    Java equivalent:
      @PostAuthorize("returnObject.organization.id == principal.organizationId")
    """
    message = "Access denied. Resource belongs to a different organization."

    def has_object_permission(self, request, view, obj):
        # obj is the model instance being accessed
        # Check that the object's organization matches the user's organization
        return obj.organization_id == request.user.organization_id
