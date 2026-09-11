"""API-layer dependency placeholders.

This module only defines dependency placeholders for the contract boundary.
It does not implement authentication, authorization, database access,
repositories, downstream services, or business logic.
"""

from typing import Any, Dict

from app.database.repository import get_db


def get_api_request_context() -> Dict[str, Any]:
    """Placeholder dependency used to keep the API boundary explicit.

    M09 is contract-only. This dependency does not provide real auth, DB,
    file, or verification behavior.
    """
    return {
        "request_id": None,
        "authenticated": False,
        "contract_placeholder": True,
    }
