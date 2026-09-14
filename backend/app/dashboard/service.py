from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.dashboard.repository import DashboardRepository
from app.models.bid import Bid
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation, TenderRequirement
from app.review.models import OfficerReview, RequirementReview
from app.schemas.officer_dashboard import (
    OfficerAttentionItem,
    OfficerDashboardOverview,
    OfficerDashboardResponse,
    OfficerTenderRow,
)
from sqlalchemy import select
from uuid import UUID


class DashboardService:
    def __init__(self, db):
        self.repository = DashboardRepository(db)
        self.db = db

    def get_dashboard(self, tender_id: str) -> dict[str, Any]:
        tender = self.repository.get_tender(tender_id)
        if tender is None:
            raise KeyError(f"Tender with ID '{tender_id}' not found")

        evaluations = self.repository.get_evaluations(tender.id)
        results = self.repository.get_requirement_evaluations(tender.id)
        latest_by_bidder = self._latest_evaluations(evaluations)
        reviews = self.repository.get_reviews([item.id for item in evaluations])
        reviews_by_evaluation = {item.evaluation_id: item for item in reviews}
        requirement_reviews = self.repository.get_requirement_reviews([item.id for item in reviews])
        reviewed_by_evaluation = defaultdict(list)
        for item in requirement_reviews:
            review = next((candidate for candidate in reviews if candidate.id == item.review_id), None)
            if review:
                reviewed_by_evaluation[review.evaluation_id].append(item)

        # Collect all unique bidders participating via tender.bidders or tender.bids
        all_bidders_map = {b.id: b for b in tender.bidders}
        for b_item in getattr(tender, "bids", []):
            if getattr(b_item, "bidder", None):
                all_bidders_map[b_item.bidder.id] = b_item.bidder
        all_bidders = list(all_bidders_map.values())

        rows = []
        attention_count = 0
        for bidder in all_bidders:
            evaluation = latest_by_bidder.get(bidder.id)
            bidder_results = [item for item in results if evaluation and item.evaluation_id == evaluation.id]
            review = reviews_by_evaluation.get(evaluation.id) if evaluation else None
            row = self._bidder_row(bidder, evaluation, bidder_results, review, reviewed_by_evaluation)
            rows.append(row)
            attention_count += int(row["attention_required"])

        completed = sum(1 for item in latest_by_bidder.values() if item.status == "COMPLETED")
        processing = sum(1 for item in latest_by_bidder.values() if item.status == "PROCESSING")
        evaluated = len(latest_by_bidder)
        review_completed = sum(1 for item in reviews if item.status == "COMPLETED")
        return {
            "tender": self._tender_row(tender),
            "summary": {
                "total_bidders": len(all_bidders),
                "evaluated": evaluated,
                "not_started": len(all_bidders) - evaluated,
                "processing": processing,
                "completed": completed,
                "attention_required": attention_count,
                "reviews_completed": review_completed,
                "reviews_pending": max(len(all_bidders) - review_completed, 0),
            },
            "bidders": rows,
            "requirement_issues": self._requirement_issues(tender.requirements, results),
        }

    def get_officer_dashboard_overview(self, officer_user_id: UUID | None = None) -> OfficerDashboardResponse:
        """Single-pass batch operational aggregation for the officer home dashboard."""
        tenders = self.repository.get_all_tenders()
        tender_ids = [t.id for t in tenders]

        bids_by_tender = defaultdict(list)
        if tender_ids:
            all_bids = list(
                self.db.execute(
                    select(Bid).where(Bid.tender_id.in_(tender_ids))
                ).scalars().all()
            )
            for b in all_bids:
                bids_by_tender[b.tender_id].append(b)

        evals_by_tender = defaultdict(list)
        all_evals = []
        if tender_ids:
            all_evals = list(
                self.db.execute(
                    select(ComplianceEvaluation).where(ComplianceEvaluation.tender_id.in_(tender_ids))
                ).scalars().all()
            )
            for ev in all_evals:
                evals_by_tender[ev.tender_id].append(ev)

        eval_ids = [ev.id for ev in all_evals]
        reviews_by_eval = {}
        if eval_ids:
            all_reviews = list(
                self.db.execute(
                    select(OfficerReview).where(OfficerReview.evaluation_id.in_(eval_ids))
                ).scalars().all()
            )
            for rev in all_reviews:
                reviews_by_eval[rev.evaluation_id] = rev

        req_evals_by_eval = defaultdict(list)
        if eval_ids:
            all_req_evals = list(
                self.db.execute(
                    select(RequirementEvaluation).where(RequirementEvaluation.evaluation_id.in_(eval_ids))
                ).scalars().all()
            )
            for re in all_req_evals:
                req_evals_by_eval[re.evaluation_id].append(re)

        tender_rows: list[OfficerTenderRow] = []
        attention_items: list[OfficerAttentionItem] = []
        total_bids_received = sum(len(b_list) for b_list in bids_by_tender.values())
        active_tenders_count = 0
        evaluations_pending_count = 0

        for t in tenders:
            st = (t.status or "").upper()
            if st == "ACTIVE":
                active_tenders_count += 1

            bidders_map = {b.id: b.legal_name for b in t.bidders}
            for b_item in getattr(t, "bids", []):
                if getattr(b_item, "bidder", None):
                    bidders_map[b_item.bidder.id] = b_item.bidder.legal_name
            for b_rec in bids_by_tender.get(t.id, []):
                if getattr(b_rec, "bidder", None):
                    bidders_map[b_rec.bidder.id] = b_rec.bidder.legal_name

            bidders_count = len(bidders_map)
            bids_count = len(bids_by_tender.get(t.id, []))

            t_evals = evals_by_tender.get(t.id, [])
            latest_by_bidder = self._latest_evaluations(t_evals)
            evaluated_count = len(latest_by_bidder)
            evals_completed = sum(1 for e in latest_by_bidder.values() if e.status == "COMPLETED")
            evals_processing = sum(1 for e in latest_by_bidder.values() if e.status == "PROCESSING")
            evals_failed = sum(1 for e in latest_by_bidder.values() if e.status == "FAILED")
            evals_pending_tender = max(0, bidders_count - evals_completed)
            evaluations_pending_count += evals_pending_tender

            tender_reasons: list[str] = []

            # 1. Check unapproved requirements
            t_reqs = t.requirements or []
            unapproved_reqs = [r for r in t_reqs if (r.status or "").upper() in ("AI_SUGGESTED", "UNDER_REVIEW", "DRAFT")]
            if unapproved_reqs:
                tender_reasons.append(f"{len(unapproved_reqs)} requirement(s) awaiting approval")
                attention_items.append(
                    OfficerAttentionItem(
                        id=f"req-app-{t.id}",
                        type="REQUIREMENT_APPROVAL",
                        tender_id=str(t.id),
                        tender_title=t.title,
                        tender_reference=t.reference_number,
                        severity="warning",
                        message=f"{len(unapproved_reqs)} requirement(s) pending officer review for {t.title}",
                        action_url=f"/officer/tenders/{t.id}",
                        action_label="Review Requirements",
                        created_at=t.created_at.isoformat() if t.created_at else None,
                    )
                )

            # 2. Check processing evaluations
            if evals_processing > 0:
                tender_reasons.append(f"{evals_processing} evaluation(s) in progress")
                attention_items.append(
                    OfficerAttentionItem(
                        id=f"eval-proc-{t.id}",
                        type="EVALUATION_PROCESSING",
                        tender_id=str(t.id),
                        tender_title=t.title,
                        tender_reference=t.reference_number,
                        severity="info",
                        message=f"{evals_processing} compliance evaluation run(s) processing in background",
                        action_url=f"/officer/tenders/{t.id}/dashboard",
                        action_label="View Progress",
                        created_at=None,
                    )
                )

            # 3. Check failed evaluations
            if evals_failed > 0:
                tender_reasons.append(f"{evals_failed} evaluation failure(s)")
                attention_items.append(
                    OfficerAttentionItem(
                        id=f"eval-fail-{t.id}",
                        type="EVALUATION_FAILED",
                        tender_id=str(t.id),
                        tender_title=t.title,
                        tender_reference=t.reference_number,
                        severity="danger",
                        message=f"Compliance evaluation failed for {evals_failed} proposal(s)",
                        action_url=f"/officer/tenders/{t.id}/dashboard",
                        action_label="Inspect Failures",
                        created_at=None,
                    )
                )

            # 4. Check mandatory requirement failures & review pending decisions on completed evaluations
            for b_id, ev in latest_by_bidder.items():
                b_name = bidders_map.get(b_id, "Bidder")
                if ev.status == "COMPLETED":
                    ev_results = req_evals_by_eval.get(ev.id, [])
                    mandatory_requirement_ids = {
                        requirement.id for requirement in t_reqs if requirement.mandatory
                    }
                    mand_fails = sum(
                        1
                        for result in ev_results
                        if result.requirement_id in mandatory_requirement_ids
                        and result.status in ("FAIL", "PARTIAL", "NOT_VERIFIED")
                    )
                    if mand_fails > 0:
                        tender_reasons.append(f"Mandatory issue ({b_name})")
                        attention_items.append(
                            OfficerAttentionItem(
                                id=f"mand-issue-{ev.id}",
                                type="MANDATORY_ISSUE",
                                tender_id=str(t.id),
                                tender_title=t.title,
                                tender_reference=t.reference_number,
                                bidder_id=str(b_id),
                                bidder_name=b_name,
                                severity="danger",
                                message=f"Mandatory requirement issue detected for {b_name}",
                                action_url=f"/officer/bidders/{b_id}?tender_id={t.id}",
                                action_label="Inspect Bidder",
                                created_at=ev.completed_at.isoformat() if ev.completed_at else None,
                            )
                        )

                    rev = reviews_by_eval.get(ev.id)
                    if not rev or rev.status != "COMPLETED" or rev.decision in ("NO_DECISION", None):
                        tender_reasons.append(f"Review pending decision ({b_name})")
                        attention_items.append(
                            OfficerAttentionItem(
                                id=f"rev-pend-{ev.id}",
                                type="REVIEW_PENDING",
                                tender_id=str(t.id),
                                tender_title=t.title,
                                tender_reference=t.reference_number,
                                bidder_id=str(b_id),
                                bidder_name=b_name,
                                severity="warning",
                                message=f"Officer review awaiting qualification decision for {b_name}",
                                action_url=f"/officer/bidders/{b_id}?tender_id={t.id}",
                                action_label="Resume Review",
                                created_at=ev.completed_at.isoformat() if ev.completed_at else None,
                            )
                        )

            unique_reasons = sorted(list(set(tender_reasons)))
            tender_rows.append(
                OfficerTenderRow(
                    id=str(t.id),
                    reference_number=t.reference_number,
                    title=t.title,
                    status=t.status,
                    bidders_count=bidders_count,
                    bids_count=bids_count,
                    evaluated_count=evaluated_count,
                    evaluations_completed=evals_completed,
                    evaluations_processing=evals_processing,
                    attention_required=bool(unique_reasons),
                    attention_reasons=unique_reasons,
                    created_at=t.created_at.isoformat() if t.created_at else None,
                    updated_at=t.updated_at.isoformat() if t.updated_at else None,
                )
            )

        overview = OfficerDashboardOverview(
            active_tenders=active_tenders_count,
            total_tenders=len(tenders),
            bids_received=total_bids_received,
            evaluations_pending=evaluations_pending_count,
            reviews_requiring_attention=len(attention_items),
        )

        return OfficerDashboardResponse(
            overview=overview,
            tenders=tender_rows,
            attention_items=attention_items,
        )


    def get_requirement_dashboard(self, tender_id: str) -> list[dict[str, Any]]:
        payload = self.get_dashboard(tender_id)
        return payload["requirement_issues"]

    @staticmethod
    def _latest_evaluations(evaluations):
        latest = {}
        for item in evaluations:
            current = latest.get(item.bidder_id)
            if current is None or (item.created_at or item.started_at) > (current.created_at or current.started_at):
                latest[item.bidder_id] = item
        return latest

    @staticmethod
    def _tender_row(tender):
        return {"id": str(tender.id), "reference_number": tender.reference_number, "title": tender.title,
                "description": tender.description, "status": tender.status,
                "created_at": tender.created_at.isoformat() if tender.created_at else None,
                "updated_at": tender.updated_at.isoformat() if tender.updated_at else None}

    @staticmethod
    def _bidder_row(bidder, evaluation, results, review, reviewed_by_evaluation):
        counts = {key: sum(1 for item in results if item.status == key)
                  for key in ("PASS", "FAIL", "PARTIAL", "NOT_VERIFIED", "NOT_APPLICABLE")}
        applicable = counts["PASS"] + counts["FAIL"] + counts["PARTIAL"] + counts["NOT_VERIFIED"]
        percentage = round(counts["PASS"] * 100 / applicable, 2) if applicable else 0.0
        reasons = []
        if counts["FAIL"]: reasons.append("FAILED requirement")
        if counts["PARTIAL"]: reasons.append("PARTIAL requirement")
        if counts["NOT_VERIFIED"]: reasons.append("mandatory NOT_VERIFIED requirement")
        if review and review.status != "COMPLETED": reasons.append("incomplete officer review")
        return {"bidder_id": str(bidder.id), "bidder_name": bidder.legal_name,
                "evaluation_status": evaluation.status if evaluation else "NOT_STARTED",
                "total_requirements": len(results), "passed": counts["PASS"], "failed": counts["FAIL"],
                "partial": counts["PARTIAL"], "not_verified": counts["NOT_VERIFIED"],
                "not_applicable": counts["NOT_APPLICABLE"], "compliance_percentage": percentage,
                "review_status": review.status if review else "NOT_STARTED",
                "officer_decision": review.decision if review else "NO_DECISION",
                "attention_required": bool(reasons), "attention_reasons": reasons}

    @staticmethod
    def _requirement_issues(requirements, results):
        grouped = defaultdict(list)
        for item in results: grouped[item.requirement_id].append(item.status)
        rows = []
        for requirement in requirements:
            statuses = grouped[requirement.id]
            rows.append({"requirement_id": str(requirement.id), "title": requirement.title, "total": len(statuses),
                         "passed": statuses.count("PASS"), "failed": statuses.count("FAIL"),
                         "partial": statuses.count("PARTIAL"), "not_verified": statuses.count("NOT_VERIFIED"),
                         "not_applicable": statuses.count("NOT_APPLICABLE")})
        return rows
