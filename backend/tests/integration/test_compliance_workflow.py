import uuid
from datetime import datetime, timezone

import pytest

from test_compliance_orchestration import sqlite_session
from app.models.bidder import Bidder
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.review.service import ReviewService
from app.services.audit_service import AuditService
from app.services.compliance_service import ComplianceService, NoApprovedRequirementsError
from app.dashboard.service import DashboardService
from app.schemas.compliance import TenderRequirementCreate


def _linked_entities(session, tender_id, bidder_id):
    tender = session.get(Tender, uuid.UUID(tender_id))
    bidder = session.get(Bidder, uuid.UUID(bidder_id))
    tender.bidders.append(bidder)
    session.commit()
    return tender, bidder


def _approved_requirement(session, tender_id, user_id, title="GST requirement"):
    service = ComplianceService(db=session)
    requirement = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            title=title,
            type="GST",
            mandatory=True,
            rule_type="STATUS_EQUALS",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
        ),
        user_id=user_id,
    )
    service.approve_requirement(str(requirement.id), officer_id=user_id)
    return requirement


def _government_record(session, bidder_id, status="COMPLETED", result="MATCH", government_status="ACTIVE"):
    record = GovernmentVerification(
        id=uuid.uuid4(), bidder_id=uuid.UUID(bidder_id), source="GST", provider="DEMO",
        identifier="29ABCDE1234F1Z5", status=status, verification_result=result,
        government_data={"status": government_status, "legal_name": "Apex Global Technologies Pvt Ltd"},
        created_at=datetime.now(timezone.utc), retrieved_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.commit()
    return record


def test_compliance_review_dashboard_and_audit(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    tender, bidder = _linked_entities(session, tender_id, bidder_id)
    requirement = _approved_requirement(session, tender_id, user_id)
    _government_record(session, bidder_id)

    compliance = ComplianceService(db=session)
    evaluation = compliance.run_compliance_evaluation(tender_id, bidder_id)
    assert evaluation.status == "COMPLETED"
    result = evaluation.requirements[0]
    assert result.requirement_id == requirement.id
    assert result.evidence

    review_service = ReviewService(session)
    payload = review_service.create_review(evaluation.evaluation_id)
    review_service.update_requirement_review(evaluation.evaluation_id, result.id, "REVIEWED", "Evidence checked")
    review_service.update_decision(evaluation.evaluation_id, "QUALIFIED", "Officer decision")
    completed = review_service.complete_review(evaluation.evaluation_id)
    assert completed.review.status == "COMPLETED"
    assert completed.review.decision == "QUALIFIED"

    dashboard = DashboardService(session).get_dashboard(tender_id)
    bidder_row = next(row for row in dashboard["bidders"] if row["bidder_id"] == bidder_id)
    assert bidder_row["evaluation_status"] == "COMPLETED"
    assert bidder_row["review_status"] == "COMPLETED"
    assert bidder_row["officer_decision"] == "QUALIFIED"
    assert dashboard["requirement_issues"][0]["total"] == 1

    events, _ = AuditService(session).list_events(limit=100, session=session)
    actions = {event.action for event in events}
    assert {"REQUIREMENT_APPROVED", "OFFICER_REVIEW_STARTED", "OFFICER_DECISION_RECORDED", "OFFICER_REVIEW_COMPLETED"}.issubset(actions)


def test_ai_suggested_requirement_is_excluded_until_approval(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    _linked_entities(session, tender_id, bidder_id)
    service = ComplianceService(db=session)
    requirement = service.create_tender_requirement(
        tender_id,
        TenderRequirementCreate(
            title="Suggested GST", type="GST", rule_type="STATUS_EQUALS",
            rule_config=[{"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}],
            status="AI_SUGGESTED",
        ),
        user_id=user_id,
    )
    with pytest.raises(NoApprovedRequirementsError):
        service.run_compliance_evaluation(tender_id, bidder_id)

    service.approve_requirement(str(requirement.id), officer_id=user_id)
    evaluation = service.run_compliance_evaluation(tender_id, bidder_id)
    assert [item.requirement_id for item in evaluation.requirements] == [requirement.id]


def test_unavailable_government_source_is_not_a_pass(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    _linked_entities(session, tender_id, bidder_id)
    _approved_requirement(session, tender_id, user_id)
    _government_record(session, bidder_id, status="FAILED", result="SOURCE_ERROR", government_status=None)

    evaluation = ComplianceService(db=session).run_compliance_evaluation(tender_id, bidder_id)
    assert evaluation.requirements[0].status == "NOT_VERIFIED"
    assert evaluation.requirements[0].status != "PASS"


def test_historical_evaluations_keep_evidence_snapshots(sqlite_session):
    session, tender_id, bidder_id, user_id = sqlite_session
    _linked_entities(session, tender_id, bidder_id)
    _approved_requirement(session, tender_id, user_id)
    _government_record(session, bidder_id, government_status="ACTIVE")
    service = ComplianceService(db=session)

    evaluation_a = service.run_compliance_evaluation(tender_id, bidder_id)
    snapshot_a = evaluation_a.requirements[0].evidence
    _government_record(session, bidder_id, government_status="CANCELLED")
    evaluation_b = service.run_compliance_evaluation(tender_id, bidder_id)

    assert evaluation_b.requirements[0].status == "FAIL"
    original = service.get_compliance_evaluation(str(evaluation_a.evaluation_id))
    assert original.requirements[0].evidence == snapshot_a
    assert original.requirements[0].status == "PASS"
