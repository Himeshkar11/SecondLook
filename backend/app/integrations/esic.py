"""Demo ESIC integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real ESIC verification should be replaced by the
official ESIC / employer-portal integration path only after required
registration and authorization. Official reference page:
https://www.esic.gov.in/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class ESICIntegration(GovernmentIntegration):
    """Demo ESIC verification integration."""

    name = "ESIC"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
