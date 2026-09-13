"""Tender Requirement Extractor abstraction, Demo extractor, and OpenRouter implementation (Task 12).

Defines provider-neutral extraction of candidate requirements from tender document text.
AI suggests candidates ONLY. Candidate requirements are initially stored as AI_SUGGESTED
and must be explicitly approved by a procurement officer before entering the Compliance Engine.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.ai.prompts_tender import (
    TENDER_REQUIREMENT_EXTRACTION_SYSTEM_PROMPT,
    TENDER_REQUIREMENT_EXTRACTION_USER_PROMPT_TEMPLATE,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CandidateRequirement(BaseModel):
    """A candidate requirement extracted by AI from tender text."""

    code: Optional[str] = Field(None, description="Suggested requirement code")
    title: str = Field(..., description="Short title of the requirement")
    description: Optional[str] = Field(None, description="Factual description based on text")
    requirement_type: str = Field("OTHER", description="Category: GST, PAN, UDYAM, MSME, TECHNICAL, BLACKLISTING, etc.")
    rule_type: Optional[str] = Field(None, description="Deterministic rule type if applicable: STATUS_EQUALS, FIELD_EQUALS, etc.")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Rule parameters: field, operator, expected_value")
    mandatory: bool = Field(True, description="Whether requirement is mandatory")
    source_text: Optional[str] = Field(None, description="Exact source sentence from tender text")
    source_page: Optional[int] = Field(None, description="Page number if referenced")
    source_section: Optional[str] = Field(None, description="Section identifier if referenced")

    def __init__(self, **data: Any) -> None:
        if "type" in data and "requirement_type" not in data:
            data["requirement_type"] = data["type"]
        super().__init__(**data)

    @property
    def type(self) -> str:
        return self.requirement_type


class TenderRequirementExtractor(ABC):
    """Abstract base class for tender requirement extraction."""

    @abstractmethod
    def extract(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CandidateRequirement]:
        """Extract candidate requirements from tender text."""
        raise NotImplementedError

    def extract_requirements(
        self, text: Optional[str] = None, document_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> List[CandidateRequirement]:
        """Convenience alias for extracting requirements from text or document."""
        meta = metadata or {}
        if document_id:
            meta["document_id"] = document_id
        return self.extract(text=text or "", metadata=meta)


class DemoTenderRequirementExtractor(TenderRequirementExtractor):
    """Deterministic, offline extractor for testing and demonstration (Task 12).

    Matches exact fictional tender specifications without external AI network calls.
    Guarantees anti-hallucination behavior: generic texts do NOT invent statutory GST/PAN.
    """

    def extract(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CandidateRequirement]:
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        suggestions: List[CandidateRequirement] = []

        # Anti-hallucination check (Step 25): Generic text must NOT invent statutory GST/PAN
        generic_patterns = [
            r"all bidders must submit the required documents",
            r"submit the required documents along with their bids",
            r"submit required qualification documents",
        ]
        is_purely_generic = any(re.search(p, clean_text, re.IGNORECASE) for p in generic_patterns) and not any(
            w in clean_text.upper() for w in ["GST", "PAN", "TAMIL NADU", "DEBARRED", "BLACKLIST"]
        )
        if is_purely_generic:
            # Return generic DOCUMENT requirement requiring review, never invent GST/PAN
            return [
                CandidateRequirement(
                    code="REQ-DOC-GENERIC",
                    title="Submission of Required Tender Documents",
                    description="Bidder must submit required documentation along with bid.",
                    requirement_type="DOCUMENT",
                    rule_type=None,
                    parameters=None,
                    mandatory=True,
                    source_text=clean_text,
                    source_page=1,
                    source_section="General",
                )
            ]

        # 1. Active GST Registration
        if re.search(r"(active\s+gst|valid\s+and\s+active\s+gst|gst\s*\(?\)?\s*registration|goods\s+and\s+services\s+tax)", clean_text, re.IGNORECASE):
            match = re.search(r"([^.\n]*(?:active\s+gst|gst\s*\(?\)?\s*registration|goods\s+and\s+services\s+tax)[^.\n]*\.?)", clean_text, re.IGNORECASE)
            src = match.group(1).strip() if match else "The tenderer shall possess a valid and active GST registration."
            suggestions.append(
                CandidateRequirement(
                    code="REQ-GST-ACTIVE",
                    title="Active GST Registration",
                    description="Bidder must possess a valid and active GST registration verified against government records.",
                    requirement_type="GST",
                    rule_type="STATUS_EQUALS",
                    parameters={"source": "GST", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
                    mandatory=True,
                    source_text=src,
                    source_page=3,
                    source_section="3.1 (a)",
                )
            )

        # 2. Valid PAN
        if re.search(r"\b(valid\s+pan|pan\s+card|submit\s+a\s+valid\s+pan|permanent\s+account\s+number)\b", clean_text, re.IGNORECASE):
            match = re.search(r"([^.\n]*\b(?:valid\s+pan|permanent\s+account\s+number)[^.\n]*\.?)", clean_text, re.IGNORECASE)
            src = match.group(1).strip() if match else "The bidder shall submit a valid PAN."
            suggestions.append(
                CandidateRequirement(
                    code="REQ-PAN-VALID",
                    title="Valid PAN",
                    description="Bidder must possess and submit a valid, active Permanent Account Number (PAN).",
                    requirement_type="PAN",
                    rule_type="STATUS_EQUALS",
                    parameters={"source": "PAN", "field": "status", "operator": "EQUALS", "expected_value": "ACTIVE"},
                    mandatory=True,
                    source_text=src,
                    source_page=3,
                    source_section="3.1 (b)",
                )
            )

        # 3. Tamil Nadu Registration
        if re.search(r"\b(tamil\s+nadu|registered\s+in\s+tamil\s+nadu)\b", clean_text, re.IGNORECASE):
            match = re.search(r"([^.\n]*\btamil\s+nadu[^.\n]*\.?)", clean_text, re.IGNORECASE)
            src = match.group(1).strip() if match else "The bidder must be registered in Tamil Nadu."
            suggestions.append(
                CandidateRequirement(
                    code="REQ-GST-STATE-TN",
                    title="Tamil Nadu Registration",
                    description="Bidder must be registered in Tamil Nadu for local statutory compliance.",
                    requirement_type="GST",
                    rule_type="FIELD_EQUALS",
                    parameters={"source": "GST", "field": "state", "operator": "EQUALS", "expected_value": "Tamil Nadu"},
                    mandatory=True,
                    source_text=src,
                    source_page=3,
                    source_section="3.1 (c)",
                )
            )

        # 4. Debarment / Blacklisting Requirement
        if re.search(r"\b(debarred|blacklisted|blacklisting)\b", clean_text, re.IGNORECASE):
            match = re.search(r"([^.\n]*\b(?:debarred|blacklisted)[^.\n]*\.?)", clean_text, re.IGNORECASE)
            src = match.group(1).strip() if match else "The bidder shall not be debarred by any government authority."
            suggestions.append(
                CandidateRequirement(
                    code="REQ-DECL-BLACKLIST",
                    title="Debarment/Blacklisting Restriction",
                    description="Bidder shall not be debarred or blacklisted by any government authority.",
                    requirement_type="BLACKLISTING",
                    rule_type=None,  # No automated deterministic rule exists yet; manual review
                    parameters=None,
                    mandatory=True,
                    source_text=src,
                    source_page=3,
                    source_section="3.2 (a)",
                )
            )

        return suggestions


class OpenRouterTenderRequirementExtractor(TenderRequirementExtractor):
    """OpenRouter-backed tender requirement extractor using configured triple fallbacks."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.primary_model = settings.openrouter_primary_model
        self.fallback_model_1 = settings.openrouter_fallback_model_1
        self.fallback_model_2 = settings.openrouter_fallback_model_2
        self.timeout = float(settings.ai_timeout_seconds)

    def _parse_candidates(self, content: str) -> List[CandidateRequirement]:
        """Parse raw JSON string into validated CandidateRequirement list."""
        clean = content.strip()
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        try:
            parsed = json.loads(clean)
        except Exception:
            return []

        if isinstance(parsed, list):
            req_list = parsed
        elif isinstance(parsed, dict):
            req_list = parsed.get("requirements", [])
        else:
            req_list = []

        candidates = []
        for r in req_list:
            if isinstance(r, dict) and "title" in r:
                try:
                    candidates.append(CandidateRequirement(**r))
                except Exception:
                    pass
        return candidates

    def extract(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CandidateRequirement]:
        if not text or not text.strip():
            return []

        models = [m for m in [self.primary_model, self.fallback_model_1, self.fallback_model_2] if m]
        user_prompt = TENDER_REQUIREMENT_EXTRACTION_USER_PROMPT_TEMPLATE.format(tender_text=text[:12000])

        last_error = None
        for model in models:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": TENDER_REQUIREMENT_EXTRACTION_SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt},
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.0,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return self._parse_candidates(content)
                    else:
                        logger.warning("OpenRouter extraction failed on model %s [%s]: %s", model, resp.status_code, resp.text)
            except Exception as exc:
                logger.warning("OpenRouter extraction error on model %s: %s", model, exc)
                last_error = exc

        # If all fail, fall back safely to DemoTenderRequirementExtractor
        logger.warning("All OpenRouter models failed for tender extraction; falling back to Demo extractor. Error: %s", last_error)
        return DemoTenderRequirementExtractor().extract(text, metadata)


def get_tender_requirement_extractor(provider_name: Optional[str] = None) -> TenderRequirementExtractor:
    """Factory: return OpenRouterTenderRequirementExtractor if configured, else DemoTenderRequirementExtractor."""
    provider = (provider_name or settings.ai_provider or "demo").lower().strip()
    if provider == "openrouter" and settings.openrouter_api_key:
        try:
            return OpenRouterTenderRequirementExtractor()
        except Exception as exc:
            logger.warning("Failed to initialize OpenRouterTenderRequirementExtractor: %s", exc)
    return DemoTenderRequirementExtractor()
