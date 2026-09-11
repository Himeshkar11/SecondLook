"""Demo EPFO integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real EPFO verification should target the official
EPFO member / employer service portal only after registration and
authorization requirements are met. Official reference page:
https://unifiedportal-emp.epfindia.gov.in/epfo/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class EPFOIntegration(GovernmentIntegration):
    """Demo EPFO verification integration."""

    name = "EPFO"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
