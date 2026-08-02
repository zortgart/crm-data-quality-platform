from typing import Dict, Any, Optional
import time
from .base import BaseEnrichmentProvider

class MockEnrichmentProvider(BaseEnrichmentProvider):
    """
    A mock provider for testing and local development.
    Simulates network latency and returns dummy data.
    """
    def enrich_company(self, name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        time.sleep(0.5) # Simulate latency
        return {
            "industry": "Technology",
            "size": "ENTERPRISE",
            "description": f"{name} is a leading technology company delivering innovative solutions."
        }

    def enrich_contact(self, first_name: str, last_name: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        time.sleep(0.5)
        return {
            "job_title": "Senior Software Engineer",
            "linkedin_url": f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}"
        }
