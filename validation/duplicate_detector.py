# =============================================================
# validation/duplicate_detector.py
# =============================================================
# Detects duplicates for a given contact and flags them in the DB.
# Levels:
#   L1: Exact normalized email (100% confidence)
#   L2: Exact normalized phone (80% confidence)
#   L3: Name + Company (60% confidence)
#
# Java equivalent:
#   A Service bean that queries the repository to find matches
#   and creates DuplicatePair entities.
# =============================================================

from .models import DuplicatePair
from contacts.models import Contact
from django.db.models import Q


def detect_duplicates(contact: Contact):
    """
    Finds duplicates for the given contact within the same organization.
    Creates or updates DuplicatePair records.
    """
    if not contact.id:
        return  # Must be saved first
        
    pairs_to_create = []
    
    # ── L1: Email Match ─────────────────────────────────────────
    if contact.normalized_email:
        l1_matches = Contact.objects.filter(
            organization=contact.organization,
            normalized_email=contact.normalized_email
        ).exclude(id=contact.id)
        
        for match in l1_matches:
            pairs_to_create.append(
                _create_pair_instance(contact, match, 100, "L1_EXACT_EMAIL")
            )
            
    # ── L2: Phone Match ─────────────────────────────────────────
    if contact.normalized_phone:
        l2_matches = Contact.objects.filter(
            organization=contact.organization,
            normalized_phone=contact.normalized_phone
        ).exclude(id=contact.id)
        
        for match in l2_matches:
            # Avoid re-adding if they already matched on email
            if not any(p.contact_b_id == match.id or p.contact_a_id == match.id for p in pairs_to_create):
                pairs_to_create.append(
                    _create_pair_instance(contact, match, 80, "L2_EXACT_PHONE")
                )
                
    # ── L3: Name + Company Match ────────────────────────────────
    if contact.first_name and contact.last_name and contact.company_id:
        l3_matches = Contact.objects.filter(
            organization=contact.organization,
            first_name__iexact=contact.first_name,
            last_name__iexact=contact.last_name,
            company_id=contact.company_id
        ).exclude(id=contact.id)
        
        for match in l3_matches:
            if not any(p.contact_b_id == match.id or p.contact_a_id == match.id for p in pairs_to_create):
                pairs_to_create.append(
                    _create_pair_instance(contact, match, 60, "L3_NAME_COMPANY")
                )
                
    # Bulk insert pairs using ignore_conflicts=True
    # (Because unique_together = ["contact_a", "contact_b"])
    if pairs_to_create:
        DuplicatePair.objects.bulk_create(pairs_to_create, ignore_conflicts=True)


def _create_pair_instance(c1, c2, confidence, level):
    """Helper to ensure A < B to prevent (A,B) and (B,A) duplicates."""
    # Always put the smaller UUID first
    if str(c1.id) < str(c2.id):
        a, b = c1, c2
    else:
        a, b = c2, c1
        
    return DuplicatePair(
        organization=c1.organization,
        contact_a=a,
        contact_b=b,
        confidence=confidence,
        detection_level=level
    )
