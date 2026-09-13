from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_authenticated_identity
from app.database.repository import get_db
from app.models.bidder import Bidder
from app.models.document import Document
from app.models.tender import Tender, tender_bidders
from app.models.tender_requirement import ComplianceEvaluation
from app.models.user import ApplicationRole, User


def get_current_application_user(
    identity=Depends(get_authenticated_identity),
) -> User:
    return identity.application_user


def require_authenticated_user(
    current_user: Annotated[User, Depends(get_current_application_user)],
) -> User:
    return current_user


def require_role(*allowed_roles: ApplicationRole) -> Callable:
    role_values = {role.value for role in allowed_roles}

    def role_dependency(
        current_user: Annotated[User, Depends(get_current_application_user)],
    ) -> User:
        if current_user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your application role cannot access this resource.",
            )
        return current_user

    return role_dependency


def require_bidder(
    current_user: Annotated[User, Depends(require_role(ApplicationRole.BIDDER))],
) -> User:
    return current_user


def require_officer(
    current_user: Annotated[User, Depends(require_role(ApplicationRole.OFFICER))],
) -> User:
    return current_user


def _parse_uuid(value: str, resource_name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_name} not found.") from None


def _load_owned_bidder(db: Session, bidder_id: str, current_user: User) -> Bidder:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorization service is unavailable.",
        )
    try:
        bidder_uuid = UUID(bidder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidder not found.") from None

    bidder = db.scalar(
        select(Bidder).where(
            Bidder.id == bidder_uuid,
            Bidder.user_id == current_user.id,
        )
    )
    if bidder is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this bidder profile.")
    return bidder


def require_owned_bidder(
    bidder_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_bidder)],
) -> Bidder:
    return _load_owned_bidder(db, bidder_id, current_user)


def require_owned_bidder_by_id(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_bidder)],
) -> Bidder:
    return _load_owned_bidder(db, id, current_user)


def require_document_access(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_application_user)],
) -> Document:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorization service is unavailable.",
        )
    try:
        document_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.") from None

    document = db.scalar(select(Document).where(Document.id == document_uuid))
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if current_user.role == ApplicationRole.OFFICER.value:
        return document
    if current_user.role != ApplicationRole.BIDDER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your application role cannot access this resource.")

    owns_document = db.scalar(
        select(Bidder.id).join(Document, Document.bidder_id == Bidder.id).where(
            Document.id == document_uuid,
            Bidder.user_id == current_user.id,
        )
    )
    if owns_document is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this document.")
    return document


def require_bidder_or_officer_bidder(
    bidder_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> Bidder:
    bidder_uuid = _parse_uuid(bidder_id, "Bidder")
    bidder = db.scalar(select(Bidder).where(Bidder.id == bidder_uuid)) if db is not None else None
    if bidder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidder not found.")
    if current_user.role == ApplicationRole.OFFICER.value:
        return bidder
    if current_user.role == ApplicationRole.BIDDER.value and bidder.user_id == current_user.id:
        return bidder
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this bidder.")


def require_tender_bidder_access(
    tender_id: str,
    bidder_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> Bidder:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authorization service is unavailable.")
    bidder_uuid = _parse_uuid(bidder_id, "Bidder")
    try:
        tender_uuid = UUID(tender_id)
        tender_filter = Tender.id == tender_uuid
    except ValueError:
        tender_filter = Tender.reference_number == tender_id
    tender_query = select(Tender.id).join(tender_bidders, tender_bidders.c.tender_id == Tender.id).where(
        tender_bidders.c.bidder_id == bidder_uuid,
        tender_filter,
    )
    if db.scalar(tender_query) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender bidder relationship not found.")
    bidder = db.scalar(select(Bidder).where(Bidder.id == bidder_uuid))
    if bidder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidder not found.")
    if current_user.role == ApplicationRole.OFFICER.value:
        return bidder
    if current_user.role == ApplicationRole.BIDDER.value and bidder.user_id == current_user.id:
        return bidder
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this bidder.")


def require_evaluation_access(
    evaluation_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> ComplianceEvaluation:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authorization service is unavailable.")
    evaluation_uuid = _parse_uuid(evaluation_id, "Evaluation")
    evaluation = db.scalar(select(ComplianceEvaluation).where(ComplianceEvaluation.id == evaluation_uuid))
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")
    if current_user.role == ApplicationRole.OFFICER.value:
        return evaluation
    if current_user.role != ApplicationRole.BIDDER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your application role cannot access this resource.")
    owns_evaluation = db.scalar(
        select(Bidder.id).where(
            Bidder.id == evaluation.bidder_id,
            Bidder.user_id == current_user.id,
        )
    )
    if owns_evaluation is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this evaluation.")
    return evaluation
