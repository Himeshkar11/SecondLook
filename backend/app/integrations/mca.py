"""Demo MCA integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real MCA company verification should be replaced
with an official MCA portal / data API integration requiring government
registration and authorization. Official reference page:
https://www.mca.gov.in/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class MCAIntegration(GovernmentIntegration):
    """Demo MCA verification integration."""

    name = "MCA"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
