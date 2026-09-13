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


# ---------------------------------------------------------------------------
# Task 10: Statutory Government Verification Providers
# ---------------------------------------------------------------------------
from typing import Any, Dict, Optional
import httpx
from app.config.settings import settings
from app.integrations.base import (
    GovernmentProvider,
    GovernmentSourceStatus,
    GovernmentVerificationResponse,
)


class DemoGSTProvider(GovernmentProvider):
    """Deterministic, fictional demo provider for GST verification.

    Works entirely offline without external credentials.
    """

    source = "GST"

    # Fictional GST records strictly for testing/demo per Task 10 specification
    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "29ABCDE1234F1Z5": {
            "gstin": "29ABCDE1234F1Z5",
            "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "trade_name": "ABC TECHNOLOGIES",
            "registration_date": "2024-04-12",
            "status": "ACTIVE",
            "state": "Tamil Nadu",
        },
    }

    # Deterministic NOT_FOUND identifier
    NOT_FOUND_IDENTIFIER = "29NOTFOUND1234F1"

    # Deterministic simulated error / unavailable identifiers
    UNAVAILABLE_IDENTIFIER = "29ERROR1234F1Z5"

    def verify(self, identifier: str, data: Optional[Dict[str, Any]] = None) -> GovernmentVerificationResponse:
        clean_id = (identifier or "").strip().upper()

        if clean_id == self.UNAVAILABLE_IDENTIFIER or clean_id.startswith("29UNAVAIL"):
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.UNAVAILABLE.value,
                identifier=clean_id,
                message="GST verification service is temporarily unavailable.",
            )

        if clean_id.startswith("29ERROR"):
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="GST verification provider returned an error.",
            )

        if clean_id in self.DEMO_RECORDS:
            record_data = dict(self.DEMO_RECORDS[clean_id])
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=record_data,
                message="GST details found in demo government source.",
            )

        # Default for any other valid or not-found identifier
        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No GST record found for GSTIN {clean_id}.",
        )


class GSTProvider(GovernmentProvider):
    """Integration-ready statutory GST provider.

    Delegates to configured official API if credentials are provided,
    or cleanly falls back to DemoGSTProvider if in demo mode or unconfigured.
    """

    source = "GST"

    def __init__(self, demo_provider: Optional[DemoGSTProvider] = None) -> None:
        self.demo_provider = demo_provider or DemoGSTProvider()

    def verify(self, identifier: str, data: Optional[Dict[str, Any]] = None) -> GovernmentVerificationResponse:
        provider_mode = (settings.gst_provider or "demo").lower().strip()
        api_url = settings.gst_api_url.strip()
        api_key = settings.gst_api_key.strip()

        # If configured for demo or if real endpoint is unconfigured, use DemoGSTProvider
        if provider_mode == "demo" or not api_url:
            return self.demo_provider.verify(identifier, data)

        # Integration-ready adapter for real API
        clean_id = (identifier or "").strip().upper()
        try:
            with httpx.Client(timeout=15.0) as client:
                headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
                resp = client.get(f"{api_url.rstrip('/')}/gstin/{clean_id}", headers=headers)
                if resp.status_code == 200:
                    payload = resp.json()
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.FOUND.value,
                        identifier=clean_id,
                        data=payload.get("data", payload),
                        raw_response={"status_code": resp.status_code},
                    )
                elif resp.status_code == 404:
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.NOT_FOUND.value,
                        identifier=clean_id,
                    )
                else:
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.ERROR.value,
                        identifier=clean_id,
                        message=f"Official GST API returned HTTP {resp.status_code}",
                    )
        except httpx.RequestError as exc:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.UNAVAILABLE.value,
                identifier=clean_id,
                message=f"Official GST API unavailable: {exc}",
            )

