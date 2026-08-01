# =============================================================
# common/models.py — Shared Abstract Base Models
# =============================================================
# These are ABSTRACT models — they never create their own tables.
# They exist purely to be inherited by other models.
#
# WHY abstract models?
#   DRY principle — Don't Repeat Yourself.
#   Every real model needs: id, created_at, updated_at.
#   Define once here, inherit everywhere.
#
# Java equivalent:
#   @MappedSuperclass — a base JPA class that's never an entity itself
#   but shares fields with child entities.
#
# Usage:
#   class Contact(UUIDModel, TimeStampedModel):
#       ...
#   → Contact table gets: id (UUID), created_at, updated_at + its own fields
# =============================================================

import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base class that adds created_at and updated_at to any model.

    auto_now_add=True → set ONCE when record is created, never changes
    auto_now=True     → updated EVERY time the record is saved

    Java equivalent:
        @CreatedDate    (Spring Data Auditing)
        @LastModifiedDate
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # abstract = True is the KEY line.
        # Without it, Django would try to create a real DB table for this model.
        # With it, this model only exists to be inherited — no table created.
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base class that replaces the default integer PK with UUID.

    WHY UUID over integer auto-increment?
    ✅ IDs are not guessable (security — IDOR attacks harder)
    ✅ IDs can be generated before DB insert (useful for distributed systems)
    ✅ IDs are globally unique across all tables
    ❌ Slightly larger storage (16 bytes vs 4/8 bytes)
    ❌ Index performance slightly worse (non-sequential by default)

    Java equivalent:
        @Id
        @GeneratedValue(generator = "UUID")
        @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
        private UUID id;
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,   # generates a new UUID automatically
        editable=False,        # never shown/changed in admin or forms
    )

    class Meta:
        abstract = True
