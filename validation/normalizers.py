# =============================================================
# validation/normalizers.py
# =============================================================
# Functions to clean and normalize input data before saving.
#
# Java equivalent:
#   Utility classes (e.g. EmailNormalizerUtil) or Spring Converters.
# =============================================================

import re
import phonenumbers


def normalize_email(email: str) -> str:
    """
    Lowercase, strip whitespace.
    (Could add punycode conversion or plus-address stripping here if needed).
    """
    if not email:
        return ""
    return email.strip().lower()


def normalize_phone(phone: str, default_region: str = "US") -> str:
    """
    Convert to E.164 format using Google's phonenumbers library.
    If parsing fails, returns the stripped original string.
    """
    if not phone:
        return ""
    
    clean_phone = phone.strip()
    try:
        parsed = phonenumbers.parse(clean_phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
        
    return clean_phone


def normalize_company_name(name: str) -> str:
    """
    Lowercase, strip whitespace, remove common legal suffixes for deduplication.
    e.g. "Acme Corp." -> "acme"
    """
    if not name:
        return ""
    
    name = name.strip().lower()
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    
    # Remove common suffixes
    suffixes = [r'\binc\b', r'\bcorp\b', r'\bllc\b', r'\bltd\b', r'\bcompany\b']
    for suffix in suffixes:
        name = re.sub(suffix, '', name)
        
    return name.strip()


def normalize_job_title(title: str) -> str:
    """
    Expand common abbreviations.
    e.g. "Sr. Eng." -> "Senior Engineer"
    """
    if not title:
        return ""
        
    title = title.strip()
    
    # Simple mapping
    mapping = {
        r'\bSr\b\.?': 'Senior',
        r'\bJr\b\.?': 'Junior',
        r'\bEng\b\.?': 'Engineer',
        r'\bDir\b\.?': 'Director',
        r'\bVP\b': 'Vice President',
    }
    
    for pattern, replacement in mapping.items():
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
        
    # Remove extra spaces
    return re.sub(r'\s+', ' ', title).strip()
