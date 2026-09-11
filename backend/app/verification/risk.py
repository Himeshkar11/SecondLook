"""Risk assessment engine abstractions and deterministic demo classification.

This module categorizes compliance risk from score results and rule outcomes.
It does not contain pipeline orchestration, rule definitions, or scoring logic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.verification.rules import RuleEvaluationResult
from app.verification.scoring import ScoreResult


class RiskLevel(str, Enum):
    """Categorical risk classifications for verification outcomes."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskResult(BaseModel):
    """Normalized risk classification outcome."""

    risk_level: RiskLevel = Field(..., description="Assessed categorical risk level")
    score_percentage: float = Field(..., description="Normalized score used during assessment")
    factors: List[str] = Field(default_factory=list, description="Specific risk drivers or failed checks")
    summary: str = Field(..., description="Readable explanation of the assessed risk level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic risk metadata")


class RiskEngine:
    """Classifies risk deterministically using threshold boundaries.

    Demo Thresholds:
    - Score >= 80.0% -> LOW
    - 50.0% <= Score < 80.0% -> MEDIUM
    - Score < 50.0% or Critical Failures (Gov Status / Blacklist) -> HIGH
    """

    def __init__(
        self,
        low_risk_threshold: float = 80.0,
        medium_risk_threshold: float = 50.0,
    ) -> None:
        self.low_risk_threshold = low_risk_threshold
        self.medium_risk_threshold = medium_risk_threshold

    def assess(
        self,
        score_result: ScoreResult,
        rule_results: Optional[List[RuleEvaluationResult]] = None,
    ) -> RiskResult:
        """Classify risk level from score results and critical rule evaluations."""
        factors: List[str] = []
        critical_failure = False

        if rule_results:
            for r in rule_results:
                if not r.passed:
                    factors.append(f"{r.name}: {r.message}")
                    if r.rule_id == "RULE_GOV_STATUS":
                        critical_failure = True

        percentage = score_result.percentage

        if critical_failure or percentage < self.medium_risk_threshold:
            risk_level = RiskLevel.HIGH
            summary = (
                f"High risk: Critical verification checks failed or low compliance score ({percentage}%)."
            )
        elif percentage < self.low_risk_threshold:
            risk_level = RiskLevel.MEDIUM
            summary = (
                f"Medium risk: Compliance score ({percentage}%) indicates minor or secondary deficiencies."
            )
        else:
            risk_level = RiskLevel.LOW
            summary = (
                f"Low risk: Satisfactory compliance score ({percentage}%) across required checks."
            )

        return RiskResult(
            risk_level=risk_level,
            score_percentage=percentage,
            factors=factors,
            summary=summary,
            metadata={
                "low_risk_threshold": self.low_risk_threshold,
                "medium_risk_threshold": self.medium_risk_threshold,
                "critical_failure": critical_failure,
            },
        )
