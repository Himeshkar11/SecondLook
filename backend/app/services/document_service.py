"""Document service demo operations.

This service validates a minimal input shape and returns deterministic
metadata suitable for the M09 public contract. It is deliberately not a
real storage, OCR, extraction, or verification implementation.
"""

from typing import Any, Dict


class DocumentService:
    """Demo-only document service for the REST API contract boundary."""

    def upload_document(self, bidder_id: str, document_type: str, file_name: str = "demo.pdf", mime_type: str = "application/pdf") -> Dict[str, Any]:
        """Return contract-compatible metadata for a document upload.

        The file is not stored; this is a demonstration placeholder only.
        """
        if not bidder_id or not document_type:
            raise ValueError("bidder_id and document_type are required")

        if not file_name.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise ValueError("unsupported document extension")

        return {
            "id": "00000000-0000-0000-0000-000000000004",
            "bidder_id": bidder_id,
            "document_type": document_type,
            "file_name": file_name,
            "mime_type": mime_type,
            "status": "uploaded",
            "uploaded_at": "2026-09-11T00:00:00Z",
        }
