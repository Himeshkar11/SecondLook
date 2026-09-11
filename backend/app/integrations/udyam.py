"""Demo Udyam integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real Udyam integration should be replaced by the
official Udyam/MSME registration verification path under government
credentialing and authorization. Official reference page:
https://udyamregistration.gov.in/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class UdyamIntegration(GovernmentIntegration):
    """Demo Udyam verification integration."""

    name = "UDYAM"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
