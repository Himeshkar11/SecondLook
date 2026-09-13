from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.service import SupabaseAuthUser
from app.models.bidder import Bidder
from app.models.officer_profile import OfficerProfile
from app.models.user import User
from app.schemas.auth import SignupProvisionRequest, SignupProvisionResponse


class SignupProvisioningService:
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

        if request.role == "BIDDER" and not request.legal_name:
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
            if request.role == "BIDDER":
                profile = Bidder(
                    user_id=application_user.id,
                    legal_name=request.legal_name,
                    registration_number=request.registration_number,
                    gst_number=request.gst_number,
                    pan_number=request.pan_number,
                )
                db.add(profile)
            else:
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
                detail="Unable to create your application profile. Please try again.",
            ) from None

        return SignupProvisionResponse(
            user_id=application_user.id,
            auth_user_id=auth_user.id,
            role=application_user.role,
            profile_id=profile.id,
        )
