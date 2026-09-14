import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.service import SupabaseAuthUser
from app.config.settings import settings
from app.models.bidder import Bidder
from app.models.officer_profile import OfficerProfile
from app.models.user import User
from app.schemas.auth import OfficerInviteProvisionRequest, SignupProvisionRequest, SignupProvisionResponse


class SignupProvisioningService:
    @staticmethod
    def _encode_invite_payload(payload: dict) -> str:
        if not settings.officer_invite_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Officer invite provisioning is not configured.",
            )

        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(settings.officer_invite_secret.encode("utf-8"), body, hashlib.sha256).digest()
        body_encoded = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
        signature_encoded = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        return f"{body_encoded}.{signature_encoded}"

    @staticmethod
    def _decode_invite_payload(token: str) -> dict:
        if not settings.officer_invite_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Officer invite provisioning is not configured.",
            )

        try:
            body_b64, signature_b64 = token.split(".", 1)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            ) from exc

        if not body_b64 or not signature_b64:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            )

        padding = "=" * (-len(body_b64) % 4)
        decoded_body = base64.urlsafe_b64decode(body_b64 + padding)
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(
                settings.officer_invite_secret.encode("utf-8"),
                decoded_body,
                hashlib.sha256,
            ).digest()
        ).decode("ascii").rstrip("=")

        if not hmac.compare_digest(signature_b64, expected_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            )

        try:
            payload = json.loads(decoded_body.decode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            )

        if payload.get("role") != "OFFICER":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            )

        expires_at = payload.get("exp")
        if not isinstance(expires_at, int) or expires_at <= int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="The officer invite token has expired.",
            )

        email = payload.get("email")
        if not isinstance(email, str) or not email.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The officer invite token is invalid.",
            )

        return payload

    @staticmethod
    def generate_officer_invite_token(email: str, ttl_minutes: int = 60) -> str:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValueError("An officer invite requires an email address.")

        expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp())
        return SignupProvisioningService._encode_invite_payload({
            "email": normalized_email,
            "role": "OFFICER",
            "exp": expires_at,
        })

    def provision(
        self,
        db: Session,
        auth_user: SupabaseAuthUser,
        request: SignupProvisionRequest,
    ) -> SignupProvisionResponse:
        if not auth_user.email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The authenticated account does not have an email address.",
            )

        if request.role != "BIDDER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Officer accounts must be created through a trusted server-side invite flow.",
            )

        if not request.legal_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Company name is required for bidder accounts.",
            )

        existing_auth_user = db.scalar(
            select(User).where(User.auth_user_id == auth_user.id)
        )
        if existing_auth_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An application profile already exists for this account.",
            )

        existing_email = db.scalar(
            select(User).where(func.lower(User.email) == auth_user.email.lower())
        )
        if existing_email is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        application_user = User(
            auth_user_id=auth_user.id,
            email=auth_user.email,
            full_name=request.full_name,
            role=request.role,
            is_active=True,
        )
        db.add(application_user)

        try:
            db.flush()
            profile = Bidder(
                user_id=application_user.id,
                legal_name=request.legal_name,
                registration_number=request.registration_number,
                gst_number=request.gst_number,
                pan_number=request.pan_number,
            )
            db.add(profile)
            db.commit()
            db.refresh(application_user)
            db.refresh(profile)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This account already has an application profile.",
            ) from None
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create your application profile. Please try again.",
            ) from None

        return SignupProvisionResponse(
            user_id=application_user.id,
            auth_user_id=auth_user.id,
            role=application_user.role,
            profile_id=profile.id,
        )

    def provision_officer_with_invite(
        self,
        db: Session,
        auth_user: SupabaseAuthUser,
        request: OfficerInviteProvisionRequest,
    ) -> SignupProvisionResponse:
        if not auth_user.email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The authenticated account does not have an email address.",
            )

        invite = self._decode_invite_payload(request.invite_token)
        invited_email = str(invite["email"]).strip().lower()
        if invited_email != auth_user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This officer invite does not match the authenticated account.",
            )

        existing_auth_user = db.scalar(
            select(User).where(User.auth_user_id == auth_user.id)
        )
        if existing_auth_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An application profile already exists for this account.",
            )

        existing_email = db.scalar(
            select(User).where(func.lower(User.email) == auth_user.email.lower())
        )
        if existing_email is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        full_name = request.full_name or auth_user.email.split("@", 1)[0].replace(".", " ").title()
        application_user = User(
            auth_user_id=auth_user.id,
            email=auth_user.email,
            full_name=full_name,
            role="OFFICER",
            is_active=True,
        )
        db.add(application_user)

        try:
            db.flush()
            profile = OfficerProfile(user_id=application_user.id)
            db.add(profile)
            db.commit()
            db.refresh(application_user)
            db.refresh(profile)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This account already has an application profile.",
            ) from None
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create the officer profile. Please try again.",
            ) from None

        return SignupProvisionResponse(
            user_id=application_user.id,
            auth_user_id=auth_user.id,
            role=application_user.role,
            profile_id=profile.id,
        )
