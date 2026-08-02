# =============================================================
# contacts/models.py — Contact Model
# =============================================================
# A Contact is a person (lead, prospect, customer) in the CRM.
# Every Contact belongs to one Organization (tenant).
# A Contact optionally works at a Company.
#
# This is the PRIMARY entity of the CRM data quality platform.
# Quality scoring, deduplication, and enrichment all act on Contacts.
#
# Java equivalent:
#   @Entity Contact with @ManyToOne Organization, @ManyToOne Company
# =============================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import UUIDModel, TimeStampedModel


class Contact(UUIDModel, TimeStampedModel):
    """
    A person record in the CRM.

    Key fields for data quality (Phase 6):
      - quality_score: 0–100, computed by the quality pipeline
      - normalized_email: lowercase, stripped (for deduplication)
      - normalized_phone: E.164 format (for deduplication)

    DB Table: contacts_contact
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        # SET_NULL: if company is deleted, contact stays but company link is removed
        null=True,
        blank=True,
        related_name="contacts",
        # related_name → company.contacts.all()
    )

    # ── Personal Info ──────────────────────────────────────────
    first_name = models.CharField(max_length=100, default="")
    last_name  = models.CharField(max_length=100, default="")

    email = models.EmailField(
        max_length=254,
        blank=True,
        default="",
        help_text="Primary email address."
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Phone number (any format — normalized in Phase 6)."
    )

    job_title = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Job title (normalized in Phase 6: Sr.→Senior, Eng.→Engineer)."
    )

    city    = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    # ── Data Quality Fields (populated in Phase 6) ─────────────
    quality_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0–100 quality score. Higher = more complete and verified."
    )

    normalized_email = models.CharField(
        max_length=254,
        blank=True,
        default="",
        db_index=True,
        help_text="Lowercased, stripped email. Used for deduplication in Phase 6."
    )

    normalized_phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="E.164 format phone. Used for deduplication in Phase 6."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Soft delete — inactive contacts excluded from normal queries."
    )

    class Meta:
        db_table = "contacts"
        ordering = ["last_name", "first_name"]
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [
            # Multi-column index: most queries filter by org first, then order by name
            models.Index(fields=["organization", "last_name", "first_name"],
                         name="idx_contacts_org_name"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
