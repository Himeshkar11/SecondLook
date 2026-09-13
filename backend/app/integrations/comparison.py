"""Deterministic field-level normalization and comparison engine for statutory verification.

Follows strict equality after canonical normalization (whitespace trimming, case normalization,
collapsed repeated spaces, and standard ISO date formatting).
Fuzzy matching is explicitly forbidden.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class FieldComparisonStatus(str, Enum):
    """Field-level outcome states."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING_FROM_DOCUMENT = "MISSING_FROM_DOCUMENT"
    MISSING_FROM_SOURCE = "MISSING_FROM_SOURCE"


class OverallVerificationResult(str, Enum):
    """Overall statutory verification determination states."""

    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    NOT_FOUND = "NOT_FOUND"
    SOURCE_ERROR = "SOURCE_ERROR"
    PENDING = "PENDING"


def normalize_value(val: Any) -> Optional[str]:
    """Deterministically normalize any scalar field value.

    - Strips leading and trailing whitespace
    - Normalizes uppercase casing
    - Replaces internal consecutive whitespace with a single space
    - Attempts ISO 8601 YYYY-MM-DD parsing for dates (e.g. DD/MM/YYYY -> YYYY-MM-DD)
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None

    # Try common date formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Collapse multiple whitespace characters and uppercase
    collapsed = re.sub(r"\s+", " ", s).strip().upper()
    return collapsed


def compare_single_field(doc_val: Any, gov_val: Any) -> Tuple[FieldComparisonStatus, Optional[str], Optional[str]]:
    """Compare a single field from document extraction against government source."""
    norm_doc = normalize_value(doc_val)
    norm_gov = normalize_value(gov_val)

    if norm_doc is None and norm_gov is None:
        # Both empty/null
        return FieldComparisonStatus.MISSING_FROM_DOCUMENT, norm_doc, norm_gov

    if norm_doc is None:
        return FieldComparisonStatus.MISSING_FROM_DOCUMENT, None, norm_gov

    if norm_gov is None:
        return FieldComparisonStatus.MISSING_FROM_SOURCE, norm_doc, None

    if norm_doc == norm_gov:
        return FieldComparisonStatus.MATCH, norm_doc, norm_gov

    return FieldComparisonStatus.MISMATCH, norm_doc, norm_gov


def compare_gst_data(
    document_fields: Dict[str, Any],
    government_data: Dict[str, Any],
) -> Tuple[OverallVerificationResult, Dict[str, Dict[str, Any]]]:
    """Deterministically compare extracted GST certificate data with government data.

    Fields considered:
    - gstin (primary identifier)
    - legal_name
    - trade_name
    - registration_date
    - status
    - state
    """
    fields_to_compare = [
        "gstin",
        "legal_name",
        "trade_name",
        "registration_date",
        "status",
        "state",
    ]

    field_results: Dict[str, Dict[str, Any]] = {}
    has_mismatch = False
    has_match = False

    for field in fields_to_compare:
        doc_raw = document_fields.get(field)
        gov_raw = government_data.get(field)

        # Handle aliases if needed (e.g. name / legal_name)
        if field == "legal_name":
            doc_raw = doc_raw or document_fields.get("name")
            gov_raw = gov_raw or government_data.get("name")

        if doc_raw is None and gov_raw is None:
            continue

        status, norm_doc, norm_gov = compare_single_field(doc_raw, gov_raw)
        field_results[field] = {
            "document_value": str(doc_raw) if doc_raw is not None else None,
            "government_value": str(gov_raw) if gov_raw is not None else None,
            "status": status.value,
        }

        if status == FieldComparisonStatus.MISMATCH:
            has_mismatch = True
        elif status == FieldComparisonStatus.MATCH:
            has_match = True

    # Check primary identifier (GSTIN) specifically
    gstin_res = field_results.get("gstin", {})
    if gstin_res.get("status") == FieldComparisonStatus.MISMATCH.value:
        return OverallVerificationResult.MISMATCH, field_results

    if has_mismatch:
        return OverallVerificationResult.MISMATCH, field_results

    if has_match:
        return OverallVerificationResult.VERIFIED, field_results

    # If no fields could be matched
    return OverallVerificationResult.MISMATCH, field_results


def compare_pan_data(
    document_fields: Dict[str, Any],
    government_data: Dict[str, Any],
) -> Tuple[OverallVerificationResult, Dict[str, Dict[str, Any]]]:
    """Deterministically compare extracted PAN card data with government data.

    Fields considered:
    - pan (primary identifier)
    - name (or legal_name)
    - status
    """
    fields_to_compare = [
        "pan",
        "name",
        "status",
    ]

    field_results: Dict[str, Dict[str, Any]] = {}
    has_mismatch = False
    has_match = False

    for field in fields_to_compare:
        doc_raw = document_fields.get(field)
        gov_raw = government_data.get(field)

        if field == "name":
            doc_raw = doc_raw or document_fields.get("legal_name")
            gov_raw = gov_raw or government_data.get("legal_name")

        if doc_raw is None and gov_raw is None:
            continue

        status, norm_doc, norm_gov = compare_single_field(doc_raw, gov_raw)
        field_results[field] = {
            "document_value": str(doc_raw) if doc_raw is not None else None,
            "government_value": str(gov_raw) if gov_raw is not None else None,
            "status": status.value,
        }

        if status == FieldComparisonStatus.MISMATCH:
            has_mismatch = True
        elif status == FieldComparisonStatus.MATCH:
            has_match = True

    pan_res = field_results.get("pan", {})
    if pan_res.get("status") == FieldComparisonStatus.MISMATCH.value:
        return OverallVerificationResult.MISMATCH, field_results

    if has_mismatch:
        return OverallVerificationResult.MISMATCH, field_results

    if has_match:
        return OverallVerificationResult.VERIFIED, field_results

    return OverallVerificationResult.MISMATCH, field_results
