# =============================================================
# imports/views.py
# =============================================================
# We use a custom ViewSet here to handle file uploads in the POST method.
#
# Java equivalent:
#   @RestController with @PostMapping consuming MULTIPART_FORM_DATA
# =============================================================

import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from accounts.permissions import IsManagerOrAbove, IsAnalystOrAbove
from .models import ImportJob, ImportRow
from .serializers import ImportJobSerializer, ImportRowSerializer
from .tasks import process_csv_import_task


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve Import Jobs.
    POST /api/v1/imports/ handles the actual file upload.
    """
    serializer_class = ImportJobSerializer
    # Allow Managers to upload, Analysts can only view
    permission_classes = [IsAnalystOrAbove]
    
    def get_queryset(self):
        return ImportJob.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")

    def get_permissions(self):
        if self.action == "create":
            return [IsManagerOrAbove()]
        return super().get_permissions()

    # Override create to handle multipart file upload
    def create(self, request, *args, **kwargs):
        """
        Accepts a CSV file upload, creates a PENDING ImportJob,
        and starts the streaming processor.
        """
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        csv_file = request.FILES["file"]
        
        if not csv_file.name.endswith('.csv'):
            return Response({"error": "File must be a CSV"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Create Job Tracker and attach file
        job = ImportJob.objects.create(
            organization=request.user.organization,
            created_by=request.user,
            filename=csv_file.name,
            file=csv_file
        )
        
        # 2. Dispatch background task to Celery
        # .delay() is shorthand for .apply_async()
        process_csv_import_task.delay(str(job.id))
            
        # Return 201 immediately while processing happens in background
        job.refresh_from_db()
        serializer = self.get_serializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def errors(self, request, pk=None):
        """
        GET /api/v1/imports/{id}/errors/
        Returns row-level errors for this job.
        """
        job = self.get_object()
        errors = ImportRow.objects.filter(job=job).order_by("row_number")
        
        # We manually paginate here using DRF's built-in methods
        page = self.paginate_queryset(errors)
        if page is not None:
            serializer = ImportRowSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = ImportRowSerializer(errors, many=True)
        return Response(serializer.data)
