import pytest

from app.ocr import DocumentInput, ExtractedText, OCRProcessor, DemoOCRProcessor
from app.ai import AIExtractor, DemoAIExtractor, StructuredDocumentData
from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse, IntegrationStatus
from app.integrations.pan import PANIntegration
from app.integrations.gst import GSTIntegration
from app.integrations.blacklist import BlacklistIntegration
from app.verification import (
    DocumentTypeRule,
    DocumentNumberRule,
    LegalNamePresentRule,
    GovernmentStatusRule,
    RegistrationStatusRule,
    RuleEvaluationResult,
    RulesEngine,
    ScoreResult,
    ScoringEngine,
    RiskLevel,
    RiskResult,
    RiskEngine,
    PipelineStage,
    VerificationPipeline,
    VerificationPipelineResult,
)


# ==================================================
# 1. Rules Engine Tests
# ==================================================

def test_rules_engine_passing_scenario():
    engine = RulesEngine()
    extracted = StructuredDocumentData(
        document_type="GST",
        document_number="27ABCDE1234F1Z5",
        legal_name="Demo Bidder Pvt Ltd",
        registration_status="ACTIVE",
    )
    gov_resp = IntegrationResponse(
        success=True,
        status=IntegrationStatus.VERIFIED.value,
        provider="GST",
    )

    results = engine.evaluate(extracted, gov_resp)
    assert len(results) == 5
    assert all(r.passed for r in results)


def test_rules_engine_failing_scenario():
    engine = RulesEngine()
    extracted = StructuredDocumentData(
        document_type="UNKNOWN",
        document_number=None,
        legal_name="",
        registration_status="CANCELLED",
    )
    gov_resp = IntegrationResponse(
        success=False,
        status=IntegrationStatus.NOT_FOUND.value,
        provider="GST",
    )

    results = engine.evaluate(extracted, gov_resp)
    assert len(results) == 5
    assert not any(r.passed for r in results)


# ==================================================
# 2. Scoring Engine Tests
# ==================================================

def test_scoring_engine_full_pass():
    scoring = ScoringEngine(points_per_rule=20.0)
    rule_results = [
        RuleEvaluationResult(rule_id=f"R{i}", name=f"Rule {i}", passed=True, message="OK")
        for i in range(5)
    ]
    score = scoring.calculate(rule_results)

    assert score.score == 100.0
    assert score.max_score == 100.0
    assert score.percentage == 100.0
    assert score.passed_rules_count == 5
    assert score.total_rules_count == 5


def test_scoring_engine_partial_pass():
    scoring = ScoringEngine(points_per_rule=20.0)
    rule_results = [
        RuleEvaluationResult(rule_id="R1", name="Rule 1", passed=True, message="OK"),
        RuleEvaluationResult(rule_id="R2", name="Rule 2", passed=True, message="OK"),
        RuleEvaluationResult(rule_id="R3", name="Rule 3", passed=False, message="Failed"),
        RuleEvaluationResult(rule_id="R4", name="Rule 4", passed=False, message="Failed"),
        RuleEvaluationResult(rule_id="R5", name="Rule 5", passed=False, message="Failed"),
    ]
    score = scoring.calculate(rule_results)

    assert score.score == 40.0
    assert score.max_score == 100.0
    assert score.percentage == 40.0
    assert score.passed_rules_count == 2
    assert score.total_rules_count == 5


def test_scoring_engine_empty_rules():
    scoring = ScoringEngine()
    score = scoring.calculate([])
    assert score.score == 0.0
    assert score.percentage == 0.0


# ==================================================
# 3. Risk Engine Tests
# ==================================================

def test_risk_engine_classifications():
    risk_engine = RiskEngine(low_risk_threshold=80.0, medium_risk_threshold=50.0)

    # Low risk
    score_high = ScoreResult(
        score=100.0,
        max_score=100.0,
        percentage=100.0,
        passed_rules_count=5,
        total_rules_count=5,
    )
    res_low = risk_engine.assess(score_high, [])
    assert res_low.risk_level == RiskLevel.LOW

    # Medium risk
    score_med = ScoreResult(
        score=60.0,
        max_score=100.0,
        percentage=60.0,
        passed_rules_count=3,
        total_rules_count=5,
    )
    res_med = risk_engine.assess(score_med, [])
    assert res_med.risk_level == RiskLevel.MEDIUM

    # High risk (score-based)
    score_low = ScoreResult(
        score=40.0,
        max_score=100.0,
        percentage=40.0,
        passed_rules_count=2,
        total_rules_count=5,
    )
    res_high = risk_engine.assess(score_low, [])
    assert res_high.risk_level == RiskLevel.HIGH


def test_risk_engine_critical_government_failure_triggers_high_risk():
    risk_engine = RiskEngine()
    score_med = ScoreResult(
        score=80.0,
        max_score=100.0,
        percentage=80.0,
        passed_rules_count=4,
        total_rules_count=5,
    )
    rule_results = [
        RuleEvaluationResult(
            rule_id="RULE_GOV_STATUS",
            name="Government Verification Status",
            passed=False,
            message="Blacklisted or not verified",
        )
    ]
    res = risk_engine.assess(score_med, rule_results)
    assert res.risk_level == RiskLevel.HIGH
    assert any("Government Verification Status" in f for f in res.factors)


# ==================================================
# 4. Pipeline End-to-End & Stage Tests
# ==================================================

def test_complete_verification_pipeline_success():
    """Verify Document -> OCR -> AI -> Integration -> Rules -> Score -> Risk -> Result."""
    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
        rules_engine=RulesEngine(),
        scoring_engine=ScoringEngine(),
        risk_engine=RiskEngine(),
    )

    doc = DocumentInput(
        document_id="doc-001",
        file_name="gst_certificate.pdf",
        metadata={"document_type": "gst"},
    )

    result = pipeline.run(doc, entity_id="bidder-001", document_id="doc-001")

    assert isinstance(result, VerificationPipelineResult)
    assert result.success is True
    assert result.stage == PipelineStage.COMPLETED
    assert result.extracted_text is not None
    assert "27ABCDE1234F1Z5" in result.extracted_text.text
    assert result.extracted_data is not None
    assert result.extracted_data.document_type == "GST"
    assert result.integration_response is not None
    assert result.score is not None
    assert result.score.percentage == 100.0
    assert result.risk is not None
    assert result.risk.risk_level == RiskLevel.LOW
    assert len(result.rule_results) == 5
    assert all(r.passed for r in result.rule_results)


def test_pipeline_ocr_failure_stops_pipeline():
    class FailingOCR(OCRProcessor):
        def process(self, document: DocumentInput) -> ExtractedText:
            raise RuntimeError("Corrupt image / unreadable document")

    pipeline = VerificationPipeline(
        ocr_processor=FailingOCR(),
        ai_extractor=DemoAIExtractor(),
        integration=GSTIntegration(),
    )

    doc = DocumentInput(file_name="bad.pdf")
    result = pipeline.run(doc, entity_id="bidder-001")

    assert result.success is False
    assert result.stage == PipelineStage.OCR
    assert "Corrupt image" in result.error
    assert result.extracted_data is None
    assert result.score is None


def test_pipeline_ai_failure_stops_pipeline():
    class FailingAI(AIExtractor):
        def extract(self, extracted_text: ExtractedText) -> StructuredDocumentData:
            raise ValueError("AI model parse failure")

    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=FailingAI(),
        integration=GSTIntegration(),
    )

    doc = DocumentInput(file_name="valid.pdf")
    result = pipeline.run(doc, entity_id="bidder-001")

    assert result.success is False
    assert result.stage == PipelineStage.AI_EXTRACTION
    assert "AI model parse failure" in result.error
    assert result.extracted_text is not None
    assert result.integration_response is None
    assert result.score is None


def test_pipeline_integration_failure_propagates_correctly():
    class UnavailableIntegration(GovernmentIntegration):
        name = "TEST_PROVIDER"
        def verify(self, request: IntegrationRequest) -> IntegrationResponse:
            raise RuntimeError("Provider service timeout")

    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=UnavailableIntegration(),
    )

    doc = DocumentInput(file_name="gst.pdf", metadata={"document_type": "gst"})
    result = pipeline.run(doc, entity_id="bidder-001")

    assert result.success is False
    assert result.stage == PipelineStage.INTEGRATION
    assert "Provider service timeout" in result.error


def test_pipeline_deterministic_output():
    pipeline = VerificationPipeline(
        ocr_processor=DemoOCRProcessor(),
        ai_extractor=DemoAIExtractor(),
        integration=PANIntegration(),
    )

    doc = DocumentInput(file_name="pan_card.pdf", metadata={"document_type": "pan"})
    res1 = pipeline.run(doc, entity_id="bidder-001")
    res2 = pipeline.run(doc, entity_id="bidder-001")

    assert res1.success == res2.success
    assert res1.score.percentage == res2.score.percentage
    assert res1.risk.risk_level == res2.risk.risk_level
    assert res1.extracted_data.document_number == res2.extracted_data.document_number
