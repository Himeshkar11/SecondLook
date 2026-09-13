from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User


@dataclass(frozen=True)
class SupabaseAuthUser:
    id: UUID
    email: str | None


@dataclass(frozen=True)
class AuthenticatedIdentity:
    auth_user_id: UUID
    application_user: User


class SupabaseAuthConfigurationError(RuntimeError):
    """Raised when backend Supabase Auth configuration is unavailable."""


class SupabaseAuthService:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http_client = http_client

    def _client(self) -> tuple[httpx.Client, bool]:
        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseAuthConfigurationError("Supabase Auth is not configured")
        if self.http_client is not None:
            return self.http_client, False
        return httpx.Client(timeout=10.0), True

    def resolve_supabase_user(self, access_token: str) -> SupabaseAuthUser:
        client, should_close = self._client()
        try:
            response = client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_key,
                    "Authorization": f"Bearer {access_token}",
                },
            )
        finally:
            if should_close:
                client.close()

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = response.json()
            auth_user_id = UUID(payload["id"])
        except (KeyError, TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        return SupabaseAuthUser(id=auth_user_id, email=payload.get("email"))

    def resolve_auth_user(self, access_token: str) -> UUID:
        return self.resolve_supabase_user(access_token).id

    def resolve_application_identity(self, db: Session, access_token: str) -> AuthenticatedIdentity:
        auth_user = self.resolve_supabase_user(access_token)
        application_user = db.scalar(select(User).where(User.auth_user_id == auth_user.id))
        if application_user is None or not application_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated identity is not linked to an active application user.",
            )
        return AuthenticatedIdentity(auth_user_id=auth_user.id, application_user=application_user)
