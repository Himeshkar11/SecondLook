"""Government and external verification integration framework.

M11 creates a common integration abstraction for future government and
verification providers. The implementations here are contract-only demo
providers and must not make network calls, handle credentials, or run
real verification workflows.
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse, IntegrationStatus
from app.integrations.registry import get_integration

__all__ = [
    "GovernmentIntegration",
    "IntegrationRequest",
    "IntegrationResponse",
    "IntegrationStatus",
    "get_integration",
]
