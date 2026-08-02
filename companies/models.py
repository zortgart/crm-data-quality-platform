# =============================================================
# companies/models.py — Company Model
# =============================================================
# A Company is a business entity (e.g. "Acme Corp").
# Every Company belongs to one Organization (tenant).
# Contacts are linked to Companies (where they work).
#
# Java equivalent:
#   @Entity Company with @ManyToOne Organization
# =============================================================

from django.db import models
from common.models import UUIDModel, TimeStampedModel


class CompanySize(models.TextChoices):
    """
    Employee count buckets.
    Stored as string, displayed as label.
    Java equivalent: enum CompanySize { STARTUP, SMB, MID_MARKET, ENTERPRISE }
    """
    STARTUP    = "STARTUP",    "1–10 employees"
    SMALL      = "SMALL",      "11–50 employees"
    SMB        = "SMB",        "51–200 employees"
    MID_MARKET = "MID_MARKET", "201–1000 employees"
    ENTERPRISE = "ENTERPRISE", "1000+ employees"


class Company(UUIDModel, TimeStampedModel):
    """
    A company/account in the CRM.

    Multi-tenancy: every query MUST filter by organization.
    The ViewSet enforces this via get_queryset().

    DB Table: companies_company
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="companies",
        # related_name → org.companies.all()
    )

    name = models.CharField(
        max_length=255,
        help_text="Company legal or trade name."
    )

    domain = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Primary email domain, e.g. 'acme.com'. Used for deduplication."
    )

    industry = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Industry sector, e.g. 'Technology', 'Healthcare'."
    )

    description = models.TextField(
        blank=True, 
        default="", 
        help_text="AI-generated or manual company description."
    )

    website = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Company website URL."
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Main company phone number."
    )

    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    size = models.CharField(
        max_length=20,
        choices=CompanySize.choices,
        blank=True,
        default="",
        help_text="Company size bucket."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Soft delete — inactive companies are hidden from normal queries."
    )

    class Meta:
        db_table = "companies"
        ordering = ["name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        # Unique constraint: company name must be unique within an org
        # (two different orgs CAN have a company named "Acme Corp")
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_company_name_per_org"
            )
        ]

    def __str__(self):
        return self.name
