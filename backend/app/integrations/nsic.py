"""Demo NSIC integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real NSIC verification should be routed to the
official national small industries portal or applicable public registry
path only after registration and authorization are in place.
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class NSICIntegration(GovernmentIntegration):
    """Demo NSIC verification integration."""

    name = "NSIC"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
