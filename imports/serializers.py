# =============================================================
# imports/serializers.py
# =============================================================

from rest_framework import serializers
from .models import ImportJob, ImportRow


class ImportJobSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    
    class Meta:
        model = ImportJob
        fields = [
            "id", "filename", "status", "total_rows", 
            "processed", "failed", "error_message", 
            "created_by_name", "created_at"
        ]
        read_only_fields = [
            "id", "status", "total_rows", "processed", 
            "failed", "error_message", "created_by_name", "created_at"
        ]


class ImportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRow
        fields = ["id", "row_number", "raw_data", "errors", "created_at"]
        read_only_fields = fields
