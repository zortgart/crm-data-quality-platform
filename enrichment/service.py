from django.conf import settings
from .providers.base import BaseEnrichmentProvider
from .providers.mock import MockEnrichmentProvider
from .providers.openai import OpenAIEnrichmentProvider

def get_enrichment_provider() -> BaseEnrichmentProvider:
    """
    Factory function to get the configured enrichment provider.
    """
    provider_name = getattr(settings, "ENRICHMENT_PROVIDER", "mock").lower()
    
    if provider_name == "openai":
        return OpenAIEnrichmentProvider()
    
    # Default to mock
    return MockEnrichmentProvider()
