# =============================================================
# common/management/commands/explain_queries.py
# =============================================================
# Demonstrates Django ORM's EXPLAIN ANALYZE (Phase 5)
# Run after generate_mock_data to see index utilization.
#
# Usage: python manage.py explain_queries
# =============================================================

from django.core.management.base import BaseCommand
from contacts.models import Contact
from organizations.models import Organization


class Command(BaseCommand):
    help = "Runs EXPLAIN ANALYZE on typical ORM queries"

    def handle(self, *args, **options):
        org = Organization.objects.filter(slug="perf-test-org").first()
        if not org:
            self.stdout.write(self.style.ERROR("Organization not found. Run generate_mock_data first."))
            return

        self.stdout.write(self.style.WARNING("\n=== Query 1: Filter by Organization (Indexed) ==="))
        # We use .explain(analyze=True) to ask PostgreSQL for the execution plan
        qs1 = Contact.objects.filter(organization=org)
        self.stdout.write(qs1.explain(analyze=True))

        self.stdout.write(self.style.WARNING("\n=== Query 2: Filter by Quality Score (Indexed in Phase 5) ==="))
        qs2 = Contact.objects.filter(quality_score__gte=90)
        self.stdout.write(qs2.explain(analyze=True))

        self.stdout.write(self.style.WARNING("\n=== Query 3: Multi-Column Sort (Indexed in Phase 5) ==="))
        qs3 = Contact.objects.filter(organization=org).order_by("last_name", "first_name")
        self.stdout.write(qs3.explain(analyze=True))

        self.stdout.write(self.style.SUCCESS("\nEXPLAIN demonstration complete."))
