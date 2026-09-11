import pytest

from app.config.settings import settings
from app.database.demo_government_repository import DemoGovernmentRepository
from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse, IntegrationStatus
from app.integrations.registry import get_integration, registry
from app.integrations.pan import PANIntegration
from app.integrations.gst import GSTIntegration
from app.integrations.udyam import UdyamIntegration
from app.integrations.mca import MCAIntegration
from app.integrations.epfo import EPFOIntegration
from app.integrations.esic import ESICIntegration
from app.integrations.startup_india import StartupIndiaIntegration
from app.integrations.nsic import NSICIntegration
from app.integrations.digilocker import DigiLockerIntegration
from app.integrations.blacklist import BlacklistIntegration
from app.integrations.oem import OEMIntegration


@pytest.mark.parametrize(
    "cls,provider_name",
    [
        (PANIntegration, "PAN"),
        (GSTIntegration, "GST"),
        (UdyamIntegration, "UDYAM"),
        (MCAIntegration, "MCA"),
        (EPFOIntegration, "EPFO"),
        (ESICIntegration, "ESIC"),
        (StartupIndiaIntegration, "STARTUP_INDIA"),
        (NSICIntegration, "NSIC"),
        (DigiLockerIntegration, "DIGILOCKER"),
        (BlacklistIntegration, "BLACKLIST"),
        (OEMIntegration, "OEM"),
    ],
)
def test_all_11_required_demo_integrations_exist_and_satisfy_contract(cls, provider_name):
    integration = cls()
    assert isinstance(integration, GovernmentIntegration)

    request = IntegrationRequest(entity_type="bidder", entity_id="demo-bidder-1", document_id="doc-1", provider=provider_name)
    response = integration.verify(request)

    assert isinstance(response, IntegrationResponse)
    assert response.provider == provider_name
    assert response.status in {status.value for status in IntegrationStatus}
    assert response.data["provider"] == provider_name
    assert response.data["source"] == "supabase_demo"
    assert response.reference_id.startswith("DEMO-")


def test_registry_resolves_all_required_m11_provider_tokens():
    for provider in [
        "PAN",
        "GST",
        "UDYAM",
        "MCA",
        "EPFO",
        "ESIC",
        "STARTUP_INDIA",
        "NSIC",
        "DIGILOCKER",
        "BLACKLIST",
        "OEM",
    ]:
        integration = get_integration(provider)
        assert isinstance(integration, GovernmentIntegration)
        assert integration.name == provider


def test_unknown_provider_registration_fails_cleanly():
    with pytest.raises(KeyError, match="Unknown provider 'ABC'"):
        registry.get("ABC")


def test_unknown_identifier_is_not_mapped_to_a_hardcoded_provider_success():
    integration = PANIntegration()
    request = IntegrationRequest(
        entity_type="bidder",
        entity_id="missing-bidder-1",
        document_id="missing-document-1",
        provider="PAN",
        payload={"identifier": "NO_SUCH_SUPABASE_IDENTIFIER_000000"},
    )
    response = integration.verify(request)

    assert isinstance(response, IntegrationResponse)
    assert response.success is False
    assert response.status == IntegrationStatus.NOT_FOUND.value
    assert response.provider == "PAN"
    assert response.data["source"] == "supabase_demo"
    assert response.data["demo_result"] == "not_found"


def test_repository_known_record_maps_to_provider_response_from_supabase():
    if not settings.database_url:
        pytest.skip("configured Supabase/PostgreSQL DATABASE_URL is not available")

    repository = DemoGovernmentRepository()
    record = repository.find_by_provider_and_identifier("PAN", "ABCDE1234F")

    assert record is not None
    assert record["provider"] == "PAN"
    assert record["identifier"] == "ABCDE1234F"
    assert record["status"] == "VERIFIED"
    assert record["name"]

    integration = PANIntegration()
    request = IntegrationRequest(
        entity_type="bidder",
        entity_id="known-bidder-1",
        document_id="known-doc-1",
        provider="PAN",
        payload={"identifier": "ABCDE1234F"},
    )
    response = integration.verify(request)

    assert response.success is True
    assert response.status == IntegrationStatus.VERIFIED.value
    assert response.provider == "PAN"
    assert response.data["provider"] == "PAN"
    assert response.data["source"] == "supabase_demo"


def test_blacklist_demo_records_map_to_clear_blacklisted_and_not_found_from_supabase():
    integration = BlacklistIntegration()

    clear_req = IntegrationRequest(
        entity_type="bidder",
        entity_id="clear-bidder-1",
        document_id="clear-doc-1",
        provider="BLACKLIST",
        payload={"identifier": "DEMO-CLEAR-001"},
    )
    clear_resp = integration.verify(clear_req)
    assert clear_resp.status == IntegrationStatus.CLEAR.value
    assert clear_resp.data["listed"] is False
    assert clear_resp.data["source"] == "supabase_demo"

    blacklisted_req = IntegrationRequest(
        entity_type="bidder",
        entity_id="blacklisted-bidder-1",
        document_id="blacklisted-doc-1",
        provider="BLACKLIST",
        payload={"identifier": "DEMO-BLACKLISTED-001"},
    )
    blacklisted_resp = integration.verify(blacklisted_req)
    assert blacklisted_resp.status == IntegrationStatus.BLACKLISTED.value
    assert blacklisted_resp.data["listed"] is True
    assert blacklisted_resp.data["source"] == "supabase_demo"

    unknown_req = IntegrationRequest(
        entity_type="bidder",
        entity_id="unknown-bidder-1",
        document_id="unknown-doc-1",
        provider="BLACKLIST",
        payload={"identifier": "DEMO-UNKNOWN-999"},
    )
    unknown_resp = integration.verify(unknown_req)
    assert unknown_resp.status == IntegrationStatus.NOT_FOUND.value
    assert unknown_resp.data["source"] == "supabase_demo"
    assert unknown_resp.data["demo_result"] == "not_found"


def test_verification_service_uses_registry_without_provider_specific_logic():
    from app.services.verification_service import VerificationService

    service = VerificationService()
    demo = service.start_verification(
        bidder_id="00000000-0000-0000-0000-000000000001",
        document_id="00000000-0000-0000-0000-000000000002",
        verification_type="vendor-gst",
        provider="PAN",
    )

    assert demo["provider"] == "PAN"
    assert demo["verification_type"] == "vendor-gst"
    assert demo["result"]["checks"][0]["provider"] == "PAN"
    assert demo["result"]["checks"][0]["status"] == "VERIFIED"

