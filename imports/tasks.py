# =============================================================
# imports/tasks.py
# =============================================================
# Celery tasks for background processing (Phase 8).
#
# Java equivalent:
#   @Async method or a Quartz Job.
# =============================================================

import logging
from celery import shared_task
from .models import ImportJob, ImportStatus
from .processor import process_csv_import

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_csv_import_task(self, job_id: str):
    """
    Celery task that retrieves the job from the DB,
    opens the uploaded file, and processes it.
    """
    try:
        job = ImportJob.objects.get(id=job_id)
    except ImportJob.DoesNotExist:
        logger.error(f"ImportJob {job_id} not found.")
        return

    if not job.file:
        job.status = ImportStatus.FAILED
        job.error_message = "No file attached to this job."
        job.save(update_fields=["status", "error_message"])
        return

    logger.info(f"Starting background processing for job {job_id}")

    try:
        # Pass the file stream to the processor
        import io
        with job.file.open("rb") as f:
            text_stream = io.TextIOWrapper(f, encoding="utf-8")
            process_csv_import(job, text_stream)
    except UnicodeDecodeError:
        job.status = ImportStatus.FAILED
        job.error_message = "File is not valid UTF-8"
        job.save(update_fields=["status", "error_message"])
    except Exception as e:
        logger.exception("Unexpected error opening file")
        job.status = ImportStatus.FAILED
        job.error_message = f"File error: {str(e)}"
        job.save(update_fields=["status", "error_message"])
        
    # Optional: Delete the file after successful processing to save space
    # if job.status == ImportStatus.COMPLETED:
    #     job.file.delete(save=False)
