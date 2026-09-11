"""Demo GST integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real GST integration should use the official GSTN
portal/API path subject to government registration and authorization.
Official reference page: https://www.gst.gov.in/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class GSTIntegration(GovernmentIntegration):
    """Demo GST verification integration."""

    name = "GST"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
