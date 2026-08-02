# =============================================================
# companies/views.py — Company ViewSet
# =============================================================
# ModelViewSet automatically gives us:
#   list()           GET  /companies/
#   create()         POST /companies/
#   retrieve()       GET  /companies/{id}/
#   update()         PUT  /companies/{id}/
#   partial_update() PATCH /companies/{id}/
#   destroy()        DELETE /companies/{id}/
#
# Java equivalent:
#   @RestController + @GetMapping, @PostMapping, @PutMapping etc.
#   OR Spring Data REST (which also auto-generates endpoints)
# =============================================================

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsManagerOrAbove, IsAnalystOrAbove, IsSameOrganization
from .models import Company
from .serializers import CompanyListSerializer, CompanyDetailSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Companies.

    TENANT ISOLATION:
      get_queryset() filters by request.user.organization.
      A user from Org A CANNOT see Org B's companies — ever.

    RBAC:
      Read  (list, retrieve)  → IsAnalystOrAbove  (all logged-in users)
      Write (create, update, delete) → IsManagerOrAbove (MANAGER + ADMIN)
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "domain", "industry", "city", "country"]
    ordering_fields = ["name", "created_at", "industry"]
    ordering = ["name"]  # default ordering

    def get_queryset(self):
        """
        CRITICAL: Always scope to the current user's organization.
        This is the primary tenant isolation mechanism.

        Java equivalent:
            companyRepository.findAllByOrganizationId(currentUser.getOrganizationId())
        """
        return Company.objects.filter(
            organization=self.request.user.organization
        ).select_related("organization")
        # select_related("organization") → SQL JOIN instead of N+1 queries
        # Java equivalent: @EntityGraph or JOIN FETCH

    def get_serializer_class(self):
        """
        Use lightweight serializer for list, full serializer for everything else.
        Java equivalent: different @JsonView profiles per endpoint.
        """
        if self.action == "list":
            return CompanyListSerializer
        return CompanyDetailSerializer

    def get_permissions(self):
        """
        Dynamic permission assignment based on the HTTP action.

        Read actions (safe methods) → ANALYST or above
        Write actions (unsafe)      → MANAGER or above

        Java equivalent:
            @GetMapping → @PreAuthorize("isAuthenticated()")
            @PostMapping → @PreAuthorize("hasAnyRole('ADMIN','MANAGER')")
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAnalystOrAbove]
        else:
            permission_classes = [IsManagerOrAbove]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        SECURITY: Always inject organization from request.user.
        The client CANNOT set the organization field.

        Java equivalent:
            company.setOrganization(currentUser.getOrganization());
            companyRepository.save(company);
        """
        serializer.save(organization=self.request.user.organization)

    def perform_update(self, serializer):
        """Prevent organization from being changed on update."""
        serializer.save(organization=self.request.user.organization)
