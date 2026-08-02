# =============================================================
# imports/models.py — Import tracking models
# =============================================================
# Tracks the progress of bulk CSV imports and logs row-level errors.
#
# Java equivalent:
#   Spring Batch JobExecution / StepExecution tables
# =============================================================

from django.db import models
from common.models import UUIDModel, TimeStampedModel


class ImportStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class ImportJob(UUIDModel, TimeStampedModel):
    """
    High-level tracker for a CSV upload.
    Tenant scoped via organization_id.
    """
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="import_jobs"
    )
    
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="import_jobs"
    )

    filename = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, 
        choices=ImportStatus.choices, 
        default=ImportStatus.PENDING
    )
    
    # Progress tracking
    total_rows = models.IntegerField(default=0)
    processed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    
    # Error message if the entire job failed (e.g., file not found, bad headers)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "import_jobs"
        ordering = ["-created_at"]
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"
        indexes = [
            # Phase 5 planned index: filtering/polling by status
            models.Index(fields=["status", "created_at"], name="idx_import_jobs_status"),
        ]

    def __str__(self):
        return f"{self.filename} ({self.status})"


class ImportRow(models.Model):
    """
    Tracks validation errors for individual rows within a job.
    We don't use UUIDs here to save space, standard auto-incrementing big int is fine.
    """
    job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="errors"
    )
    
    row_number = models.IntegerField()
    raw_data = models.JSONField(
        help_text="The original row data that failed validation"
    )
    errors = models.JSONField(
        help_text="Dictionary of field-level errors"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "import_rows"
        ordering = ["row_number"]
        verbose_name = "Import Row Error"
        verbose_name_plural = "Import Row Errors"

    def __str__(self):
        return f"Job {self.job_id} Row {self.row_number} Error"
