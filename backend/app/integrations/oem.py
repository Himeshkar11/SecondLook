"""Demo OEM integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real OEM verification should be routed to the
applicable original equipment manufacturer or public procurement
registry path only after registration and authorization are in place.
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class OEMIntegration(GovernmentIntegration):
    """Demo OEM verification integration."""

    name = "OEM"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
