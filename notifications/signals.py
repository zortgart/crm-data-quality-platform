from django.db.models.signals import post_save
from django.dispatch import receiver
from imports.models import ImportJob, ImportStatus
from .models import Notification

@receiver(post_save, sender=ImportJob)
def notify_import_job_completion(sender, instance, created, **kwargs):
    # Only notify if the job is finished (COMPLETED or FAILED) and not just created
    if not created and instance.status in [ImportStatus.COMPLETED, ImportStatus.FAILED]:
        message = f"Your CSV import '{instance.filename}' has {instance.status.lower()}."
        if instance.status == ImportStatus.COMPLETED:
            message += f" ({instance.processed} contacts processed successfully)"
        elif instance.status == ImportStatus.FAILED:
            message += f" ({instance.failed} errors encountered)"
            
        Notification.objects.get_or_create(
            user=instance.created_by,
            message=message
        )
