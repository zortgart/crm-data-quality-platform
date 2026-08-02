# =============================================================
# common/management/commands/generate_mock_data.py
# =============================================================
# Management command to generate a large dataset for Phase 5
# performance testing (N+1 queries and EXPLAIN).
#
# Usage: python manage.py generate_mock_data --contacts 10000
#
# Java equivalent:
#   A CommandLineRunner or ApplicationRunner bean in Spring Boot
# =============================================================

import random
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from organizations.models import Organization
from companies.models import Company, CompanySize
from contacts.models import Contact
from accounts.models import UserRole
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Generates synthetic data for performance testing (Phase 5)"

    def add_arguments(self, parser):
        parser.add_argument("--contacts", type=int, default=1000, help="Number of contacts to generate")
        parser.add_argument("--companies", type=int, default=50, help="Number of companies to generate")

    def handle(self, *args, **options):
        num_contacts = options["contacts"]
        num_companies = options["companies"]

        self.stdout.write(f"Generating {num_companies} companies and {num_contacts} contacts...")
        start_time = time.time()

        with transaction.atomic():
            # 1. Create Organization
            org, _ = Organization.objects.get_or_create(
                name="Performance Test Org",
                slug="perf-test-org"
            )

            # 2. Create Admin User
            if not User.objects.filter(email="perfadmin@example.com").exists():
                User.objects.create_user(
                    email="perfadmin@example.com",
                    password="StrongPassword123!",
                    role=UserRole.ADMIN,
                    organization=org
                )

            # 3. Create Companies (Bulk)
            companies_to_create = []
            for i in range(num_companies):
                companies_to_create.append(
                    Company(
                        organization=org,
                        name=f"Perf Company {i}",
                        domain=f"perf{i}.com",
                        size=random.choice(CompanySize.choices)[0]
                    )
                )
            
            Company.objects.bulk_create(companies_to_create, ignore_conflicts=True)
            companies = list(Company.objects.filter(organization=org))

            # 4. Create Contacts (Bulk in chunks to avoid memory issues)
            batch_size = 5000
            contacts_to_create = []
            
            for i in range(num_contacts):
                contacts_to_create.append(
                    Contact(
                        organization=org,
                        company=random.choice(companies) if companies else None,
                        first_name="Perf",
                        last_name=f"Contact_{i}",
                        email=f"contact{i}@perf.com",
                        quality_score=random.randint(0, 100)
                    )
                )

                if len(contacts_to_create) >= batch_size:
                    Contact.objects.bulk_create(contacts_to_create)
                    contacts_to_create = []

            # Insert remaining
            if contacts_to_create:
                Contact.objects.bulk_create(contacts_to_create)

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated data in {end_time - start_time:.2f} seconds."
        ))
