"""Demo Startup India integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real Startup India verification should be routed to
DPIIT or an official registration/verification service path only after
registration and authorization are in place.
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class StartupIndiaIntegration(GovernmentIntegration):
    """Demo Startup India verification integration."""

    name = "STARTUP_INDIA"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
