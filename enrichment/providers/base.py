from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseEnrichmentProvider(ABC):
    """
    Abstract Base Class for AI/Data Enrichment Providers.
    Follows the Strategy Pattern.
    """

    @abstractmethod
    def enrich_company(self, name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Takes a company name and optional domain, returns enriched data.
        Returns a dict containing fields like 'industry', 'size', 'description'.
        """
        pass

    @abstractmethod
    def enrich_contact(self, first_name: str, last_name: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Takes contact details, returns enriched data.
        Returns a dict containing fields like 'job_title', 'linkedin_url'.
        """
        pass
