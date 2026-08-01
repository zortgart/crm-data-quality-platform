# =============================================================
# organizations/models.py — Organization Model (Tenant Root)
# =============================================================
# Organization is the TOP of our data hierarchy.
# EVERY other model belongs to an Organization.
#
# This is our multi-tenancy strategy:
#   - One database, one schema (shared schema)
#   - Every table has organization_id column
#   - Every query filters by organization_id
#   - Organization A NEVER sees Organization B's data
#
# Real-world examples:
#   Salesforce has "orgs" (organizations/tenants)
#   HubSpot has "portals"
#   Slack has "workspaces"
#   We call them "Organizations"
#
# Java equivalent:
#   @Entity with @TenantId — Hibernate multi-tenancy
#   Or a TenantAwareEntity base class
# =============================================================

from django.db import models
from common.models import UUIDModel, TimeStampedModel


class Organization(UUIDModel, TimeStampedModel):
    """
    The tenant root entity.

    Every Company, Contact, User, ImportJob belongs to one Organization.
    Organizations are completely isolated from each other.

    DB Table: organizations_organization
    """

    name = models.CharField(
        max_length=255,
        help_text="Full organization name, e.g. 'Acme Corporation'"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier, e.g. 'acme-corporation'. Must be unique."
        # UNIQUE constraint → PostgreSQL creates a unique index automatically
        # Attempting to insert duplicate slug → IntegrityError (caught at service layer)
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive organizations cannot log in or access data."
    )

    class Meta:
        db_table = "organizations"
        # db_table: override Django's default table name.
        # Default would be: organizations_organization
        # We prefer clean name: organizations

        ordering = ["name"]
        # Default ordering when querying Organization.objects.all()
        # Java equivalent: @OrderBy("name ASC") on @Entity

        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        # What shows in Django admin and shell
        # Java equivalent: toString()
        return self.name
