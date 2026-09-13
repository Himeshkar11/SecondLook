"""OpenRouter AI provider implementation.

Implements AIExtractor using OpenRouter's chat completion API with a
TRIPLE FALLBACK mechanism:

    PRIMARY_MODEL → failure → FALLBACK_MODEL_1 → failure → FALLBACK_MODEL_2 → failure → AIExtractionError

Retryable failures (move to next model):
- httpx.TimeoutException
- httpx.ConnectError / httpx.NetworkError
- HTTP 429 (rate limit)
- HTTP 502 / 503 (provider unavailable)

Non-retryable failures (immediately raise, no fallback):
- Empty OCR text (AIEmptyOCRError)
- JSON parse failure (AIExtractionError)
- Pydantic schema validation failure (AIExtractionError)

Security:
- Only ocr_text and document_type are sent to the API. Never PDF binary, never
  Supabase credentials, never application secrets.
- API key is read from settings at runtime — never hard-coded.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import ValidationError

from app.ai.extractor import (
    AIEmptyOCRError,
    AIExtractionError,
    AIExtractor,
    AIProviderRetryableError,
    StructuredDocumentData,
)
from app.ai.prompts import get_prompt, get_prompt_version_key
from app.ai.schemas import get_schema_for_document_type

logger = logging.getLogger(__name__)


class OpenRouterAIExtractor(AIExtractor):
    """AI extractor backed by OpenRouter with triple-model fallback.

    Configuration is read from app.config.settings at construction time:
        - openrouter_api_key
        - openrouter_base_url (default: https://openrouter.ai/api/v1)
        - openrouter_primary_model
        - openrouter_fallback_model_1
        - openrouter_fallback_model_2
        - ai_timeout_seconds
        - ai_max_retries (max attempts per model — NOT used for model fallback logic)

    No credentials appear in this file. All are read from environment config.
    """

    def __init__(self, http_client: Optional[httpx.Client] = None) -> None:
        from app.config.settings import settings
        self._api_key = settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._timeout = float(settings.ai_timeout_seconds)
        self._primary = settings.openrouter_primary_model
        self._fallback1 = settings.openrouter_fallback_model_1
        self._fallback2 = settings.openrouter_fallback_model_2
        self._http_client = http_client

    def _model_list(self) -> List[str]:
        """Return ordered list of models to try (primary first)."""
        models = []
        for m in [self._primary, self._fallback1, self._fallback2]:
            if m and m.strip():
                models.append(m.strip())
        if not models:
            raise AIExtractionError(
                "No OpenRouter models configured. Set OPENROUTER_PRIMARY_MODEL in environment."
            )
        return models

    def _build_messages(self, document_type: str, ocr_text: str) -> List[Dict[str, str]]:
        """Build the chat messages payload. Only sends document_type + ocr_text."""
        system_prompt = get_prompt(document_type)
        user_content = (
            f"Document Type: {document_type}\n\n"
            f"--- BEGIN RAW OCR TEXT ---\n{ocr_text.strip()}\n--- END RAW OCR TEXT ---"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def _call_model(self, model: str, messages: List[Dict[str, str]]) -> str:
        """Call one OpenRouter model. Returns raw response text.

        Raises:
            AIProviderRetryableError: On timeout, connection failure, 429, 502, 503.
            AIExtractionError: On 4xx errors (excluding 429).
        """
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://secondlook.app",
            "X-Title": "SecondLook Document Extraction",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.0,
        }

        try:
            if self._http_client is not None:
                res = self._http_client.post(url, headers=headers, json=payload, timeout=self._timeout)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    res = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIProviderRetryableError(f"OpenRouter model '{model}' timed out: {exc}") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise AIProviderRetryableError(f"OpenRouter model '{model}' connection failed: {exc}") from exc

        if res.status_code in (429, 502, 503, 504) or res.status_code >= 500:
            raise AIProviderRetryableError(
                f"OpenRouter model '{model}' returned retryable HTTP {res.status_code}"
            )
        if res.status_code != 200:
            raise AIExtractionError(
                f"OpenRouter model '{model}' returned non-retryable HTTP {res.status_code}"
            )

        try:
            data = res.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIExtractionError(
                f"OpenRouter model '{model}' returned unexpected response structure: {exc}"
            ) from exc

    def _parse_and_validate(
        self,
        raw_content: str,
        document_type: str,
        model: str,
    ) -> StructuredDocumentData:
        """Parse JSON response and validate against document-specific schema.

        Raises:
            AIExtractionError: On JSON parse failure or schema validation failure.
        """
        # Strip any accidental markdown fencing
        content = raw_content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        # Parse JSON — non-retryable on failure
        try:
            parsed: Dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIExtractionError(
                f"AI model returned malformed JSON (non-retryable): {exc}\nRaw: {raw_content[:200]}"
            ) from exc

        # Schema validation
        schema_cls = get_schema_for_document_type(document_type)
        prompt_version = get_prompt_version_key(document_type)

        if schema_cls is not None:
            try:
                validated = schema_cls.model_validate(parsed)
                fields = validated.model_dump()
            except ValidationError as exc:
                raise AIExtractionError(
                    f"AI extraction schema validation failed for {document_type}: {exc}"
                ) from exc
        else:
            fields = parsed

        # Top-level convenience accessors
        doc_number = (
            fields.get("gstin")
            or fields.get("pan")
            or fields.get("udyam_number")
            or fields.get("primary_identifier")
        )
        legal_name = (
            fields.get("legal_name")
            or fields.get("name")
            or fields.get("enterprise_name")
            or fields.get("entity_name")
        )
        reg_status = fields.get("status")

        # Build StructuredDocumentData from validated fields
        return StructuredDocumentData(
            document_type=document_type,
            document_number=doc_number,
            legal_name=legal_name,
            registration_status=reg_status,
            fields=fields,
            confidence=None,
            ai_model=model,
            prompt_version=prompt_version,
            metadata={"source": "openrouter", "model": model},
        )

    def extract(
        self,
        document_type_or_extracted_text: Any,
        ocr_text: Optional[str] = None,
    ) -> StructuredDocumentData:
        """Extract structured information using OpenRouter with triple fallback.

        Args:
            document_type_or_extracted_text: e.g. "GST", "PAN", "UDYAM", or ExtractedText.
            ocr_text: Raw OCR text. Required if document_type string is passed.

        Returns:
            StructuredDocumentData from the first successful model.

        Raises:
            AIEmptyOCRError: If ocr_text is empty (non-retryable, no API call made).
            AIExtractionError: If all models fail or non-retryable failure occurs.
        """
        # Unpack arguments for backward and forward compatibility
        if ocr_text is None:
            if hasattr(document_type_or_extracted_text, "text"):
                text = document_type_or_extracted_text.text or ""
                metadata = getattr(document_type_or_extracted_text, "metadata", {}) or {}
                document_type = metadata.get("document_type") or "OTHER"
            else:
                text = str(document_type_or_extracted_text or "")
                document_type = "OTHER"
        else:
            document_type = str(document_type_or_extracted_text or "OTHER")
            text = ocr_text or ""

        # Pre-flight: empty OCR check — never call API with empty text
        if not text or not text.strip():
            raise AIEmptyOCRError("AI extraction skipped because OCR text is empty.")

        models = self._model_list()
        messages = self._build_messages(document_type, text)
        last_error: Optional[Exception] = None

        for idx, model in enumerate(models):
            label = ["PRIMARY", "FALLBACK_1", "FALLBACK_2"][min(idx, 2)]
            logger.info("Attempting AI extraction with %s model: %s", label, model)

            try:
                raw_content = self._call_model(model, messages)
                result = self._parse_and_validate(raw_content, document_type, model)
                logger.info("AI extraction succeeded with %s model: %s", label, model)
                return result

            except AIProviderRetryableError as exc:
                logger.warning("Retryable failure on %s (%s): %s. Trying next fallback.", label, model, exc)
                last_error = exc
                continue  # try next model

            except AIExtractionError:
                # Non-retryable: propagate immediately without trying fallbacks
                raise

        raise AIExtractionError(
            f"All {len(models)} OpenRouter model(s) exhausted. Last error: {last_error}"
        )
