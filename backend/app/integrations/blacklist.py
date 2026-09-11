"""Demo Blacklist integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class BlacklistIntegration(GovernmentIntegration):
    """Demo blacklist verification integration."""

    name = "BLACKLIST"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
