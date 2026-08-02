# =============================================================
# validation/models.py — DuplicatePair Model
# =============================================================
# Tracks flagged duplicates found by the L1/L2/L3 detector.
#
# Java equivalent:
#   @Entity DuplicatePair with @ManyToOne ContactA/ContactB
# =============================================================

from django.db import models
from common.models import UUIDModel, TimeStampedModel
from django.core.validators import MinValueValidator, MaxValueValidator


class DuplicatePair(UUIDModel, TimeStampedModel):
    """
    Represents a flagged duplicate between two contacts.
    Tenant scoped via contact relationships, but we also store org_id for easier querying.
    """
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="duplicate_pairs"
    )
    
    contact_a = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="duplicate_pairs_as_a"
    )
    
    contact_b = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="duplicate_pairs_as_b"
    )

    confidence = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100 confidence score that these are duplicates."
    )

    detection_level = models.CharField(
        max_length=50,
        help_text="e.g. L1_EXACT_EMAIL, L2_EXACT_PHONE, L3_NAME_COMPANY"
    )

    resolved = models.BooleanField(
        default=False,
        help_text="Has a user manually reviewed and merged/dismissed this pair?"
    )

    class Meta:
        db_table = "duplicate_pairs"
        ordering = ["-confidence"]
        unique_together = ["contact_a", "contact_b"]
        verbose_name = "Duplicate Pair"
        verbose_name_plural = "Duplicate Pairs"
        
    def __str__(self):
        return f"Duplicate: {self.contact_a_id} <-> {self.contact_b_id} ({self.confidence}%)"
