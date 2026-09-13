"""Government and external verification integration framework.

M11 creates a common integration abstraction for future government and
verification providers. The implementations here are contract-only demo
providers and must not make network calls, handle credentials, or run
real verification workflows.
"""

from app.integrations.base import (
    GovernmentIntegration,
    GovernmentProvider,
    GovernmentSourceStatus,
    GovernmentVerificationResponse,
    IntegrationRequest,
    IntegrationResponse,
    IntegrationStatus,
    ProviderCapabilities,
)
from app.integrations.registry import (
    GovernmentProviderRegistry,
    get_government_provider,
    get_integration,
    get_provider,
    government_provider_registry,
)

__all__ = [
    "GovernmentIntegration",
    "GovernmentProvider",
    "GovernmentSourceStatus",
    "GovernmentVerificationResponse",
    "IntegrationRequest",
    "IntegrationResponse",
    "IntegrationStatus",
    "ProviderCapabilities",
    "GovernmentProviderRegistry",
    "government_provider_registry",
    "get_integration",
    "get_provider",
    "get_government_provider",
]
