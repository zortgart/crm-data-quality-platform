# =============================================================
# companies/serializers.py
# =============================================================
# Two serializers:
#   CompanyListSerializer  → lightweight, for list view (fewer fields)
#   CompanyDetailSerializer → full fields, for create/retrieve/update
#
# WHY two serializers for one model?
#   List view returns 20+ records → minimize payload → fewer fields
#   Detail view returns 1 record → return everything
#
# Java equivalent:
#   CompanySummaryDTO (list view)
#   CompanyDetailDTO  (full view)
# =============================================================

from rest_framework import serializers
from .models import Company


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""

    class Meta:
        model = Company
        fields = ["id", "name", "domain", "industry", "size", "city", "country", "is_active"]
        read_only_fields = ["id"]


class CompanyDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for create / retrieve / update.

    NOTE: organization is NOT included in input fields.
    It is ALWAYS set from request.user.organization in perform_create().
    Clients CANNOT set the organization themselves.
    """
    # Show organization name (read-only) in response, not just the UUID
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = Company
        fields = [
            "id",
            "organization_name",
            "name",
            "domain",
            "industry",
            "description",
            "website",
            "phone",
            "city",
            "country",
            "size",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_name", "created_at", "updated_at"]
