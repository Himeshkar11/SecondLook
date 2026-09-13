from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.service import AuthenticatedIdentity, SupabaseAuthService, SupabaseAuthUser
from app.database.repository import get_db


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def get_authenticated_identity(
    token: Annotated[str, Depends(get_bearer_token)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthenticatedIdentity:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application identity service is unavailable.",
        )
    return SupabaseAuthService().resolve_application_identity(db, token)


def get_supabase_auth_user(
    token: Annotated[str, Depends(get_bearer_token)],
) -> SupabaseAuthUser:
    """Validate a Supabase identity before application-user provisioning."""
    return SupabaseAuthService().resolve_supabase_user(token)
