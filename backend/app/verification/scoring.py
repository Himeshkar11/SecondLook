"""Scoring engine abstractions and deterministic demo calculations.

This module computes compliance scores from rule evaluation results.
It does not contain pipeline orchestration, rule definitions, or risk thresholds.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from app.verification.rules import RuleEvaluationResult


class ScoreResult(BaseModel):
    """Normalized score calculation outcome."""

    score: float = Field(..., ge=0.0, description="Earned score points")
    max_score: float = Field(..., gt=0.0, description="Maximum possible score points")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Normalized score percentage (0-100)")
    passed_rules_count: int = Field(..., ge=0, description="Number of rules that passed")
    total_rules_count: int = Field(..., ge=0, description="Total number of evaluated rules")
    breakdown: Dict[str, Any] = Field(default_factory=dict, description="Per-rule point contributions")


class ScoringEngine:
    """Calculates deterministic compliance scores from evaluated rules.

    The demo algorithm assigns equal weight to each rule (e.g. 20.0 points each for 5 rules),
    summing up passed rules to yield a normalized percentage between 0.0 and 100.0.
    """

    def __init__(self, points_per_rule: float = 20.0) -> None:
        self.points_per_rule = points_per_rule

    def calculate(self, rule_results: List[RuleEvaluationResult]) -> ScoreResult:
        """Compute the aggregate score from rule evaluation outcomes."""
        total_rules = len(rule_results)
        if total_rules == 0:
            return ScoreResult(
                score=0.0,
                max_score=100.0,
                percentage=0.0,
                passed_rules_count=0,
                total_rules_count=0,
                breakdown={},
            )

        passed_rules = sum(1 for r in rule_results if r.passed)
        max_possible_score = float(total_rules * self.points_per_rule)
        earned_score = float(passed_rules * self.points_per_rule)
        percentage = round((earned_score / max_possible_score) * 100.0, 2)

        breakdown = {
            r.rule_id: {
                "name": r.name,
                "passed": r.passed,
                "points": self.points_per_rule if r.passed else 0.0,
                "max_points": self.points_per_rule,
            }
            for r in rule_results
        }

        return ScoreResult(
            score=earned_score,
            max_score=max_possible_score,
            percentage=percentage,
            passed_rules_count=passed_rules,
            total_rules_count=total_rules,
            breakdown=breakdown,
        )
