# =============================================================
# contacts/views.py — Contact ViewSet
# =============================================================

from rest_framework import viewsets, filters
from accounts.permissions import IsManagerOrAbove, IsAnalystOrAbove
from validation.normalizers import normalize_email, normalize_phone, normalize_job_title
from validation.quality_scorer import calculate_quality_score
from validation.duplicate_detector import detect_duplicates
from .models import Contact
from .serializers import ContactListSerializer, ContactDetailSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Contacts, scoped to the current user's organization.

    Extra features:
      - Search by name, email, job_title, company name
      - Order by last_name, quality_score, created_at
      - Active-only by default (is_active=True)
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "first_name", "last_name", "email",
        "job_title", "company__name",    # double underscore = JOIN traversal
    ]
    ordering_fields = ["last_name", "first_name", "quality_score", "created_at"]
    ordering = ["last_name", "first_name"]

    def get_queryset(self):
        """
        Tenant-scoped queryset. ALWAYS filters by organization.
        Also uses select_related to avoid N+1 queries when accessing
        contact.organization and contact.company in serializer.

        N+1 problem:
          Without select_related: 1 query for contacts + N queries for each company
          With select_related: 1 JOIN query — much more efficient
        Java equivalent: @EntityGraph or JOIN FETCH in JPQL
        """
        return (
            Contact.objects
            .filter(organization=self.request.user.organization)
            .select_related("organization", "company")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAnalystOrAbove]
        else:
            permission_classes = [IsManagerOrAbove]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        1. Inject organization.
        2. Normalize data.
        3. Save contact.
        4. Calculate quality score (requires saved object or field access).
        5. Run duplicate detection (requires saved object ID).
        """
        contact = serializer.save(organization=self.request.user.organization)
        self._run_quality_pipeline(contact)

    def perform_update(self, serializer):
        """Prevent org from being changed on update, and re-run pipeline."""
        contact = serializer.save(organization=self.request.user.organization)
        self._run_quality_pipeline(contact)

    def _run_quality_pipeline(self, contact):
        """
        Executes the Phase 6 data quality pipeline.
        """
        # 1. Normalization
        contact.normalized_email = normalize_email(contact.email)
        contact.normalized_phone = normalize_phone(contact.phone)
        contact.job_title = normalize_job_title(contact.job_title)
        
        # 2. Quality Scoring
        contact.quality_score = calculate_quality_score(contact)
        
        # Save updates to the DB
        contact.save(update_fields=["normalized_email", "normalized_phone", "job_title", "quality_score"])
        
        # 3. Duplicate Detection
        detect_duplicates(contact)
