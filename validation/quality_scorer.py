# =============================================================
# validation/quality_scorer.py
# =============================================================
# Calculates a 0-100 quality score for a contact.
#
# Java equivalent:
#   A Strategy pattern or a chain of Evaluator classes.
# =============================================================

import re


def calculate_quality_score(contact) -> int:
    """
    Evaluates a contact instance and returns a score from 0-100.
    
    Weights (total 100):
    - Valid email: +30
    - Valid phone (E.164): +20
    - Has Company: +20
    - Has First & Last Name: +20
    - Has Job Title: +10
    """
    score = 0
    
    # 1. Email (30 pts)
    # Simple regex for valid shape, assuming normalization already happened
    if contact.normalized_email and re.match(r"[^@]+@[^@]+\.[^@]+", contact.normalized_email):
        score += 30
        
    # 2. Phone (20 pts)
    # We assume if it starts with '+' and has digits, it was successfully E.164 normalized
    if contact.normalized_phone and contact.normalized_phone.startswith('+'):
        score += 20
        
    # 3. Company (20 pts)
    if contact.company_id is not None:
        score += 20
        
    # 4. Name (20 pts)
    if contact.first_name and contact.last_name:
        score += 20
    elif contact.first_name or contact.last_name:
        score += 10
        
    # 5. Job Title (10 pts)
    if contact.job_title:
        score += 10
        
    # Ensure bounds
    return max(0, min(100, score))
