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

from app.ai.tender_extractor import get_tender_requirement_extractor
from app.database.connection import SessionLocal
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.schemas.compliance import (
    DEFAULT_COMPLIANCE_DISCLAIMER,
    VALID_REQUIREMENT_STATUSES,
    VALID_REQUIREMENT_TYPES,
    BidderComplianceResponse,
    ComplianceEvaluationRead,
    ComplianceEvaluationSummaryItem,
    ComplianceSummary,
    EvaluationEvidenceTraceResponse,
    EvidenceTraceChainRead,
    FieldComparisonRead,
    NormalizedEvidenceItemRead,
    RequirementEvaluationRead,
    TenderRequirementCreate,
    TenderRequirementUpdate,
)
from app.services.audit_service import get_audit_service
from app.verification.compliance_engine import ComplianceEngine, Evidence
from app.verification.evidence_resolver import EvidenceResolver
from app.verification.explanation_engine import ExplanationEngine

logger = logging.getLogger(__name__)


class NoApprovedRequirementsError(ValueError):
    """Raised when an evaluation is attempted with zero approved requirements."""
    pass


# Standard demo statutory requirements per Step 20
DEFAULT_DEMO_REQUIREMENTS = [
    {
        "code": "REQ-GST-001",
        "title": "Active GST Registration",
        "description": "Bidder must possess an active GST registration verified against government records.",
        "type": "GST",
        "mandatory": True,
        "display_order": 1,
        "status": "APPROVED",
        "rule_type": "STATUS_EQUALS",
        "parameters": {"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
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
        "status": "APPROVED",
        "rule_type": "FIELD_EQUALS",
        "parameters": {"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
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
        "status": "APPROVED",
        "rule_type": "STATUS_EQUALS",
        "parameters": {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
        "rule_config": [
            {"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"}
        ],
    },
]


class ComplianceService:
    """Service orchestrating compliance evaluations and tender requirement management."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        if SessionLocal is not None:
            return SessionLocal(), True
        raise RuntimeError("No database connection available")

    def get_tender_requirements(
        self, tender_id: str, status: Optional[str] = None
    ) -> List[TenderRequirement]:
        """Fetch all requirements for a tender, optionally filtered by lifecycle status."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            stmt = select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)
            if status:
                stmt = stmt.where(TenderRequirement.status == status.upper())
            stmt = stmt.order_by(TenderRequirement.display_order.asc(), TenderRequirement.created_at.asc())
            requirements = list(session.execute(stmt).scalars().all())
            if not requirements and not status:
                requirements = self.ensure_default_demo_requirements(str(t_uuid), session=session)
            return requirements
        finally:
            if should_close:
                session.close()

    def get_tender_requirement(self, requirement_id: str) -> Optional[TenderRequirement]:
        """Fetch a single tender requirement by its UUID."""
        session, should_close = self._get_session()
        try:
            req_uuid = uuid.UUID(requirement_id) if isinstance(requirement_id, str) else requirement_id
            stmt = select(TenderRequirement).where(TenderRequirement.id == req_uuid)
            return session.execute(stmt).scalars().first()
        finally:
            if should_close:
                session.close()

    def create_tender_requirement(
        self, tender_id: str, data: TenderRequirementCreate, user_id: Optional[str] = None
    ) -> TenderRequirement:
        """Create a new requirement for a tender. Initial status defaults to UNDER_REVIEW or DRAFT.
        
        Direct escalation to APPROVED is prevented on creation.
        """
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            
            # Auto-generate code if omitted
            req_type = data.type.upper() if data.type else "GST"
            code = data.code
            if not code:
                count_stmt = select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)
                existing_cnt = len(list(session.execute(count_stmt).scalars().all()))
                code = f"REQ-{req_type}-{existing_cnt + 1:03d}"

            # Ensure initial status is not directly APPROVED
            initial_status = data.status.upper() if data.status else "UNDER_REVIEW"
            if initial_status == "APPROVED":
                initial_status = "UNDER_REVIEW"

            # Build rule_config from rule_type and parameters if rule_config is empty
            rule_config = data.rule_config or []
            if not rule_config and data.rule_type and data.parameters:
                params = data.parameters
                rule_config = [{
                    "source": params.get("source", req_type),
                    "field": params.get("field", "status"),
                    "operator": params.get("operator", "EQUALS"),
                    "expected_value": params.get("expected_value", "ACTIVE"),
                }]

            creator_uuid = None
            if user_id:
                try:
                    creator_uuid = uuid.UUID(user_id)
                except ValueError:
                    creator_uuid = None

            req = TenderRequirement(
                id=uuid.uuid4(),
                tender_id=t_uuid,
                code=code,
                title=data.title,
                description=data.description,
                type=req_type,
                mandatory=data.mandatory,
                display_order=data.display_order,
                status=initial_status,
                rule_type=data.rule_type,
                parameters=data.parameters,
                rule_config=rule_config,
                source_document_id=data.source_document_id,
                source_text=data.source_text,
                source_page=data.source_page,
                source_section=data.source_section,
                created_by=creator_uuid,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(req)
            session.commit()
            session.refresh(req)
            return req
        finally:
            if should_close:
                session.close()

    def update_tender_requirement(
        self, requirement_id: str, data: TenderRequirementUpdate
    ) -> TenderRequirement:
        """Update an existing requirement.
        
        Enforces:
        1. Reject direct escalation to APPROVED via generic update.
        2. If requirement was APPROVED and core rule/content fields are modified,
           automatically demote status to UNDER_REVIEW and clear approved_at/approved_by.
        """
        session, should_close = self._get_session()
        try:
            req_uuid = uuid.UUID(requirement_id) if isinstance(requirement_id, str) else requirement_id
            req = session.get(TenderRequirement, req_uuid)
            if req is None:
                raise KeyError(f"Tender requirement with ID '{requirement_id}' not found")

            # Check for illegal direct escalation to APPROVED
            if data.status and data.status.upper() == "APPROVED":
                raise ValueError(
                    "Cannot escalate requirement status to APPROVED directly via generic update. "
                    "Use the dedicated /approve endpoint."
                )

            # Detect content modifications that invalidate prior approval
            content_changed = False
            if data.title is not None and data.title != req.title:
                req.title = data.title
                content_changed = True
            if data.description is not None and data.description != req.description:
                req.description = data.description
                content_changed = True
            if data.type is not None and data.type.upper() != req.type:
                req.type = data.type.upper()
                content_changed = True
            if data.mandatory is not None and data.mandatory != req.mandatory:
                req.mandatory = data.mandatory
                content_changed = True
            if data.display_order is not None and data.display_order != req.display_order:
                req.display_order = data.display_order
            if data.rule_type is not None and data.rule_type != req.rule_type:
                req.rule_type = data.rule_type
                content_changed = True
            if data.parameters is not None and data.parameters != req.parameters:
                req.parameters = data.parameters
                content_changed = True
            if data.rule_config is not None and data.rule_config != req.rule_config:
                req.rule_config = data.rule_config
                content_changed = True
            if data.source_text is not None:
                req.source_text = data.source_text
            if data.source_page is not None:
                req.source_page = data.source_page
            if data.source_section is not None:
                req.source_section = data.source_section

            # Demote if previously approved and content changed
            if req.status == "APPROVED" and content_changed:
                req.status = "UNDER_REVIEW"
                req.approved_at = None
                req.approved_by = None
            elif data.status is not None:
                new_status = data.status.upper()
                if new_status not in VALID_REQUIREMENT_STATUSES:
                    raise ValueError(f"Invalid status '{data.status}'. Allowed statuses: {sorted(VALID_REQUIREMENT_STATUSES)}")
                
                # Enforce state transition rules
                allowed_transitions = {
                    "AI_SUGGESTED": {"UNDER_REVIEW", "REJECTED"},
                    "DRAFT": {"UNDER_REVIEW", "REJECTED"},
                    "UNDER_REVIEW": {"DRAFT", "REJECTED"},
                    "APPROVED": {"UNDER_REVIEW", "ARCHIVED"},
                    "REJECTED": {"UNDER_REVIEW", "ARCHIVED"},
                    "ARCHIVED": {"UNDER_REVIEW"},
                }
                if new_status != req.status:
                    if new_status not in allowed_transitions.get(req.status, set()):
                        raise ValueError(f"Invalid state transition from {req.status} to {new_status}")
                    req.status = new_status

            req.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(req)
            return req
        finally:
            if should_close:
                session.close()

    def approve_requirement(
        self, requirement_id: str, officer_id: Optional[str] = None
    ) -> TenderRequirement:
        """Explicitly approve a requirement by a procurement officer.
        
        Only APPROVED requirements will be evaluated by the ComplianceEngine.
        Allowed transitions to APPROVED: AI_SUGGESTED, DRAFT, UNDER_REVIEW (or already APPROVED).
        REJECTED and ARCHIVED cannot be approved directly.
        """
        session, should_close = self._get_session()
        try:
            req_uuid = uuid.UUID(requirement_id) if isinstance(requirement_id, str) else requirement_id
            req = session.get(TenderRequirement, req_uuid)
            if req is None:
                raise KeyError(f"Tender requirement with ID '{requirement_id}' not found")

            if req.status in ("ARCHIVED", "REJECTED"):
                raise ValueError(
                    f"Invalid state transition: Cannot approve requirement {requirement_id} "
                    f"with status {req.status}. Only requirements in AI_SUGGESTED, DRAFT, or UNDER_REVIEW can be approved."
                )

            officer_uuid = None
            if officer_id:
                try:
                    officer_uuid = uuid.UUID(officer_id)
                except ValueError:
                    officer_uuid = None

            prev_status = req.status
            now = datetime.now(timezone.utc)
            req.status = "APPROVED"
            req.approved_at = now
            req.updated_at = now
            req.approved_by = officer_uuid
            session.commit()
            session.refresh(req)

            try:
                get_audit_service(session).record_event(
                    action="REQUIREMENT_APPROVED",
                    entity_type="TENDER_REQUIREMENT",
                    entity_id=req.id,
                    user_id=officer_uuid,
                    details={
                        "requirement_id": str(req.id),
                        "tender_id": str(req.tender_id),
                        "code": req.code,
                        "title": req.title,
                        "previous_status": prev_status,
                        "new_status": "APPROVED",
                    },
                    session=session,
                )
            except Exception as audit_err:
                logger.warning("Failed to record audit event for requirement approval: %s", audit_err)

            return req
        finally:
            if should_close:
                session.close()

    def reject_requirement(
        self, requirement_id: str, reason: Optional[str] = None
    ) -> TenderRequirement:
        """Reject a candidate or existing requirement so it is not evaluated."""
        session, should_close = self._get_session()
        try:
            req_uuid = uuid.UUID(requirement_id) if isinstance(requirement_id, str) else requirement_id
            req = session.get(TenderRequirement, req_uuid)
            if req is None:
                raise KeyError(f"Tender requirement with ID '{requirement_id}' not found")

            if req.status == "ARCHIVED":
                raise ValueError(f"Invalid state transition: Cannot reject ARCHIVED requirement {requirement_id}")

            prev_status = req.status
            now = datetime.now(timezone.utc)
            req.status = "REJECTED"
            req.updated_at = now
            session.commit()
            session.refresh(req)

            try:
                get_audit_service(session).record_event(
                    action="REQUIREMENT_REJECTED",
                    entity_type="TENDER_REQUIREMENT",
                    entity_id=req.id,
                    user_id=None,
                    details={
                        "requirement_id": str(req.id),
                        "tender_id": str(req.tender_id),
                        "code": req.code,
                        "title": req.title,
                        "previous_status": prev_status,
                        "new_status": "REJECTED",
                        "reason": reason,
                    },
                    session=session,
                )
            except Exception as audit_err:
                logger.warning("Failed to record audit event for requirement rejection: %s", audit_err)

            return req
        finally:
            if should_close:
                session.close()

    def extract_tender_requirements(
        self, tender_id: str, text: Optional[str] = None, document_id: Optional[str] = None
    ) -> List[TenderRequirement]:
        """Extract requirement candidates from tender text or document using TenderRequirementExtractor.
        
        All extracted candidates are stored strictly with status AI_SUGGESTED.
        They must be reviewed and explicitly approved before the ComplianceEngine can evaluate them.
        """
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            tender = session.get(Tender, t_uuid)
            if tender is None:
                raise KeyError(f"Tender with ID '{tender_id}' not found")

            extraction_text = text
            source_doc_uuid: Optional[uuid.UUID] = None
            if document_id:
                try:
                    source_doc_uuid = uuid.UUID(document_id)
                    doc = session.get(Document, source_doc_uuid)
                    if doc and not extraction_text:
                        extraction_text = doc.ocr_text or ""
                except ValueError:
                    pass

            if not extraction_text or not extraction_text.strip():
                raise ValueError("No tender text or document OCR text available for extraction")

            extractor = get_tender_requirement_extractor()
            candidates = extractor.extract_requirements(text=extraction_text, document_id=document_id)

            # Fetch existing count to sequence display_order and codes
            count_stmt = select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)
            existing_cnt = len(list(session.execute(count_stmt).scalars().all()))

            created_records: List[TenderRequirement] = []
            for idx, candidate in enumerate(candidates, start=1):
                # Build rule_config
                rule_config = []
                if candidate.rule_type and candidate.parameters:
                    rule_config = [{
                        "source": candidate.parameters.get("source", candidate.type),
                        "field": candidate.parameters.get("field", "status"),
                        "operator": candidate.parameters.get("operator", "EQUALS"),
                        "expected_value": candidate.parameters.get("expected_value", "ACTIVE"),
                    }]

                req = TenderRequirement(
                    id=uuid.uuid4(),
                    tender_id=t_uuid,
                    code=candidate.code or f"REQ-{candidate.type}-{existing_cnt + idx:03d}",
                    title=candidate.title,
                    description=candidate.description,
                    type=candidate.type,
                    mandatory=candidate.mandatory,
                    display_order=existing_cnt + idx,
                    status="AI_SUGGESTED",
                    rule_type=candidate.rule_type,
                    parameters=candidate.parameters,
                    rule_config=rule_config,
                    source_document_id=source_doc_uuid,
                    source_text=candidate.source_text,
                    source_page=candidate.source_page,
                    source_section=candidate.source_section,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(req)
                created_records.append(req)

            session.commit()
            for r in created_records:
                session.refresh(r)
            return created_records
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
                    status=item.get("status", "APPROVED"),
                    rule_type=item.get("rule_type"),
                    parameters=item.get("parameters"),
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

    def run_compliance_evaluation(
        self,
        tender_id: str,
        bidder_id: str,
        officer_id: Optional[str] = None,
        allow_empty: bool = False,
    ) -> ComplianceEvaluationRead:
        """Run complete deterministic statutory compliance evaluation for a bidder against tender requirements (Task 13).

        Strict Safety & Architecture Rules:
        1. Validates existence of Tender and Bidder.
        2. Strict Approval Gate: Evaluates ONLY requirements with status == 'APPROVED'.
           If zero approved requirements exist and not allow_empty, raises NoApprovedRequirementsError.
        3. Discovers multi-source evidence using EvidenceResolver (Government > AI > Document).
        4. Evaluates EVERY approved requirement in deterministic display_order; does NOT abort early on failure.
        5. Preserves evaluation history: Creates a brand-new ComplianceEvaluation record with unique UUID evaluation_id.
           NEVER overwrites, mutates, or deletes previous evaluation runs.
        6. NO automatic bidder approval, rejection, qualification, disqualification, or award scoring.
        """
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(str(tender_id))
            b_uuid = uuid.UUID(str(bidder_id))

            tender = session.get(Tender, t_uuid)
            if not tender:
                raise KeyError(f"Tender {tender_id} not found")

            bidder = session.get(Bidder, b_uuid)
            if not bidder:
                raise KeyError(f"Bidder {bidder_id} not found")

            # Check for approved requirements directly from database (do not auto-seed demo rules if empty)
            req_stmt = (
                select(TenderRequirement)
                .where(
                    TenderRequirement.tender_id == t_uuid,
                    TenderRequirement.status == "APPROVED",
                )
                .order_by(TenderRequirement.display_order.asc(), TenderRequirement.created_at.asc())
            )
            approved_requirements = list(session.execute(req_stmt).scalars().all())

            if not approved_requirements:
                if allow_empty:
                    existing_cnt = len(list(session.execute(select(TenderRequirement).where(TenderRequirement.tender_id == t_uuid)).scalars().all()))
                    if existing_cnt == 0:
                        approved_requirements = self.ensure_default_demo_requirements(str(t_uuid), session=session)
                if not approved_requirements and not allow_empty:
                    raise NoApprovedRequirementsError("No approved tender requirements are available for evaluation.")

            eval_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            eval_record = ComplianceEvaluation(
                id=eval_id,
                tender_id=t_uuid,
                bidder_id=b_uuid,
                status="PROCESSING",
                started_at=now,
            )
            session.add(eval_record)
            session.flush()


            # Resolve evidence via EvidenceResolver
            evidence_list, trace_map = EvidenceResolver.resolve_evidence_for_bidder(b_uuid, session)

            evaluation_reads: List[RequirementEvaluationRead] = []
            pass_cnt = 0
            fail_cnt = 0
            partial_cnt = 0
            not_verified_cnt = 0
            not_applicable_cnt = 0
            mandatory_failed_cnt = 0
            mandatory_not_verified_cnt = 0
            mandatory_total = 0
            mandatory_passed = 0
            optional_total = 0
            optional_passed = 0
            optional_failed = 0
            optional_not_verified = 0

            for req in approved_requirements:
                rule_config = req.rule_config or []
                if isinstance(rule_config, dict):
                    rule_config = [rule_config]

                eval_result = ComplianceEngine.evaluate_requirement(
                    requirement_code=req.code,
                    requirement_title=req.title,
                    rule_configs=rule_config,
                    evidence_list=evidence_list,
                )

                # Format enriched traceable evidence list for this requirement
                enriched_evidence: List[Dict[str, Any]] = []
                req_source = (req.type or "").strip().upper()

                # Check if specific rule configs define sources
                rule_sources = set()
                for rc in rule_config:
                    if isinstance(rc, dict) and rc.get("source"):
                        rule_sources.add(rc["source"].strip().upper())
                if not rule_sources and req_source:
                    rule_sources.add(req_source)

                for src in sorted(rule_sources):
                    if src in trace_map:
                        enriched_evidence.append(trace_map[src].to_dict())

                if not enriched_evidence:
                    # Fallback to evidence_used from ComplianceEngine
                    enriched_evidence = eval_result.evidence_used or []

                # Build explanation including any evidence conflict notes
                explanation = eval_result.explanation
                for src in rule_sources:
                    trace = trace_map.get(src)
                    if trace and trace.conflict_detected and trace.note:
                        if trace.note not in explanation:
                            explanation = f"{explanation}\n  - [AUDIT NOTE] {trace.note}"

                db_eval = RequirementEvaluation(
                    id=uuid.uuid4(),
                    evaluation_id=eval_id,
                    requirement_id=req.id,
                    bidder_id=b_uuid,
                    tender_id=t_uuid,
                    status=eval_result.status,
                    result={
                        "summary": eval_result.summary,
                        "explanation": explanation,
                    },
                    rule_results=[r.__dict__ for r in eval_result.rule_results],
                    evidence=enriched_evidence,
                    evaluated_at=now,
                )
                session.add(db_eval)

                # Count statistics
                status = eval_result.status
                is_mand = bool(req.mandatory)
                if is_mand:
                    mandatory_total += 1
                else:
                    optional_total += 1

                if status == "PASS":
                    pass_cnt += 1
                    if is_mand:
                        mandatory_passed += 1
                    else:
                        optional_passed += 1
                elif status == "FAIL":
                    fail_cnt += 1
                    if is_mand:
                        mandatory_failed_cnt += 1
                    else:
                        optional_failed += 1
                elif status == "PARTIAL":
                    partial_cnt += 1
                    if is_mand:
                        mandatory_failed_cnt += 1
                    else:
                        optional_failed += 1
                elif status == "NOT_VERIFIED":
                    not_verified_cnt += 1
                    if is_mand:
                        mandatory_not_verified_cnt += 1
                    else:
                        optional_not_verified += 1
                elif status == "NOT_APPLICABLE":
                    not_applicable_cnt += 1

                evaluation_reads.append(
                    RequirementEvaluationRead(
                        id=db_eval.id,
                        evaluation_id=eval_id,
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
                        evaluated_at=now.isoformat(),
                    )
                )

            summary_data = {
                "total_requirements": len(approved_requirements),
                "pass_count": pass_cnt,
                "fail_count": fail_cnt,
                "partial_count": partial_cnt,
                "not_verified_count": not_verified_cnt,
                "not_applicable_count": not_applicable_cnt,
                "mandatory_failed": mandatory_failed_cnt,
                "mandatory_not_verified": mandatory_not_verified_cnt,
                "mandatory_total": mandatory_total,
                "mandatory_passed": mandatory_passed,
                "optional_total": optional_total,
                "optional_passed": optional_passed,
                "optional_failed": optional_failed,
                "optional_not_verified": optional_not_verified,
            }

            eval_record.status = "COMPLETED"
            eval_record.summary = summary_data
            eval_record.completed_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(eval_record)

            try:
                get_audit_service(session).record_event(
                    action="COMPLIANCE_EVALUATION_EXECUTED",
                    entity_type="COMPLIANCE_EVALUATION",
                    entity_id=eval_record.id,
                    user_id=officer_id,
                    details={
                        "evaluation_id": str(eval_record.id),
                        "tender_id": str(t_uuid),
                        "bidder_id": str(b_uuid),
                        "summary": summary_data,
                        "requirements_count": len(approved_requirements),
                    },
                    session=session,
                )
            except Exception as audit_err:
                logger.warning("Failed to record audit event for compliance evaluation: %s", audit_err)

            summary_schema = ComplianceSummary(**summary_data)

            return ComplianceEvaluationRead(
                evaluation_id=eval_record.id,
                tender_id=t_uuid,
                bidder_id=b_uuid,
                bidder_legal_name=bidder.legal_name,
                tender_title=tender.title,
                status=eval_record.status,
                summary=summary_schema,
                requirements=evaluation_reads,
                started_at=eval_record.started_at.isoformat() if eval_record.started_at else None,
                completed_at=eval_record.completed_at.isoformat() if eval_record.completed_at else None,
                created_at=eval_record.created_at.isoformat() if eval_record.created_at else None,
                disclaimer=DEFAULT_COMPLIANCE_DISCLAIMER,
            )
        finally:
            if should_close:
                session.close()

    def get_compliance_evaluation(self, evaluation_id: str) -> Optional[ComplianceEvaluationRead]:
        """Retrieve a specific compliance evaluation run by its unique UUID."""
        session, should_close = self._get_session()
        try:
            eval_uuid = uuid.UUID(str(evaluation_id))
            eval_record = session.get(ComplianceEvaluation, eval_uuid)
            if not eval_record:
                return None

            tender = session.get(Tender, eval_record.tender_id)
            bidder = session.get(Bidder, eval_record.bidder_id)

            stmt = (
                select(RequirementEvaluation)
                .where(RequirementEvaluation.evaluation_id == eval_uuid)
            )
            req_evals = list(session.execute(stmt).scalars().all())

            req_map = {
                req.id: req
                for req in session.execute(
                    select(TenderRequirement).where(TenderRequirement.tender_id == eval_record.tender_id)
                ).scalars().all()
            }

            sorted_evals = sorted(
                req_evals,
                key=lambda x: (
                    getattr(req_map.get(x.requirement_id), "display_order", 999),
                    getattr(x, "evaluated_at", datetime.min),
                )
            )

            evaluation_reads: List[RequirementEvaluationRead] = []
            for ev in sorted_evals:
                req = req_map.get(ev.requirement_id)
                evaluation_reads.append(
                    RequirementEvaluationRead(
                        id=ev.id,
                        evaluation_id=eval_record.id,
                        requirement_id=ev.requirement_id,
                        bidder_id=ev.bidder_id,
                        tender_id=ev.tender_id,
                        requirement_code=req.code if req else "REQ",
                        requirement_title=req.title if req else "Requirement",
                        requirement_type=req.type if req else "GST",
                        mandatory=req.mandatory if req else True,
                        status=ev.status,
                        result=ev.result,
                        rule_results=ev.rule_results,
                        evidence=ev.evidence,
                        evaluated_at=ev.evaluated_at.isoformat() if ev.evaluated_at else None,
                    )
                )

            summary_dict = eval_record.summary or {}
            summary_schema = ComplianceSummary(**summary_dict)

            return ComplianceEvaluationRead(
                evaluation_id=eval_record.id,
                tender_id=eval_record.tender_id,
                bidder_id=eval_record.bidder_id,
                bidder_legal_name=bidder.legal_name if bidder else None,
                tender_title=tender.title if tender else None,
                status=eval_record.status,
                summary=summary_schema,
                requirements=evaluation_reads,
                started_at=eval_record.started_at.isoformat() if eval_record.started_at else None,
                completed_at=eval_record.completed_at.isoformat() if eval_record.completed_at else None,
                created_at=eval_record.created_at.isoformat() if eval_record.created_at else None,
                disclaimer=DEFAULT_COMPLIANCE_DISCLAIMER,
            )
        finally:
            if should_close:
                session.close()

    def get_compliance_evaluations_history(
        self, tender_id: str, bidder_id: str
    ) -> List[ComplianceEvaluationSummaryItem]:
        """Fetch audit history of all compliance evaluation runs for a bidder on a tender."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(str(tender_id))
            b_uuid = uuid.UUID(str(bidder_id))

            stmt = (
                select(ComplianceEvaluation)
                .where(
                    ComplianceEvaluation.tender_id == t_uuid,
                    ComplianceEvaluation.bidder_id == b_uuid,
                )
                .order_by(ComplianceEvaluation.started_at.desc(), ComplianceEvaluation.created_at.desc())
            )
            records = list(session.execute(stmt).scalars().all())
            return [
                ComplianceEvaluationSummaryItem(
                    evaluation_id=r.id,
                    tender_id=r.tender_id,
                    bidder_id=r.bidder_id,
                    status=r.status,
                    summary=r.summary,
                    created_at=r.created_at.isoformat() if r.created_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                )
                for r in records
            ]
        finally:
            if should_close:
                session.close()

    def evaluate_bidder_compliance(
        self, tender_id: str, bidder_id: str
    ) -> BidderComplianceResponse:
        """Run deterministic compliance evaluation for all approved requirements of a tender (Task 11 / Task 13)."""
        eval_read = self.run_compliance_evaluation(tender_id=tender_id, bidder_id=bidder_id, allow_empty=True)
        return BidderComplianceResponse(
            evaluation_id=str(eval_read.evaluation_id),
            tender_id=str(eval_read.tender_id),
            bidder_id=str(eval_read.bidder_id),
            bidder_legal_name=eval_read.bidder_legal_name,
            summary=eval_read.summary,
            requirements=eval_read.requirements,
            disclaimer=eval_read.disclaimer,
        )

    def get_bidder_compliance(
        self, tender_id: str, bidder_id: str
    ) -> BidderComplianceResponse:
        """Fetch latest compliance evaluation or run an initial evaluation if none exist."""
        session, should_close = self._get_session()
        try:
            t_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
            b_uuid = uuid.UUID(bidder_id) if isinstance(bidder_id, str) else bidder_id

            stmt = (
                select(ComplianceEvaluation)
                .where(
                    ComplianceEvaluation.tender_id == t_uuid,
                    ComplianceEvaluation.bidder_id == b_uuid,
                )
                .order_by(ComplianceEvaluation.created_at.desc())
            )
            latest_eval = session.execute(stmt).scalars().first()
            if not latest_eval:
                return self.evaluate_bidder_compliance(tender_id, bidder_id)

            eval_read = self.get_compliance_evaluation(str(latest_eval.id))
            if not eval_read:
                return self.evaluate_bidder_compliance(tender_id, bidder_id)

            return BidderComplianceResponse(
                evaluation_id=str(eval_read.evaluation_id),
                tender_id=str(eval_read.tender_id),
                bidder_id=str(eval_read.bidder_id),
                bidder_legal_name=eval_read.bidder_legal_name,
                summary=eval_read.summary,
                requirements=eval_read.requirements,
                disclaimer=eval_read.disclaimer,
            )
        finally:
            if should_close:
                session.close()

    def get_evaluation_evidence_traces(
        self, evaluation_id: str
    ) -> EvaluationEvidenceTraceResponse:
        """Fetch all evidence trace chains for a completed compliance evaluation run (Task 15).

        Returns requirement -> rule -> evidence -> document/OCR/AI/government trace chains.
        """
        session, should_close = self._get_session()
        try:
            eval_uuid = uuid.UUID(str(evaluation_id))
            eval_record = session.get(ComplianceEvaluation, eval_uuid)
            if not eval_record:
                raise KeyError(f"Compliance evaluation '{evaluation_id}' not found")

            # Load requirement evaluations
            stmt = (
                select(RequirementEvaluation)
                .where(RequirementEvaluation.evaluation_id == eval_uuid)
            )
            req_evals = list(session.execute(stmt).scalars().all())

            # Load requirements map
            req_map = {
                req.id: req
                for req in session.execute(
                    select(TenderRequirement).where(TenderRequirement.tender_id == eval_record.tender_id)
                ).scalars().all()
            }

            sorted_evals = sorted(
                req_evals,
                key=lambda x: (
                    getattr(req_map.get(x.requirement_id), "display_order", 999),
                    getattr(x, "evaluated_at", datetime.min),
                )
            )

            traces: List[EvidenceTraceChainRead] = []
            for ev in sorted_evals:
                req = req_map.get(ev.requirement_id)
                req_code = req.code if req else "REQ"
                req_title = req.title if req else "Requirement"

                rule_results = ev.rule_results or []
                evidence_items = ev.evidence or []

                # Resolve document and government traces
                doc_trace = None
                ocr_trace = None
                ai_trace = None
                gov_trace = None

                # Find any document_id or verification_id referenced in evidence
                doc_ids = [
                    e.get("document_id")
                    for e in evidence_items
                    if isinstance(e, dict) and e.get("document_id")
                ]
                gov_ids = [
                    e.get("verification_id")
                    for e in evidence_items
                    if isinstance(e, dict) and e.get("verification_id")
                ]

                if doc_ids:
                    try:
                        d_uuid = uuid.UUID(str(doc_ids[0]))
                        doc = session.get(Document, d_uuid)
                        if doc:
                            doc_trace = {
                                "document_id": str(doc.id),
                                "file_name": doc.file_name,
                                "document_type": doc.document_type,
                                "mime_type": doc.mime_type,
                                "file_size": doc.file_size,
                                "status": doc.status,
                                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                            }
                            ocr_trace = {
                                "status": doc.ocr_status,
                                "text": doc.ocr_text,
                                "error": doc.ocr_error,
                                "completed_at": doc.ocr_completed_at.isoformat() if doc.ocr_completed_at else None,
                            }
                            ai_trace = {
                                "status": doc.ai_status,
                                "model": doc.ai_model,
                                "extraction": doc.ai_extraction,
                                "error": doc.ai_error,
                                "completed_at": doc.ai_completed_at.isoformat() if doc.ai_completed_at else None,
                            }
                    except (ValueError, TypeError):
                        pass

                if gov_ids:
                    try:
                        g_uuid = uuid.UUID(str(gov_ids[0]))
                        gv = session.get(GovernmentVerification, g_uuid)
                        if gv:
                            gov_trace = {
                                "verification_id": str(gv.id),
                                "source": gv.source,
                                "identifier": gv.identifier,
                                "status": gv.status,
                                "verification_result": gv.verification_result,
                                "retrieved_at": gv.retrieved_at.isoformat() if gv.retrieved_at else None,
                                "government_data": gv.government_data or {},
                                "field_results": gv.field_results or {},
                            }
                    except (ValueError, TypeError):
                        pass

                trace_chain = ExplanationEngine.build_trace_chain(
                    requirement_id=str(ev.requirement_id),
                    requirement_code=req_code,
                    requirement_title=req_title,
                    evaluation_status=ev.status,
                    rule_results=rule_results,
                    evidence_items=evidence_items,
                    document_metadata=doc_trace,
                    ocr_trace=ocr_trace,
                    ai_trace=ai_trace,
                    government_trace=gov_trace,
                    evaluation_id=str(eval_record.id),
                )

                field_comparisons = ExplanationEngine.build_field_comparisons(
                    rule_configs=req.rule_config or [] if req else [],
                    rule_results=rule_results,
                    evidence_items=evidence_items,
                )

                norm_items_read: List[NormalizedEvidenceItemRead] = []
                for item in trace_chain.evidence_items:
                    norm_items_read.append(
                        NormalizedEvidenceItemRead(
                            evidence_id=item.evidence_id,
                            source_type=item.source_type,
                            source=item.source,
                            document_id=item.document_id,
                            verification_id=item.verification_id,
                            extraction_id=item.extraction_id,
                            field=item.field,
                            value=item.value,
                            expected_value=item.expected_value,
                            document_value=item.document_value,
                            government_value=item.government_value,
                            result=item.result,
                            retrieved_at=item.retrieved_at,
                            is_demo=item.is_demo,
                            verified=item.verified,
                            field_comparisons=[
                                FieldComparisonRead(
                                    field=fc.field,
                                    expected_value=fc.expected_value,
                                    document_value=fc.document_value,
                                    government_value=fc.government_value,
                                    result=fc.result,
                                )
                                for fc in field_comparisons
                            ],
                            raw_data=item.raw_data,
                            ai_extracted=item.ai_extracted,
                            conflict_detected=item.conflict_detected,
                            conflict_details=item.conflict_details,
                            explanation=item.explanation,
                            metadata=item.metadata,
                        )
                    )

                traces.append(
                    EvidenceTraceChainRead(
                        requirement_id=str(ev.requirement_id),
                        requirement_code=req_code,
                        requirement_title=req_title,
                        evaluation_id=str(eval_record.id),
                        evaluation_status=ev.status,
                        explanation=trace_chain.explanation,
                        rule_results=rule_results,
                        evidence_items=norm_items_read,
                        document_trace=doc_trace,
                        ocr_trace=ocr_trace,
                        ai_trace=ai_trace,
                        government_trace=gov_trace,
                    )
                )

            return EvaluationEvidenceTraceResponse(
                evaluation_id=eval_record.id,
                tender_id=eval_record.tender_id,
                bidder_id=eval_record.bidder_id,
                traces=traces,
            )
        finally:
            if should_close:
                session.close()

    def get_requirement_evidence_trace(
        self, requirement_id: str, bidder_id: Optional[str] = None
    ) -> Optional[EvidenceTraceChainRead]:
        """Fetch trace chain for a specific requirement's latest evaluation."""
        session, should_close = self._get_session()
        try:
            req_uuid = uuid.UUID(str(requirement_id))
            req = session.get(TenderRequirement, req_uuid)
            if not req:
                return None

            stmt = select(RequirementEvaluation).where(RequirementEvaluation.requirement_id == req_uuid)
            if bidder_id:
                try:
                    b_uuid = uuid.UUID(str(bidder_id))
                    stmt = stmt.where(RequirementEvaluation.bidder_id == b_uuid)
                except ValueError:
                    pass
            stmt = stmt.order_by(RequirementEvaluation.evaluated_at.desc())
            ev = session.execute(stmt).scalars().first()
            if not ev:
                trace_chain = ExplanationEngine.build_trace_chain(
                    requirement_id=str(req.id),
                    requirement_code=req.code,
                    requirement_title=req.title,
                    evaluation_status="NOT_VERIFIED",
                    rule_results=[],
                    evidence_items=[],
                )
                return EvidenceTraceChainRead(
                    requirement_id=str(req.id),
                    requirement_code=req.code,
                    requirement_title=req.title,
                    evaluation_status="NOT_VERIFIED",
                    explanation=trace_chain.explanation,
                    rule_results=[],
                    evidence_items=[],
                )

            if ev.evaluation_id:
                eval_traces = self.get_evaluation_evidence_traces(str(ev.evaluation_id))
                for t in eval_traces.traces:
                    if t.requirement_id == str(req.id):
                        return t

            return None
        finally:
            if should_close:
                session.close()
