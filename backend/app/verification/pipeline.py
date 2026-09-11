"""Central verification pipeline orchestrator.

Coordinates Document -> OCR -> AI Extraction -> Government Integration ->
Rules -> Scoring -> Risk stages via constructor dependency injection.

This orchestrator contains NO database queries, SQL, HTTP calls, OCR engine logic,
AI prompt/vendor code, rule definitions, scoring formulas, or risk threshold math.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ocr.processor import DocumentInput, ExtractedText, OCRProcessor
from app.ai.extractor import AIExtractor, StructuredDocumentData
from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse
from app.verification.rules import RuleEvaluationResult, RulesEngine
from app.verification.scoring import ScoreResult, ScoringEngine
from app.verification.risk import RiskEngine, RiskResult


class PipelineStage(str, Enum):
    """Execution stages of the verification pipeline."""

    INITIALIZED = "INITIALIZED"
    OCR = "OCR"
    AI_EXTRACTION = "AI_EXTRACTION"
    INTEGRATION = "INTEGRATION"
    RULES = "RULES"
    SCORING = "SCORING"
    RISK = "RISK"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VerificationPipelineResult(BaseModel):
    """Standardized composite result of the verification pipeline execution."""

    success: bool = Field(..., description="Whether the verification pipeline succeeded end-to-end")
    stage: PipelineStage = Field(..., description="Last completed or failed stage")
    extracted_text: Optional[ExtractedText] = Field(None, description="OCR text output")
    extracted_data: Optional[StructuredDocumentData] = Field(None, description="AI structured extraction")
    integration_response: Optional[IntegrationResponse] = Field(None, description="Statutory integration result")
    rule_results: List[RuleEvaluationResult] = Field(default_factory=list, description="Evaluated rules")
    score: Optional[ScoreResult] = Field(None, description="Scoring outcome")
    risk: Optional[RiskResult] = Field(None, description="Risk assessment outcome")
    error: Optional[str] = Field(None, description="Stage failure reason if execution aborted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Pipeline run metadata")


class VerificationPipeline:
    """Orchestrates the multi-stage verification workflow.

    Dependencies are injected via constructor, ensuring that demo and real
    implementations of OCR, AI, integrations, and engines can be swapped
    without changing pipeline coordination logic.
    """

    def __init__(
        self,
        ocr_processor: OCRProcessor,
        ai_extractor: AIExtractor,
        integration: GovernmentIntegration,
        rules_engine: Optional[RulesEngine] = None,
        scoring_engine: Optional[ScoringEngine] = None,
        risk_engine: Optional[RiskEngine] = None,
    ) -> None:
        self.ocr_processor = ocr_processor
        self.ai_extractor = ai_extractor
        self.integration = integration
        self.rules_engine = rules_engine if rules_engine is not None else RulesEngine()
        self.scoring_engine = scoring_engine if scoring_engine is not None else ScoringEngine()
        self.risk_engine = risk_engine if risk_engine is not None else RiskEngine()

    def run(
        self,
        document: DocumentInput,
        entity_id: str,
        document_id: Optional[str] = None,
        verification_type: str = "vendor-compliance",
    ) -> VerificationPipelineResult:
        """Execute the end-to-end verification pipeline on the input document."""
        current_stage = PipelineStage.INITIALIZED

        # 1. OCR Stage
        current_stage = PipelineStage.OCR
        try:
            extracted_text = self.ocr_processor.process(document)
            if not extracted_text or not extracted_text.text:
                return VerificationPipelineResult(
                    success=False,
                    stage=PipelineStage.OCR,
                    error="OCR stage failed: no text could be extracted from the document",
                    metadata={"document_id": document_id, "entity_id": entity_id},
                )
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.OCR,
                error=f"OCR stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 2. AI Extraction Stage
        current_stage = PipelineStage.AI_EXTRACTION
        try:
            extracted_data = self.ai_extractor.extract(extracted_text)
            if not extracted_data:
                return VerificationPipelineResult(
                    success=False,
                    stage=PipelineStage.AI_EXTRACTION,
                    extracted_text=extracted_text,
                    error="AI extraction stage failed: no structured data produced",
                    metadata={"document_id": document_id, "entity_id": entity_id},
                )
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.AI_EXTRACTION,
                extracted_text=extracted_text,
                error=f"AI extraction stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 3. Statutory Government Integration Verification
        current_stage = PipelineStage.INTEGRATION
        try:
            identifier = extracted_data.document_number or ""
            integration_req = IntegrationRequest(
                entity_type="bidder",
                entity_id=entity_id,
                document_id=document_id,
                provider=self.integration.name,
                payload={
                    "identifier": identifier,
                    "verification_type": verification_type,
                    "legal_name": extracted_data.legal_name,
                },
            )
            integration_resp = self.integration.verify(integration_req)
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.INTEGRATION,
                extracted_text=extracted_text,
                extracted_data=extracted_data,
                error=f"Integration verification stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 4. Rules Evaluation Stage
        current_stage = PipelineStage.RULES
        try:
            rule_results = self.rules_engine.evaluate(extracted_data, integration_resp)
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.RULES,
                extracted_text=extracted_text,
                extracted_data=extracted_data,
                integration_response=integration_resp,
                error=f"Rules evaluation stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 5. Scoring Stage
        current_stage = PipelineStage.SCORING
        try:
            score_result = self.scoring_engine.calculate(rule_results)
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.SCORING,
                extracted_text=extracted_text,
                extracted_data=extracted_data,
                integration_response=integration_resp,
                rule_results=rule_results,
                error=f"Scoring stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 6. Risk Assessment Stage
        current_stage = PipelineStage.RISK
        try:
            risk_result = self.risk_engine.assess(score_result, rule_results)
        except Exception as exc:
            return VerificationPipelineResult(
                success=False,
                stage=PipelineStage.RISK,
                extracted_text=extracted_text,
                extracted_data=extracted_data,
                integration_response=integration_resp,
                rule_results=rule_results,
                score=score_result,
                error=f"Risk assessment stage exception: {exc}",
                metadata={"document_id": document_id, "entity_id": entity_id},
            )

        # 7. Completed Result Construction
        return VerificationPipelineResult(
            success=True,
            stage=PipelineStage.COMPLETED,
            extracted_text=extracted_text,
            extracted_data=extracted_data,
            integration_response=integration_resp,
            rule_results=rule_results,
            score=score_result,
            risk=risk_result,
            error=None,
            metadata={
                "document_id": document_id,
                "entity_id": entity_id,
                "provider": self.integration.name,
                "verification_type": verification_type,
            },
        )
