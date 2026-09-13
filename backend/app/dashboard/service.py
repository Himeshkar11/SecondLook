from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.dashboard.repository import DashboardRepository
from app.models.tender_requirement import ComplianceEvaluation, RequirementEvaluation


class DashboardService:
    def __init__(self, db):
        self.repository = DashboardRepository(db)

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

        rows = []
        attention_count = 0
        for bidder in tender.bidders:
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
                "total_bidders": len(tender.bidders),
                "evaluated": evaluated,
                "not_started": len(tender.bidders) - evaluated,
                "processing": processing,
                "completed": completed,
                "attention_required": attention_count,
                "reviews_completed": review_completed,
                "reviews_pending": max(len(tender.bidders) - review_completed, 0),
            },
            "bidders": rows,
            "requirement_issues": self._requirement_issues(tender.requirements, results),
        }

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
