"""Verification module package for SecondLook.

Exports the central VerificationPipeline, RulesEngine, ScoringEngine,
RiskEngine, and corresponding data models.
"""

from app.verification.rules import (
    Rule,
    RuleEvaluationResult,
    RulesEngine,
    DocumentTypeRule,
    DocumentNumberRule,
    LegalNamePresentRule,
    GovernmentStatusRule,
    RegistrationStatusRule,
)
from app.verification.scoring import (
    ScoreResult,
    ScoringEngine,
)
from app.verification.risk import (
    RiskLevel,
    RiskResult,
    RiskEngine,
)
from app.verification.pipeline import (
    PipelineStage,
    VerificationPipeline,
    VerificationPipelineResult,
)
from app.verification.compliance_engine import (
    ComplianceEngine,
    Evidence,
    RequirementResult,
    RuleResult,
)
from app.verification.evidence_resolver import (
    EvidenceResolver,
    ResolvedEvidenceTrace,
)

__all__ = [
    "Rule",
    "RuleEvaluationResult",
    "RulesEngine",
    "DocumentTypeRule",
    "DocumentNumberRule",
    "LegalNamePresentRule",
    "GovernmentStatusRule",
    "RegistrationStatusRule",
    "ScoreResult",
    "ScoringEngine",
    "RiskLevel",
    "RiskResult",
    "RiskEngine",
    "PipelineStage",
    "VerificationPipeline",
    "VerificationPipelineResult",
    "ComplianceEngine",
    "Evidence",
    "RuleResult",
    "RequirementResult",
    "EvidenceResolver",
    "ResolvedEvidenceTrace",
]
