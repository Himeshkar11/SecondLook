"""Statutory Compliance Service (Task 11).

Orchestrates evaluation of tender statutory requirements against verified evidence.
Produces factual compliance evaluations at the individual requirement level.
Strictly decoupled from final procurement awards, rejections, qualifications, or scoring.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import RequirementEvaluation, TenderRequirement
from app.schemas.compliance import (
    DEFAULT_COMPLIANCE_DISCLAIMER,
    BidderComplianceResponse,
    ComplianceSummary,
    RequirementEvaluationRead,
    TenderRequirementCreate,
)
from app.verification.compliance_engine import ComplianceEngine, Evidence

logger = logging.getLogger(__name__)

# Standard demo statutory requirements per Step 20
DEFAULT_DEMO_REQUIREMENTS = [
    {
        "code": "REQ-GST-001",
        "title": "Active GST Registration",
        "description": "Bidder must possess an active GST registration verified against government records.",
        "type": "GST",
        "mandatory": True,
        "display_order": 1,
        "rule_config": [
            {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
        ],
    },
    {
        "code": "REQ-GST-002",
        "title": "Tamil Nadu GST Registration",
        "description": "Bidder must be registered in Tamil Nadu (State Code 33) for local procurement preference.",
        "type": "GST",
        "mandatory": True,
        "display_order": 2,
        "rule_config": [
            {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"}
        ],
    },
    {
        "code": "REQ-PAN-001",
        "title": "Valid PAN",
        "description": "Bidder must possess a valid, active PAN card verified against income tax records.",
        "type": "PAN",
        "mandatory": True,
        "display_order": 3,
        "rule_config": [
            {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
        ],
    },
]


class ComplianceService:
    """Service orchestrating compliance evaluations for tender requirements."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        if SessionLocal is not None:
            return SessionLocal(), True
        raise RuntimeError("No database connection available")

    def get_tender_requirements(self, tender_id: str) -> List[TenderRequirement]:
        """Fetch all statutory requirements for a tender, ensuring defaults if empty."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            stmt = (
                select(TenderRequirement)
                .where(TenderRequirement.tender_id == t_uuid)
                .order_by(TenderRequirement.display_order.asc())
            )
            requirements = list(session.execute(stmt).scalars().all())
            if not requirements:
                requirements = self.ensure_default_demo_requirements(str(t_uuid), session=session)
            return requirements
        finally:
            if should_close:
                session.close()

    def create_tender_requirement(
        self, tender_id: str, data: TenderRequirementCreate
    ) -> TenderRequirement:
        """Create a new requirement for a tender."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            req = TenderRequirement(
                id=uuid.uuid4(),
                tender_id=t_uuid,
                code=data.code,
                title=data.title,
                description=data.description,
                type=data.type,
                mandatory=data.mandatory,
                display_order=data.display_order,
                rule_config=data.rule_config,
            )
            session.add(req)
            session.commit()
            session.refresh(req)
            return req
        finally:
            if should_close:
                session.close()

    def ensure_default_demo_requirements(
        self, tender_id: str, session: Optional[Session] = None
    ) -> List[TenderRequirement]:
        """Seed default demo statutory requirements for a tender if none exist."""
        sess = session
        should_close = False
        if sess is None:
            sess, should_close = self._get_session()

        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            existing = list(
                sess.execute(
                    select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)
                ).scalars().all()
            )
            if existing:
                return existing

            created: List[TenderRequirement] = []
            for item in DEFAULT_DEMO_REQUIREMENTS:
                req = TenderRequirement(
                    id=uuid.uuid4(),
                    tender_id=t_uuid,
                    code=item["code"],
                    title=item["title"],
                    description=item["description"],
                    type=item["type"],
                    mandatory=item["mandatory"],
                    display_order=item["display_order"],
                    rule_config=item["rule_config"],
                )
                sess.add(req)
                created.append(req)
            sess.commit()
            for r in created:
                sess.refresh(r)
            return created
        finally:
            if should_close and sess is not None:
                sess.close()

    def collect_bidder_evidence(self, bidder_id: str, session: Session) -> List[Evidence]:
        """Aggregate all available evidence items (both verified and unverified) for a bidder."""
        b_uuid = uuid.UUID(bidder_id) if isinstance(bidder_id, str) else bidder_id
        evidence_list: List[Evidence] = []

        # 1. Fetch government verifications
        gv_stmt = (
            select(GovernmentVerification)
            .where(GovernmentVerification.bidder_id == b_uuid)
            .order_by(GovernmentVerification.created_at.desc())
        )
        verifications = list(session.execute(gv_stmt).scalars().all())

        seen_sources = set()
        for gv in verifications:
            # Check verification success
            is_verified = (
                gv.status == "COMPLETED"
                and gv.verification_result in ["MATCH", "VERIFIED"]
            )
            gov_data = gv.government_data or {}
            # Flatten or ensure fields like status, state are accessible
            ev = Evidence(
                source=gv.source.upper(),
                identifier=gv.identifier,
                verified=is_verified,
                verification_id=str(gv.id),
                document_id=str(gv.document_id) if gv.document_id else None,
                data=gov_data,
            )
            evidence_list.append(ev)
            seen_sources.add(gv.source.upper())

        # 2. Also check documents to capture unverified evidence if government verification hasn't run
        doc_stmt = select(Document).where(Document.bidder_id == b_uuid)
        docs = list(session.execute(doc_stmt).scalars().all())
        for doc in docs:
            doc_type = (doc.document_type or "").upper()
            if doc_type in {"GST", "PAN"} and doc_type not in seen_sources:
                # Evidence exists as document / AI extraction, but no government verification yet
                extracted = getattr(doc, "ai_extraction", None) or getattr(doc, "extracted_data", None) or {}
                identifier = (
                    extracted.get("gstin")
                    or extracted.get("pan")
                    or extracted.get("document_number")
                )
                evidence_list.append(
                    Evidence(
                        source=doc_type,
                        identifier=identifier,
                        verified=False,
                        verification_id=None,
                        document_id=str(doc.id),
                        data=extracted,
                    )
                )

        return evidence_list

    def evaluate_bidder_compliance(
        self, tender_id: str, bidder_id: str
    ) -> BidderComplianceResponse:
        """Run deterministic compliance evaluation for all requirements of a tender."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            b_uuid = uuid.UUID(bidder_id) if isinstance(bidder_id, str) else bidder_id

            # Verify tender and bidder existence
            tender = session.get(Tender, t_uuid)
            bidder = session.get(Bidder, b_uuid)
            bidder_name = bidder.legal_name if bidder else None

            # Get requirements
            requirements = self.get_tender_requirements(str(t_uuid))

            # Collect evidence
            evidence_list = self.collect_bidder_evidence(str(b_uuid), session)

            # Clear existing evaluations for this tender & bidder
            del_stmt = delete(RequirementEvaluation).where(
                RequirementEvaluation.tender_id == t_uuid,
                RequirementEvaluation.bidder_id == b_uuid,
            )
            session.execute(del_stmt)

            evaluation_reads: List[RequirementEvaluationRead] = []
            pass_cnt = 0
            fail_cnt = 0
            partial_cnt = 0
            not_verified_cnt = 0
            not_applicable_cnt = 0
            mandatory_failed_cnt = 0
            mandatory_not_verified_cnt = 0

            for req in requirements:
                rule_config = req.rule_config or []
                if isinstance(rule_config, dict):
                    rule_config = [rule_config]

                eval_result = ComplianceEngine.evaluate_requirement(
                    requirement_code=req.code,
                    requirement_title=req.title,
                    rule_configs=rule_config,
                    evidence_list=evidence_list,
                )

                # Persist evaluation record
                db_eval = RequirementEvaluation(
                    id=uuid.uuid4(),
                    requirement_id=req.id,
                    bidder_id=b_uuid,
                    tender_id=t_uuid,
                    status=eval_result.status,
                    result={
                        "summary": eval_result.summary,
                        "explanation": eval_result.explanation,
                    },
                    rule_results=[r.__dict__ for r in eval_result.rule_results],
                    evidence=eval_result.evidence_used,
                    evaluated_at=datetime.now(timezone.utc),
                )
                session.add(db_eval)

                # Count statistics
                status = eval_result.status
                if status == "PASS":
                    pass_cnt += 1
                elif status == "FAIL":
                    fail_cnt += 1
                    if req.mandatory:
                        mandatory_failed_cnt += 1
                elif status == "PARTIAL":
                    partial_cnt += 1
                    if req.mandatory:
                        mandatory_failed_cnt += 1
                elif status == "NOT_VERIFIED":
                    not_verified_cnt += 1
                    if req.mandatory:
                        mandatory_not_verified_cnt += 1
                elif status == "NOT_APPLICABLE":
                    not_applicable_cnt += 1

                evaluation_reads.append(
                    RequirementEvaluationRead(
                        id=db_eval.id,
                        requirement_id=req.id,
                        bidder_id=b_uuid,
                        tender_id=t_uuid,
                        requirement_code=req.code,
                        requirement_title=req.title,
                        requirement_type=req.type,
                        mandatory=req.mandatory,
                        status=db_eval.status,
                        result=db_eval.result,
                        rule_results=db_eval.rule_results,
                        evidence=db_eval.evidence,
                        evaluated_at=db_eval.evaluated_at.isoformat() if db_eval.evaluated_at else None,
                    )
                )

            session.commit()

            summary = ComplianceSummary(
                total_requirements=len(requirements),
                pass_count=pass_cnt,
                fail_count=fail_cnt,
                partial_count=partial_cnt,
                not_verified_count=not_verified_cnt,
                not_applicable_count=not_applicable_cnt,
                mandatory_failed=mandatory_failed_cnt,
                mandatory_not_verified=mandatory_not_verified_cnt,
            )

            return BidderComplianceResponse(
                tender_id=str(t_uuid),
                bidder_id=str(b_uuid),
                bidder_legal_name=bidder_name,
                summary=summary,
                requirements=evaluation_reads,
                disclaimer=DEFAULT_COMPLIANCE_DISCLAIMER,
            )
        finally:
            if should_close:
                session.close()

    def get_bidder_compliance(
        self, tender_id: str, bidder_id: str
    ) -> BidderComplianceResponse:
        """Fetch existing compliance evaluation or run an initial evaluation if none exist."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            b_uuid = uuid.UUID(bidder_id) if isinstance(bidder_id, str) else bidder_id

            stmt = (
                select(RequirementEvaluation)
                .where(
                    RequirementEvaluation.tender_id == t_uuid,
                    RequirementEvaluation.bidder_id == b_uuid,
                )
            )
            existing_evals = list(session.execute(stmt).scalars().all())
            if not existing_evals:
                # Run fresh evaluation
                return self.evaluate_bidder_compliance(tender_id, bidder_id)

            # Build response from existing persisted evaluations
            requirements_map = {
                req.id: req
                for req in session.execute(
                    select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)
                ).scalars().all()
            }
            bidder = session.get(Bidder, b_uuid)

            reads: List[RequirementEvaluationRead] = []
            pass_cnt = 0
            fail_cnt = 0
            partial_cnt = 0
            not_verified_cnt = 0
            not_applicable_cnt = 0
            mandatory_failed_cnt = 0
            mandatory_not_verified_cnt = 0

            for ev in existing_evals:
                req = requirements_map.get(ev.requirement_id)
                req_code = req.code if req else "UNKNOWN"
                req_title = req.title if req else "Unknown Requirement"
                req_type = req.type if req else "GST"
                is_mandatory = req.mandatory if req else True

                status = ev.status
                if status == "PASS":
                    pass_cnt += 1
                elif status == "FAIL":
                    fail_cnt += 1
                    if is_mandatory:
                        mandatory_failed_cnt += 1
                elif status == "PARTIAL":
                    partial_cnt += 1
                    if is_mandatory:
                        mandatory_failed_cnt += 1
                elif status == "NOT_VERIFIED":
                    not_verified_cnt += 1
                    if is_mandatory:
                        mandatory_not_verified_cnt += 1
                elif status == "NOT_APPLICABLE":
                    not_applicable_cnt += 1

                reads.append(
                    RequirementEvaluationRead(
                        id=ev.id,
                        requirement_id=ev.requirement_id,
                        bidder_id=ev.bidder_id,
                        tender_id=ev.tender_id,
                        requirement_code=req_code,
                        requirement_title=req_title,
                        requirement_type=req_type,
                        mandatory=is_mandatory,
                        status=ev.status,
                        result=ev.result,
                        rule_results=ev.rule_results,
                        evidence=ev.evidence,
                        evaluated_at=ev.evaluated_at.isoformat() if ev.evaluated_at else None,
                    )
                )

            summary = ComplianceSummary(
                total_requirements=len(existing_evals),
                pass_count=pass_cnt,
                fail_count=fail_cnt,
                partial_count=partial_cnt,
                not_verified_count=not_verified_cnt,
                not_applicable_count=not_applicable_cnt,
                mandatory_failed=mandatory_failed_cnt,
                mandatory_not_verified=mandatory_not_verified_cnt,
            )

            return BidderComplianceResponse(
                tender_id=str(t_uuid),
                bidder_id=str(b_uuid),
                bidder_legal_name=bidder.legal_name if bidder else None,
                summary=summary,
                requirements=reads,
                disclaimer=DEFAULT_COMPLIANCE_DISCLAIMER,
            )
        finally:
            if should_close:
                session.close()
