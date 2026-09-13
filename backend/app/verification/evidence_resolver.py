"""Evidence Resolver for Multi-Source Statutory Compliance Pipeline (Task 13).

Discovers, resolves, normalizes, and prioritizes bidder evidence from multiple sources:
1. Statutory Government Verifications (from Task 10)
2. AI Extracted Document Data (from Task 09)
3. Submitted Bidder Documents (from Task 08)

Strict Evidence Priority:
    Government-verified evidence > AI extracted evidence > Raw document evidence

Key Safety & Audit Rules:
- When government verification exists and is verified, it takes precedence.
- AI extracted data is NEVER destroyed or overwritten; both are preserved in the audit trace.
- If AI extracted status is ACTIVE but Government status is CANCELLED, government status wins
  for compliance evaluation (producing FAIL), but both values are recorded in the trace.
- AI-only evidence (without completed government verification) is marked as unverified (`verified=False`).
  The deterministic ComplianceEngine evaluates such statutory requirements as NOT_VERIFIED.
- Purely deterministic; NO external network calls, NO LLM invocations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.government_verification import GovernmentVerification
from app.verification.compliance_engine import Evidence, normalize_text

logger = logging.getLogger(__name__)


class ResolvedEvidenceTrace:
    """Detailed audit trace container for an evidence item."""

    def __init__(
        self,
        source: str,
        identifier: Optional[str] = None,
        verified: bool = False,
        document_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        government_data: Optional[Dict[str, Any]] = None,
        ai_extracted_data: Optional[Dict[str, Any]] = None,
        conflict_detected: bool = False,
        conflict_details: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ):
        self.source = source
        self.identifier = identifier
        self.verified = verified
        self.document_id = document_id
        self.verification_id = verification_id
        self.government_data = government_data or {}
        self.ai_extracted_data = ai_extracted_data or {}
        self.conflict_detected = conflict_detected
        self.conflict_details = conflict_details
        self.note = note

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "source": self.source,
            "identifier": self.identifier,
            "verified": self.verified,
            "document_id": self.document_id,
            "verification_id": self.verification_id,
        }
        if self.government_data:
            d["government_data"] = self.government_data
        if self.ai_extracted_data:
            d["ai_extracted"] = self.ai_extracted_data
        if self.conflict_detected:
            d["conflict_detected"] = True
            if self.conflict_details:
                d["conflict_details"] = self.conflict_details
        if self.note:
            d["note"] = self.note
        return d


class EvidenceResolver:
    """Deterministic orchestrator for resolving multi-source bidder compliance evidence."""

    @classmethod
    def resolve_evidence_for_bidder(
        cls,
        bidder_id: uuid.UUID | str,
        session: Session,
    ) -> Tuple[List[Evidence], Dict[str, ResolvedEvidenceTrace]]:
        """Discover and resolve all available evidence items for a bidder.
        
        Returns:
            evidence_list: List of Evidence dataclasses ready for ComplianceEngine.
            trace_map: Dict of source -> ResolvedEvidenceTrace for rich persistence.
        """
        b_uuid = uuid.UUID(str(bidder_id))

        # 1. Fetch all documents for this bidder
        doc_stmt = select(Document).where(Document.bidder_id == b_uuid)
        documents = list(session.execute(doc_stmt).scalars().all())

        # Index documents by type (e.g., GST, PAN, DOCUMENT)
        docs_by_type: Dict[str, Document] = {}
        for doc in documents:
            dtype = (doc.document_type or "DOCUMENT").strip().upper()
            # If multiple of same type, take latest uploaded or AI-completed
            if dtype not in docs_by_type:
                docs_by_type[dtype] = doc
            else:
                existing = docs_by_type[dtype]
                if (doc.ai_status == "AI_COMPLETED" and existing.ai_status != "AI_COMPLETED") or (
                    (doc.created_at or 0) > (existing.created_at or 0)
                ):
                    docs_by_type[dtype] = doc

        # 2. Fetch all government verification records for this bidder
        gv_stmt = (
            select(GovernmentVerification)
            .where(GovernmentVerification.bidder_id == b_uuid)
            .order_by(GovernmentVerification.created_at.desc())
        )
        verifications = list(session.execute(gv_stmt).scalars().all())

        # Index latest government verification per source
        gvs_by_source: Dict[str, GovernmentVerification] = {}
        for gv in verifications:
            src = gv.source.strip().upper()
            if src in ("BLACKLISTING", "DEBARMENT"):
                src = "BLACKLIST"
            elif src == "MSME":
                src = "UDYAM"
            if src not in gvs_by_source:
                gvs_by_source[src] = gv

        # 3. Discover all relevant sources across documents and verifications
        all_sources = set(docs_by_type.keys()) | set(gvs_by_source.keys())

        evidence_list: List[Evidence] = []
        trace_map: Dict[str, ResolvedEvidenceTrace] = {}

        for source in sorted(all_sources):
            gv = gvs_by_source.get(source)
            doc = docs_by_type.get(source)

            ai_data: Dict[str, Any] = {}
            if doc and doc.ai_status == "AI_COMPLETED" and doc.ai_extraction:
                if isinstance(doc.ai_extraction, dict):
                    ai_data = dict(doc.ai_extraction)

            # SCENARIO 1: Government verification exists
            if gv is not None:
                is_verified = (
                    gv.status == "COMPLETED"
                    and gv.verification_result in ["MATCH", "VERIFIED", "CLEAR", "LISTED"]
                )
                gov_data = dict(gv.government_data or {})
                identifier = gv.identifier or ai_data.get("gstin") or ai_data.get("pan") or ai_data.get("document_number")
                doc_id = str(gv.document_id) if gv.document_id else (str(doc.id) if doc else None)

                # Detect potential evidence conflict between AI and Government
                conflict_detected = False
                conflict_details: Optional[Dict[str, Any]] = None
                conflict_note: Optional[str] = None

                if ai_data and gov_data:
                    # Check status conflict
                    ai_status = ai_data.get("status")
                    gov_status = gov_data.get("status")
                    if ai_status and gov_status and normalize_text(ai_status) != normalize_text(gov_status):
                        conflict_detected = True
                        conflict_details = {
                            "field": "status",
                            "ai_extracted": ai_status,
                            "government_verified": gov_status,
                        }
                        conflict_note = (
                            f"Evidence Conflict: AI extracted status '{ai_status}' differs from government "
                            f"verified status '{gov_status}'. Government record takes precedence."
                        )

                    # Check legal name conflict
                    ai_name = ai_data.get("legal_name") or ai_data.get("trade_name")
                    gov_name = gov_data.get("legal_name") or gov_data.get("trade_name")
                    if ai_name and gov_name and normalize_text(ai_name) != normalize_text(gov_name):
                        conflict_detected = True
                        if not conflict_details:
                            conflict_details = {
                                "field": "legal_name",
                                "ai_extracted": ai_name,
                                "government_verified": gov_name,
                            }
                            conflict_note = (
                                f"Government Mismatch: AI legal name '{ai_name}' differs from government "
                                f"record '{gov_name}'."
                            )

                # Primary evaluation data is government data (per Section 8 Evidence Priority)
                # Keep AI data attached as metadata for full auditability
                eval_data = dict(gov_data)
                eval_data["_ai_extracted"] = ai_data
                eval_data["_conflict_detected"] = conflict_detected
                if conflict_details:
                    eval_data["_conflict_details"] = conflict_details

                ev = Evidence(
                    source=source,
                    identifier=identifier,
                    verified=is_verified,
                    verification_id=str(gv.id),
                    document_id=doc_id,
                    data=eval_data,
                )
                evidence_list.append(ev)

                note = conflict_note
                if not note:
                    if is_verified:
                        note = f"Government verification confirmed {source} record."
                    elif gv.verification_result == "MISMATCH":
                        note = f"Government verification reported MISMATCH for {source} identifier."
                    else:
                        note = f"Government verification returned status {gv.verification_result or gv.status}."

                trace = ResolvedEvidenceTrace(
                    source=source,
                    identifier=identifier,
                    verified=is_verified,
                    document_id=doc_id,
                    verification_id=str(gv.id),
                    government_data=gov_data,
                    ai_extracted_data=ai_data,
                    conflict_detected=conflict_detected,
                    conflict_details=conflict_details,
                    note=note,
                )
                trace_map[source] = trace

            # SCENARIO 2: AI extraction exists without government verification (AI-Only Evidence)
            elif doc is not None and ai_data:
                identifier = ai_data.get("gstin") or ai_data.get("pan") or ai_data.get("document_number")
                doc_id = str(doc.id)

                ev = Evidence(
                    source=source,
                    identifier=identifier,
                    verified=False,  # Strictly unverified
                    verification_id=None,
                    document_id=doc_id,
                    data=ai_data,
                )
                evidence_list.append(ev)

                trace = ResolvedEvidenceTrace(
                    source=source,
                    identifier=identifier,
                    verified=False,
                    document_id=doc_id,
                    verification_id=None,
                    government_data={},
                    ai_extracted_data=ai_data,
                    conflict_detected=False,
                    note="Information was extracted from the submitted document, but required government verification is unavailable.",
                )
                trace_map[source] = trace

            # SCENARIO 3: Document uploaded but no AI extraction yet
            elif doc is not None:
                doc_id = str(doc.id)
                ev = Evidence(
                    source=source,
                    identifier=None,
                    verified=False,
                    verification_id=None,
                    document_id=doc_id,
                    data={"status": doc.status, "file_name": doc.file_name},
                )
                evidence_list.append(ev)

                trace = ResolvedEvidenceTrace(
                    source=source,
                    identifier=None,
                    verified=False,
                    document_id=doc_id,
                    verification_id=None,
                    government_data={},
                    ai_extracted_data={},
                    conflict_detected=False,
                    note=f"Document '{doc.file_name}' uploaded but extraction/verification is pending.",
                )
                trace_map[source] = trace

        return evidence_list, trace_map
