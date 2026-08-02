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

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsManagerOrAbove, IsAnalystOrAbove, IsSameOrganization
from .models import Company
from .serializers import CompanyListSerializer, CompanyDetailSerializer
from enrichment.service import get_enrichment_provider


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

    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        """
        List companies. Cached for 5 minutes per user/token to prevent DB hits.
        """
        return super().list(request, *args, **kwargs)

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

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def enrich(self, request, pk=None):
        """
        Phase 11: Call the configured AI provider to enrich this company.
        """
        company = self.get_object()
        provider = get_enrichment_provider()
        
        enriched_data = provider.enrich_company(company.name, company.domain)
        
        updated = False
        if "industry" in enriched_data and not company.industry:
            company.industry = enriched_data["industry"]
            updated = True
            
        if "size" in enriched_data and not company.size:
            company.size = enriched_data["size"]
            updated = True
            
        if "description" in enriched_data and not company.description:
            company.description = enriched_data["description"]
            updated = True
            
        if updated:
            company.save(update_fields=["industry", "size", "description"])
            
        serializer = self.get_serializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
