"""Common contract for demo government integration providers.

This module defines the common abstraction that all M11 provider
implementations must satisfy. The interface is intentionally small:
    verify(request) -> IntegrationResponse

No real API client, OAuth, authentication, network, AI, OCR, or
credential handling is allowed in this milestone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class IntegrationStatus(str, Enum):
    """Common, provider-neutral statuses for all demo integrations."""

    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    CLEAR = "CLEAR"
    BLACKLISTED = "BLACKLISTED"


@dataclass
class IntegrationRequest:
    """Shared request shape for provider-agnostic verification.

    The request is intentionally minimal and free of provider secrets.
    """

    entity_type: str = "vendor"
    entity_id: str = ""
    provider: str = "PAN"
    document_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationResponse:
    """Shared response shape for provider-agnostic verification outcomes."""

    success: bool = True
    status: str = IntegrationStatus.VERIFIED.value
    provider: str = "PAN"
    reference_id: str = "DEMO-REFERENCE-001"
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = "Demo verification successful"


class GovernmentIntegration:
    """Abstract integration contract every demo provider implements.

    A real provider should extend or replace the demo implementation behind
    the common interface so calling code never depends on provider-specific
    request/response details.
    """

    name: str = "GOVERNMENT_INTEGRATION"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        """Return a provider-neutral response object.

        Implementations may be demo-only in this milestone and must not
        perform real government or external network activity.
        """
        raise NotImplementedError("Demo integration must implement verify(request)")

    def _identifier_from_request(self, request: IntegrationRequest) -> str:
        """Extract a deterministic demo identifier from the request object.

        The identifier is intentionally carried inside the shared request
        payload or the existing entity/document fields.
        """
        payload = request.payload or {}
        identifier = payload.get("identifier") or payload.get("id") or request.entity_id or request.document_id
        if not identifier:
            identifier = ""
        return str(identifier)

    def _response_from_repository_record(self, request: IntegrationRequest, record: dict | None) -> IntegrationResponse:
        """Return a common response object from the repository record.

        Missing records must produce NOT_FOUND only. Database failures must
        be reported as UNAVAILABLE or ERROR using the existing contract.
        """
        provider = (request.provider or self.name).upper().strip()
        if not record:
            return IntegrationResponse(
                success=False,
                status=IntegrationStatus.NOT_FOUND.value,
                provider=provider,
                reference_id="DEMO-REFERENCE-000",
                data={
                    "provider": provider,
                    "identifier": self._identifier_from_request(request),
                    "demo_result": "not_found",
                    "source": "supabase_demo",
                },
                message="Demo record not found in Supabase",
            )

        status = str((record.get("status") or "VERIFIED")).upper()
        source_data = dict(record.get("data") or {})
        name = record.get("name")
        if name:
            source_data.setdefault("name", name)

        response_status = {
            "VALID": IntegrationStatus.VERIFIED.value,
            "ACTIVE": IntegrationStatus.VERIFIED.value,
            "VERIFIED": IntegrationStatus.VERIFIED.value,
            "AVAILABLE": IntegrationStatus.VERIFIED.value,
            "CLEAR": IntegrationStatus.CLEAR.value,
            "BLACKLISTED": IntegrationStatus.BLACKLISTED.value,
            "INVALID": IntegrationStatus.NOT_VERIFIED.value,
            "INACTIVE": IntegrationStatus.NOT_VERIFIED.value,
            "NOT_VERIFIED": IntegrationStatus.NOT_VERIFIED.value,
            "UNAVAILABLE": IntegrationStatus.UNAVAILABLE.value,
            "PENDING": IntegrationStatus.PENDING.value,
            "ERROR": IntegrationStatus.ERROR.value,
        }.get(status, status)

        # Keep the listed boolean in the canonical repository payload shape for
        # the explicit blacklist scenario mapping.
        if "listed" not in source_data and status.upper() == "CLEAR":
            source_data["listed"] = False
        if "listed" not in source_data and status.upper() == "BLACKLISTED":
            source_data["listed"] = True

        return IntegrationResponse(
            success=response_status in {IntegrationStatus.VERIFIED.value, IntegrationStatus.CLEAR.value, IntegrationStatus.BLACKLISTED.value},
            status=response_status,
            provider=provider,
            reference_id=str(record.get("id") or "DEMO-REFERENCE-001"),
            data={
                "provider": provider,
                "identifier": record.get("identifier") or self._identifier_from_request(request),
                "name": record.get("name") or "",
                **source_data,
                "source": "supabase_demo",
                "demo_result": "verified" if response_status in {IntegrationStatus.VERIFIED.value, IntegrationStatus.CLEAR.value, IntegrationStatus.BLACKLISTED.value} else "not_verified",
            },
            message="Demo verification data returned from Supabase",
        )

    def _fetch_from_demo_repo(self, request: IntegrationRequest) -> IntegrationResponse:
        """Query the demo government repository and translate the row into a
        provider-neutral `IntegrationResponse`.
        """
        from app.database.demo_government_repository import (
            DemoGovernmentRepository,
            DemoGovernmentRepositoryUnavailable,
        )

        provider = (request.provider or self.name).upper().strip()
        identifier = self._identifier_from_request(request)
        if not identifier:
            return IntegrationResponse(
                success=False,
                status=IntegrationStatus.NOT_FOUND.value,
                provider=provider,
                reference_id="DEMO-REFERENCE-000",
                data={
                    "provider": provider,
                    "identifier": "",
                    "demo_result": "not_found",
                    "source": "supabase_demo",
                },
                message="No demo identifier supplied",
            )

        repository = DemoGovernmentRepository()
        try:
            record = repository.find_by_provider_and_identifier(provider, identifier)
        except DemoGovernmentRepositoryUnavailable:
            return IntegrationResponse(
                success=False,
                status=IntegrationStatus.UNAVAILABLE.value,
                provider=provider,
                reference_id="DEMO-REFERENCE-000",
                data={
                    "provider": provider,
                    "identifier": identifier,
                    "demo_result": "unavailable",
                    "source": "supabase_demo",
                },
                message="Supabase demo repository unavailable",
            )

        if record is None:
            return IntegrationResponse(
                success=False,
                status=IntegrationStatus.NOT_FOUND.value,
                provider=provider,
                reference_id="DEMO-REFERENCE-000",
                data={
                    "provider": provider,
                    "identifier": identifier,
                    "demo_result": "not_found",
                    "source": "supabase_demo",
                },
                message="Supabase demo record not found",
            )

        return self._response_from_repository_record(request, record)
