from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.bidder import Bidder
from app.models.officer_profile import OfficerProfile
from app.models.user import User


@dataclass(frozen=True)
class SupabaseAuthUser:
    id: UUID
    email: str | None
    user_metadata: dict | None = None


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
        return SupabaseAuthUser(
            id=auth_user_id,
            email=payload.get("email"),
            user_metadata=payload.get("user_metadata") or {},
        )

    def resolve_auth_user(self, access_token: str) -> UUID:
        return self.resolve_supabase_user(access_token).id

    def _ensure_application_user(self, db: Session, auth_user: SupabaseAuthUser) -> User:
        existing_user = db.scalar(select(User).where(User.auth_user_id == auth_user.id))
        if existing_user is not None:
            return existing_user

        metadata = auth_user.user_metadata or {}

        # SECURITY: role must NEVER be sourced from client-controlled
        # user_metadata. Supabase user_metadata is set by the client at
        # signup time (e.g. via `options: { data: { role: "OFFICER" } }`)
        # and is not server-validated. Trusting it here would let any
        # signup self-elevate to OFFICER. All lazily-provisioned identities
        # default to the least-privileged role. Legitimate OFFICER accounts
        # must be created through a separate, server-authorized path
        # (admin invite / manual promotion / invite-token signup) rather
        # than through this lazy-provisioning fallback.
        role = "BIDDER"

        existing_email = (
            db.scalar(select(User).where(User.email == auth_user.email))
            if auth_user.email
            else None
        )
        if existing_email is not None and existing_email.auth_user_id != auth_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated identity is not linked to an active application user.",
            )

        application_user = User(
            auth_user_id=auth_user.id,
            email=auth_user.email or f"{auth_user.id}@placeholder.local",
            full_name=(
                metadata.get("full_name")
                or metadata.get("name")
                or auth_user.email
                or str(auth_user.id)
            ),
            role=role,
            is_active=True,
        )
        db.add(application_user)

        try:
            db.flush()
            # role is always BIDDER on this path, so only a Bidder profile
            # is ever auto-provisioned here. OfficerProfile rows must be
            # created exclusively through the authorized officer-provisioning
            # path, never through this fallback.
            bidder_profile = Bidder(
                user_id=application_user.id,
                legal_name=(
                    metadata.get("legal_name")
                    or metadata.get("company_name")
                    or application_user.full_name
                ),
                registration_number=metadata.get("registration_number"),
                gst_number=metadata.get("gst_number"),
                pan_number=metadata.get("pan_number"),
            )
            db.add(bidder_profile)
            db.commit()
            db.refresh(application_user)
        except IntegrityError:
            # Another concurrent request for the same brand-new auth
            # identity may have already provisioned this user (e.g. two
            # tabs, a double-click, or a retried request). Roll back and
            # re-check for the winning row instead of failing a legitimate,
            # correctly-authenticated request outright.
            db.rollback()
            winner = db.scalar(select(User).where(User.auth_user_id == auth_user.id))
            if winner is not None:
                return winner
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated identity is not linked to an active application user.",
            ) from None

        return application_user

    def resolve_application_identity(self, db: Session, access_token: str) -> AuthenticatedIdentity:
        auth_user = self.resolve_supabase_user(access_token)
        application_user = self._ensure_application_user(db, auth_user)
        if not application_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated identity is not linked to an active application user.",
            )
        return AuthenticatedIdentity(auth_user_id=auth_user.id, application_user=application_user)  