"""Demo PAN integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real PAN verification should be routed to the
official Income Tax Department / UTIITSL service pathway only after
registration and authorization are in place. Official reference page:
https://www.incometax.gov.in/iec/foportal/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class PANIntegration(GovernmentIntegration):
    """Demo PAN verification integration."""

    name = "PAN"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
