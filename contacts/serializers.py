# =============================================================
# contacts/serializers.py
# =============================================================

from rest_framework import serializers
from .models import Contact


class ContactListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view — minimal fields."""
    full_name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True, default=None)

    class Meta:
        model = Contact
        fields = [
            "id", "full_name", "email", "phone",
            "job_title", "company_name", "quality_score", "is_active",
        ]
        read_only_fields = ["id", "full_name", "company_name", "quality_score"]


class ContactDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for create / retrieve / update.

    organization is NEVER accepted from client.
    It is always set from request.user.organization in perform_create().

    company is accepted as a UUID (company_id).
    We validate it belongs to the same organization (tenant safety).
    """
    full_name = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True, default=None)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "organization_name",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "job_title",
            "linkedin_url",
            "company",        # UUID input (FK)
            "company_name",   # string output (read-only)
            "city",
            "country",
            "quality_score",
            "normalized_email",
            "normalized_phone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "full_name", "company_name", "organization_name",
            "quality_score", "normalized_email", "normalized_phone",
            "created_at", "updated_at",
        ]

    def validate_company(self, company):
        """
        Validate that the chosen company belongs to the same organization.
        Prevents a user from linking a contact to another org's company.

        Java equivalent:
            if (!company.getOrganization().equals(currentUser.getOrganization())) {
                throw new AccessDeniedException("Company belongs to different org");
            }
        """
        if company is None:
            return company
        request = self.context.get("request")
        if request and company.organization != request.user.organization:
            raise serializers.ValidationError(
                "Company does not belong to your organization."
            )
        return company
