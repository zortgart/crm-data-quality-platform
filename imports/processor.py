# =============================================================
# imports/processor.py
# =============================================================
# Processes CSV uploads efficiently using generators and chunking.
# This prevents OOM errors when processing 1M+ rows.
#
# Java equivalent:
#   Spring Batch ItemReader / ItemProcessor / ItemWriter chunks.
# =============================================================

import csv
import io
import logging
from django.db import transaction
from contacts.models import Contact
from contacts.serializers import ContactDetailSerializer
from validation.duplicate_detector import detect_duplicates
from validation.normalizers import normalize_email, normalize_phone, normalize_job_title
from validation.quality_scorer import calculate_quality_score
from .models import ImportJob, ImportStatus, ImportRow

logger = logging.getLogger(__name__)


def process_csv_import(job: ImportJob, file_stream):
    """
    Reads a CSV file via a text stream, processing it in chunks.
    This runs synchronously for now (Phase 7), but is designed
    to be easily moved to Celery in Phase 8.
    """
    job.status = ImportStatus.PROCESSING
    job.save(update_fields=["status"])
    
    # We expect file_stream to be an open text file or io.StringIO
    try:
        reader = csv.DictReader(file_stream)
        
        # Verify required headers (naive check)
        required_headers = {"first_name", "last_name", "email"}
        if not required_headers.issubset(set(reader.fieldnames or [])):
            job.status = ImportStatus.FAILED
            job.error_message = f"Missing required headers: {required_headers}"
            job.save(update_fields=["status", "error_message"])
            return

        batch_size = 500  # Number of rows per transaction chunk
        chunk = []
        row_number = 1 # 1-indexed, starting after header
        
        for row in reader:
            row_number += 1
            chunk.append((row_number, row))
            
            if len(chunk) >= batch_size:
                _process_chunk(job, chunk)
                chunk = []
                
        # Process remaining
        if chunk:
            _process_chunk(job, chunk)
            
        job.status = ImportStatus.COMPLETED
        job.save(update_fields=["status"])
        
    except Exception as e:
        logger.exception("Import failed catastrophically")
        job.status = ImportStatus.FAILED
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])


def _process_chunk(job: ImportJob, chunk: list):
    """
    Processes a batch of rows inside a single DB transaction.
    """
    valid_contacts = []
    error_rows = []
    
    # Create a mock request context for the serializer
    # This is needed because ContactDetailSerializer expects request.user.organization
    class MockRequest:
        class MockUser:
            organization = job.organization
        user = MockUser()
        
    context = {"request": MockRequest()}
    
    for row_number, row_data in chunk:
        # Use our existing serializer for validation! Reusability!
        # Note: company name -> ID mapping would go here, skipping for simplicity
        serializer = ContactDetailSerializer(data=row_data, context=context)
        
        if serializer.is_valid():
            # Create instance, run Phase 6 pipeline manually
            # Since we are bulk inserting, we don't call serializer.save() which saves 1-by-1
            contact = Contact(**serializer.validated_data)
            contact.organization = job.organization
            
            # Phase 6 normalizers
            contact.normalized_email = normalize_email(contact.email)
            contact.normalized_phone = normalize_phone(contact.phone)
            contact.job_title = normalize_job_title(contact.job_title)
            contact.quality_score = calculate_quality_score(contact)
            
            valid_contacts.append(contact)
        else:
            # Log field errors to ImportRow
            error_rows.append(
                ImportRow(
                    job=job,
                    row_number=row_number,
                    raw_data=row_data,
                    errors=serializer.errors
                )
            )
            
    # Write to DB atomically
    with transaction.atomic():
        if valid_contacts:
            # Insert valid contacts efficiently, ignoring constraint violations (Phase 6 upsert concept)
            Contact.objects.bulk_create(valid_contacts, ignore_conflicts=True)
            
        if error_rows:
            ImportRow.objects.bulk_create(error_rows)
            
        # Update job progress
        job.processed += len(valid_contacts)
        job.failed += len(error_rows)
        job.total_rows = job.processed + job.failed
        job.save(update_fields=["processed", "failed", "total_rows"])
        
    # NOTE: To run duplicate detection accurately on bulk imports, 
    # we would normally need to fetch the inserted IDs and run `detect_duplicates`.
    # For Phase 7, we skip running L1/L2/L3 in bulk to keep it simple, 
    # relying on the database unique constraints or periodic cron jobs.
