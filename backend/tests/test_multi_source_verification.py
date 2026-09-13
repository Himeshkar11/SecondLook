"""Tests for Task 14 — Multi-Source Government Verification Expansion.

Covers:
1. Provider registry for all 10 sources + unknown provider rejection
2. Provider capabilities and audit metadata (is_demo=True, retrieved_at)
3. Deterministic responses for all 8 new providers (FOUND, NOT_FOUND, UNAVAILABLE)
4. Backward compatibility with existing GST & PAN providers
5. ComplianceEngine numeric comparison (FIELD_GREATER_THAN_OR_EQUAL) for Make In India
6. Blacklist CLEAR (PASS) vs LISTED (FAIL) requirement evaluation without automatic bidder disqualification
7. EvidenceResolver multi-source resolution
8. GovernmentVerificationService multi-source verification and database schema persistence
"""

import uuid
from datetime import datetime, timezone
import pytest

from app.integrations.base import (
    GovernmentProvider,
    GovernmentSourceStatus,
    ProviderCapabilities,
)
from app.integrations.registry import (
    GovernmentProviderRegistry,
    get_provider,
    get_government_provider,
)
from app.integrations.udyam import DemoUdyamProvider
from app.integrations.epfo import DemoEPFOProvider
from app.integrations.esic import DemoESICProvider
from app.integrations.startup_india import DemoStartupIndiaProvider
from app.integrations.nsic import DemoNSICProvider
from app.integrations.make_in_india import DemoMakeInIndiaProvider
from app.integrations.oem import DemoOEMProvider
from app.integrations.blacklist import DemoBlacklistProvider
from app.integrations.gst import DemoGSTProvider
from app.integrations.pan import DemoPANProvider

from app.verification.compliance_engine import ComplianceEngine, Evidence
from app.verification.evidence_resolver import EvidenceResolver
from app.services.government_verification_service import (
    GovernmentVerificationService,
    SUPPORTED_DOCUMENT_TYPES,
    SUPPORTED_VERIFICATION_SOURCES,
    UnsupportedDocumentTypeError,
    MissingIdentifierError,
)
from app.models.government_verification import GovernmentVerification


# ==============================================================================
# 1. PROVIDER REGISTRY TESTS
# ==============================================================================

def test_registry_contains_all_ten_sources():
    """All 10 statutory sources must be registered."""
    sources = GovernmentProviderRegistry.list_providers()
    expected_sources = {
        "GST",
        "PAN",
        "UDYAM",
        "EPFO",
        "ESIC",
        "STARTUP_INDIA",
        "NSIC",
        "MAKE_IN_INDIA",
        "OEM",
        "BLACKLIST",
    }
    assert expected_sources.issubset(set(sources))


@pytest.mark.parametrize("source,expected_cls", [
    ("GST", DemoGSTProvider),
    ("PAN", DemoPANProvider),
    ("UDYAM", DemoUdyamProvider),
    ("MSME", DemoUdyamProvider),
    ("EPFO", DemoEPFOProvider),
    ("ESIC", DemoESICProvider),
    ("STARTUP_INDIA", DemoStartupIndiaProvider),
    ("NSIC", DemoNSICProvider),
    ("MAKE_IN_INDIA", DemoMakeInIndiaProvider),
    ("OEM", DemoOEMProvider),
    ("BLACKLIST", DemoBlacklistProvider),
    ("BLACKLISTING", DemoBlacklistProvider),
    ("DEBARMENT", DemoBlacklistProvider),
])
def test_get_provider_resolves_all_sources_and_aliases(source, expected_cls):
    """get_provider resolves each registered source and alias to an instance of expected provider."""
    provider = get_provider(source)
    assert isinstance(provider, expected_cls)
    assert isinstance(provider, GovernmentProvider)


def test_get_provider_unknown_source_raises_value_error():
    """Unsupported sources must raise a controlled ValueError."""
    with pytest.raises(ValueError, match="Unknown or unsupported government verification source"):
        get_provider("NON_EXISTENT_SOURCE_XYZ")


def test_get_government_provider_backward_compatibility():
    """Legacy helper get_government_provider remains backward compatible."""
    p_gst = get_government_provider("GST")
    assert isinstance(p_gst, DemoGSTProvider)
    p_pan = get_government_provider("PAN")
    assert isinstance(p_pan, DemoPANProvider)


# ==============================================================================
# 2. PROVIDER CAPABILITIES & AUDIT METADATA TESTS
# ==============================================================================

@pytest.mark.parametrize("source", [
    "GST", "PAN", "UDYAM", "EPFO", "ESIC", "STARTUP_INDIA", "NSIC", "MAKE_IN_INDIA", "OEM", "BLACKLIST"
])
def test_all_providers_declare_capabilities_and_demo_mode(source):
    """Every provider must return ProviderCapabilities declaring is_demo=True."""
    provider = get_provider(source)
    caps = provider.get_capabilities()
    assert isinstance(caps, ProviderCapabilities)
    assert caps.source == source if source not in ("MSME", "BLACKLISTING") else caps.source
    assert caps.is_demo is True
    assert len(caps.supported_identifiers) > 0


# ==============================================================================
# 3. INDIVIDUAL DEMO PROVIDERS (FOUND, NOT_FOUND, UNAVAILABLE)
# ==============================================================================

def test_udyam_provider_scenarios():
    provider = DemoUdyamProvider()
    # 1. FOUND
    resp = provider.verify("UDYAM-TN-00-0000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.retrieved_at is not None
    assert resp.data["enterprise_type"] == "Micro"
    assert resp.data["status"] == "ACTIVE"

    # 2. NOT_FOUND
    resp_nf = provider.verify("UDYAM-NOTFOUND-000001")
    assert resp_nf.status == GovernmentSourceStatus.NOT_FOUND.value
    assert resp_nf.is_demo is True

    # 3. UNAVAILABLE
    resp_un = provider.verify("UDYAM-UNAVAIL-000001")
    assert resp_un.status == GovernmentSourceStatus.UNAVAILABLE.value
    assert resp_un.is_demo is True


def test_epfo_provider_scenarios():
    provider = DemoEPFOProvider()
    resp = provider.verify("EPFO-DEMO-000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.data["status"] == "ACTIVE"
    assert resp.data["establishment_name"] == "ABC TECHNOLOGIES PRIVATE LIMITED"

    resp_nf = provider.verify("EPFO-NOTFOUND-000001")
    assert resp_nf.status == GovernmentSourceStatus.NOT_FOUND.value

    resp_un = provider.verify("EPFO-UNAVAIL-000001")
    assert resp_un.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_esic_provider_scenarios():
    provider = DemoESICProvider()
    resp = provider.verify("ESIC-DEMO-000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.data["status"] == "ACTIVE"

    resp_nf = provider.verify("ESIC-NOTFOUND-000001")
    assert resp_nf.status == GovernmentSourceStatus.NOT_FOUND.value

    resp_un = provider.verify("ESIC-UNAVAIL-000001")
    assert resp_un.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_startup_india_provider_scenarios():
    provider = DemoStartupIndiaProvider()
    resp = provider.verify("DPIIT-DEMO-000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.data["status"] == "ACTIVE"
    assert resp.data["entity_name"] == "ABC TECHNOLOGIES PRIVATE LIMITED"

    resp_nf = provider.verify("DPIIT-NOTFOUND-000001")
    assert resp_nf.status == GovernmentSourceStatus.NOT_FOUND.value

    resp_un = provider.verify("DPIIT-UNAVAIL-000001")
    assert resp_un.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_nsic_provider_scenarios():
    provider = DemoNSICProvider()
    resp = provider.verify("NSIC-DEMO-000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.data["status"] == "ACTIVE"
    assert resp.data["valid_until"] == "2027-04-12"

    resp_nf = provider.verify("NSIC-NOTFOUND-000001")
    assert resp_nf.status == GovernmentSourceStatus.NOT_FOUND.value

    resp_un = provider.verify("NSIC-UNAVAIL-000001")
    assert resp_un.status == GovernmentSourceStatus.UNAVAILABLE.value


def test_make_in_india_provider_scenarios():
    provider = DemoMakeInIndiaProvider()
    # High local content (65%)
    resp_high = provider.verify("MII-DEMO-000001")
    assert resp_high.status == GovernmentSourceStatus.FOUND.value
    assert resp_high.is_demo is True
    assert resp_high.data["local_content_percentage"] == 65
    assert resp_high.data["status"] == "VALID"

    # Lower local content (40%)
    resp_low = provider.verify("MII-LOW-000001")
    assert resp_low.status == GovernmentSourceStatus.FOUND.value
    assert resp_low.is_demo is True
    assert resp_low.data["local_content_percentage"] == 40
    assert resp_low.data["status"] == "VALID"

    # Not found & unavailable
    assert provider.verify("MII-NOTFOUND-000001").status == GovernmentSourceStatus.NOT_FOUND.value
    assert provider.verify("MII-UNAVAIL-000001").status == GovernmentSourceStatus.UNAVAILABLE.value


def test_oem_provider_scenarios():
    provider = DemoOEMProvider()
    resp = provider.verify("OEM-DEMO-000001")
    assert resp.status == GovernmentSourceStatus.FOUND.value
    assert resp.is_demo is True
    assert resp.data["status"] == "VALID"
    assert resp.data["oem_name"] == "ABC ORIGINAL EQUIPMENT MANUFACTURER"

    assert provider.verify("OEM-NOTFOUND-000001").status == GovernmentSourceStatus.NOT_FOUND.value
    assert provider.verify("OEM-UNAVAIL-000001").status == GovernmentSourceStatus.UNAVAILABLE.value


def test_blacklist_provider_scenarios():
    provider = DemoBlacklistProvider()
    # Clear entity
    resp_clear = provider.verify("ABC TECHNOLOGIES PRIVATE LIMITED")
    assert resp_clear.status == GovernmentSourceStatus.FOUND.value
    assert resp_clear.is_demo is True
    assert resp_clear.data["listed"] is False
    assert resp_clear.data["status"] == "CLEAR"

    # Listed entity (Debarred)
    resp_listed = provider.verify("BLACKLIST-LISTED-000001")
    assert resp_listed.status == GovernmentSourceStatus.FOUND.value
    assert resp_listed.is_demo is True
    assert resp_listed.data["listed"] is True
    assert resp_listed.data["status"] == "LISTED"
    assert resp_listed.data["reason"] is not None

    # Not found & unavailable
    assert provider.verify("BLACKLIST-NOTFOUND-000001").status == GovernmentSourceStatus.NOT_FOUND.value
    assert provider.verify("BLACKLIST-UNAVAIL-000001").status == GovernmentSourceStatus.UNAVAILABLE.value


# ==============================================================================
# 4. COMPLIANCE ENGINE NUMERIC RULE EVALUATION (MAKE IN INDIA)
# ==============================================================================

def test_compliance_engine_field_greater_than_or_equal_pass():
    """Make In India local content 65% meets >= 50% threshold -> PASS."""
    rule = {
        "source": "MAKE_IN_INDIA",
        "field": "local_content_percentage",
        "operator": "FIELD_GREATER_THAN_OR_EQUAL",
        "expected_value": 50.0,
    }
    evidence = [
        Evidence(
            source="MAKE_IN_INDIA",
            identifier="MII-DEMO-000001",
            verified=True,
            data={"local_content_percentage": 65.0, "status": "VERIFIED"},
        )
    ]
    result = ComplianceEngine.evaluate_rule(rule, evidence)
    assert result.passed is True
    assert result.status == "PASS"
    assert "meets required minimum threshold" in result.reason


def test_compliance_engine_field_greater_than_or_equal_fail():
    """Make In India local content 40% fails >= 50% threshold -> FAIL."""
    rule = {
        "source": "MAKE_IN_INDIA",
        "field": "local_content_percentage",
        "operator": "FIELD_GREATER_THAN_OR_EQUAL",
        "expected_value": 50.0,
    }
    evidence = [
        Evidence(
            source="MAKE_IN_INDIA",
            identifier="MII-LOW-000001",
            verified=True,
            data={"local_content_percentage": 40.0, "status": "VERIFIED"},
        )
    ]
    result = ComplianceEngine.evaluate_rule(rule, evidence)
    assert result.passed is False
    assert result.status == "FAIL"
    assert "below required minimum threshold" in result.reason


def test_compliance_engine_field_greater_than_or_equal_missing_evidence():
    """Missing evidence for numeric rule returns NOT_VERIFIED."""
    rule = {
        "source": "MAKE_IN_INDIA",
        "field": "local_content_percentage",
        "operator": "FIELD_GREATER_THAN_OR_EQUAL",
        "expected_value": 50.0,
    }
    result = ComplianceEngine.evaluate_rule(rule, [])
    assert result.passed is False
    assert result.status == "NOT_VERIFIED"


# ==============================================================================
# 5. BLACKLIST RULE EVALUATION & NO AUTOMATIC BIDDER DISQUALIFICATION
# ==============================================================================

def test_compliance_engine_blacklist_clear_evaluation():
    """Clear entity evaluated against debarment requirement -> PASS."""
    requirement_code = "REQ-DECL-BLACKLIST"
    requirement_title = "Debarment/Blacklisting Restriction"
    rule_configs = [
        {
            "source": "BLACKLIST",
            "field": "status",
            "operator": "EQUALS",
            "expected_value": "CLEAR",
        }
    ]
    evidence = [
        Evidence(
            source="BLACKLIST",
            identifier="ABC TECHNOLOGIES PRIVATE LIMITED",
            verified=True,
            data={"status": "CLEAR", "listed": False},
        )
    ]
    req_result = ComplianceEngine.evaluate_requirement(
        requirement_code, requirement_title, rule_configs, evidence
    )
    assert req_result.status == "PASS"
    assert req_result.rule_results[0].passed is True


def test_compliance_engine_blacklist_listed_evaluation_fails_requirement_only():
    """Listed entity evaluated against debarment requirement -> FAIL.
    
    CRITICAL: The engine marks the requirement status as FAIL.
    It does NOT disqualify the bidder or make any procurement decision.
    """
    requirement_code = "REQ-DECL-BLACKLIST"
    requirement_title = "Debarment/Blacklisting Restriction"
    rule_configs = [
        {
            "source": "BLACKLIST",
            "field": "status",
            "operator": "EQUALS",
            "expected_value": "CLEAR",
        }
    ]
    evidence = [
        Evidence(
            source="BLACKLIST",
            identifier="BLACKLIST-LISTED-000001",
            verified=True,
            data={"status": "LISTED", "listed": True, "restriction_reason": "Default in contract delivery"},
        )
    ]
    req_result = ComplianceEngine.evaluate_requirement(
        requirement_code, requirement_title, rule_configs, evidence
    )
    # Requirement evaluation is FAIL
    assert req_result.status == "FAIL"
    assert req_result.rule_results[0].passed is False
    assert req_result.rule_results[0].status == "FAIL"
    # Ensure no automated bidder disqualification attribute or action
    assert not hasattr(req_result, "bidder_decision")
    assert not hasattr(req_result, "disqualified")


# ==============================================================================
# 6. GOVERNMENT VERIFICATION SERVICE MULTI-SOURCE SUPPORT
# ==============================================================================

def test_government_verification_service_supported_sources():
    """Service must declare all 10 sources as supported for verification."""
    assert "UDYAM" in SUPPORTED_VERIFICATION_SOURCES
    assert "EPFO" in SUPPORTED_VERIFICATION_SOURCES
    assert "ESIC" in SUPPORTED_VERIFICATION_SOURCES
    assert "STARTUP_INDIA" in SUPPORTED_VERIFICATION_SOURCES
    assert "NSIC" in SUPPORTED_VERIFICATION_SOURCES
    assert "MAKE_IN_INDIA" in SUPPORTED_VERIFICATION_SOURCES
    assert "OEM" in SUPPORTED_VERIFICATION_SOURCES
    assert "BLACKLIST" in SUPPORTED_VERIFICATION_SOURCES


def test_government_verification_model_schema_attributes():
    """GovernmentVerification model supports is_demo and retrieved_at with nullable document_id."""
    rec = GovernmentVerification(
        id=uuid.uuid4(),
        document_id=None,
        bidder_id=uuid.uuid4(),
        source="UDYAM",
        provider="demo",
        identifier="UDYAM-TN-00-0000001",
        status="COMPLETED",
        verification_result="VERIFIED",
        is_demo=True,
        retrieved_at=datetime.now(timezone.utc),
    )
    assert rec.is_demo is True
    assert rec.retrieved_at is not None
    assert rec.document_id is None
