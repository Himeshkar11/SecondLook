"""Demo DigiLocker integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real DigiLocker verification should be replaced
by an official DigiLocker service/API integration path that requires
registration and authorization. Official reference page:
https://www.digilocker.gov.in/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class DigiLockerIntegration(GovernmentIntegration):
    """Demo DigiLocker verification integration."""

    name = "DIGILOCKER"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)
