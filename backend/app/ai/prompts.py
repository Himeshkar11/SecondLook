"""Versioned prompt templates for AI document extraction.

Prompts are kept separate from API routes, workers, database code, and
React components. Each prompt version is a named constant so that the
ai_prompt_version field stored in PostgreSQL can be traced back to the
exact instruction set that produced the extraction.

Rules enforced in every prompt:
- Return JSON only — no markdown, no explanation
- Use null for unavailable fields — never invent values
- Preserve identifiers exactly as they appear in the OCR text
- Normalize dates to YYYY-MM-DD where possible
- Extract ONLY information present in the provided OCR text
- Do NOT make compliance decisions, risk assessments, or eligibility judgments
"""

from __future__ import annotations

from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Versioned prompt constants
# ---------------------------------------------------------------------------

GST_EXTRACTION_PROMPT_V1 = """You are a document information extraction engine.

Extract the following fields from the raw OCR text of a GST Certificate.
Return ONLY a valid JSON object with exactly these keys. Do NOT add markdown fences, explanation, or commentary.

Required JSON keys:
- gstin (string or null): The GSTIN registration number exactly as it appears
- legal_name (string or null): The legal name of the registered entity
- trade_name (string or null): The trade name if different from legal name, else null
- registration_date (string or null): Registration date normalized to YYYY-MM-DD format; null if not present
- status (string or null): Registration status exactly as stated (e.g. ACTIVE, CANCELLED); null if not present
- address (string or null): Registered address as a single string; null if not present

Rules:
1. Return ONLY the JSON object. No markdown. No triple backticks. No explanation.
2. If a field is not present in the OCR text, set its value to null.
3. Do NOT invent or hallucinate values. Only extract information present in the text.
4. Preserve identifiers (GSTIN numbers, etc.) exactly character-for-character.
5. Do NOT make compliance decisions or eligibility assessments.
"""

PAN_EXTRACTION_PROMPT_V1 = """You are a document information extraction engine.

Extract the following fields from the raw OCR text of a PAN Card / Income Tax document.
Return ONLY a valid JSON object with exactly these keys. Do NOT add markdown fences, explanation, or commentary.

Required JSON keys:
- pan (string or null): The PAN (Permanent Account Number) exactly as it appears
- name (string or null): The name of the PAN holder exactly as stated
- date_of_birth_or_incorporation (string or null): Date of birth (individuals) or date of incorporation (entities), normalized to YYYY-MM-DD format; null if not present

Rules:
1. Return ONLY the JSON object. No markdown. No triple backticks. No explanation.
2. If a field is not present in the OCR text, set its value to null.
3. Do NOT invent or hallucinate values. Only extract information present in the text.
4. Preserve PAN numbers exactly character-for-character.
5. Do NOT make compliance decisions or eligibility assessments.
"""

UDYAM_EXTRACTION_PROMPT_V1 = """You are a document information extraction engine.

Extract the following fields from the raw OCR text of a UDYAM Registration Certificate.
Return ONLY a valid JSON object with exactly these keys. Do NOT add markdown fences, explanation, or commentary.

Required JSON keys:
- udyam_number (string or null): The UDYAM registration number (format: UDYAM-XX-00-0000000) exactly as it appears
- enterprise_name (string or null): The name of the registered enterprise exactly as stated
- enterprise_type (string or null): The enterprise classification (MICRO, SMALL, or MEDIUM); null if not present
- major_activity (string or null): The major activity of the enterprise (MANUFACTURING, SERVICES, or TRADING); null if not present

Rules:
1. Return ONLY the JSON object. No markdown. No triple backticks. No explanation.
2. If a field is not present in the OCR text, set its value to null.
3. Do NOT invent or hallucinate values. Only extract information present in the text.
4. Preserve UDYAM numbers exactly character-for-character.
5. Do NOT make compliance decisions or eligibility assessments.
"""

GENERAL_EXTRACTION_PROMPT_V1 = """You are a document information extraction engine.

Extract the most important identification fields from the provided raw OCR text.
Return ONLY a valid JSON object. Do NOT add markdown fences, explanation, or commentary.

Return any fields you can reliably identify, such as:
- document_type (string or null): Your best guess at document type
- primary_identifier (string or null): The main ID/registration number if present
- entity_name (string or null): The name of the entity/person if present
- date (string or null): Any significant date, normalized to YYYY-MM-DD; null if not present

Rules:
1. Return ONLY the JSON object. No markdown. No triple backticks. No explanation.
2. If a field is not present in the OCR text, set its value to null.
3. Do NOT invent or hallucinate values. Only extract information present in the text.
4. Do NOT make compliance decisions or eligibility assessments.
"""


# ---------------------------------------------------------------------------
# Prompt registry
# ---------------------------------------------------------------------------

PROMPT_REGISTRY: Dict[str, str] = {
    "GST_V1": GST_EXTRACTION_PROMPT_V1,
    "PAN_V1": PAN_EXTRACTION_PROMPT_V1,
    "UDYAM_V1": UDYAM_EXTRACTION_PROMPT_V1,
    "GENERAL_V1": GENERAL_EXTRACTION_PROMPT_V1,
}


def get_prompt(document_type: str, version: str = "V1") -> str:
    """Look up the versioned prompt for a document type.

    Args:
        document_type: e.g. "GST", "PAN", "UDYAM".
        version: Prompt version string, default "V1".

    Returns:
        Prompt string.
    """
    key = f"{document_type.upper()}_{version.upper()}"
    return PROMPT_REGISTRY.get(key, GENERAL_EXTRACTION_PROMPT_V1)


def get_prompt_version_key(document_type: str, version: str = "V1") -> str:
    """Return the prompt version key string for storage in PostgreSQL.

    Example: "GST_V1", "PAN_V1"
    """
    key = f"{document_type.upper()}_{version.upper()}"
    if key in PROMPT_REGISTRY:
        return key
    return "GENERAL_V1"


# ---------------------------------------------------------------------------
# Legacy compatibility: ExtractionPromptTemplate kept for existing tests
# ---------------------------------------------------------------------------

class ExtractionPromptTemplate:
    """Legacy prompt builder kept for backward compatibility with existing tests."""

    SYSTEM_INSTRUCTION = (
        "You are an expert document compliance extraction engine. "
        "Your task is to analyze the provided raw OCR text and extract structured "
        "information into a standard format without hallucinations. "
        "Only extract fields present in the text. Return fields such as document_type, "
        "document_number, legal_name, registration_status, and any other relevant attributes. "
        "Return ONLY valid JSON. No markdown. No explanation."
    )

    BASE_USER_TEMPLATE = (
        "Document Type: {expected_type}\n\n"
        "--- BEGIN RAW OCR TEXT ---\n"
        "{ocr_text}\n"
        "--- END RAW OCR TEXT ---\n\n"
        "Extract all available key compliance attributes in valid JSON format only."
    )

    @classmethod
    def build_prompt(cls, ocr_text: str, expected_type: Optional[str] = None) -> Dict[str, str]:
        """Build provider-neutral prompt dictionary with system instruction and user prompt."""
        return {
            "system": cls.SYSTEM_INSTRUCTION,
            "user": cls.BASE_USER_TEMPLATE.format(
                expected_type=expected_type or "General Compliance Document",
                ocr_text=ocr_text.strip(),
            ),
        }
