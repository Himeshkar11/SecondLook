import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.service import SupabaseAuthUser
from app.auth.dependencies import get_supabase_auth_user
from app.database.repository import get_db
from app.main import app
from app.models.base import Base
from app.models.bidder import Bidder
from app.models.officer_profile import OfficerProfile
from app.models.user import User
from app.schemas.auth import SignupProvisionRequest
from app.services.signup_service import SignupProvisioningService


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    database_session = sessionmaker(bind=engine)()
    yield database_session
    database_session.close()


def auth_user(email: str) -> SupabaseAuthUser:
    return SupabaseAuthUser(id=uuid.uuid4(), email=email)


def test_bidder_signup_creates_only_bidder_profile(session):
    request = SignupProvisionRequest(
        role="BIDDER",
        full_name="ABC Applicant",
        legal_name="ABC Applicant Technologies",
        gst_number="27ABCDE1234F1Z5",
        pan_number="ABCDE1234F",
    )

    result = SignupProvisioningService().provision(session, auth_user("abc@example.test"), request)

    user = session.get(User, result.user_id)
    assert user.role == "BIDDER"
    assert user.auth_user_id == result.auth_user_id
    assert user.bidder_profile.user_id == user.id
    assert user.bidder_profile.legal_name == "ABC Applicant Technologies"
    assert user.officer_profile is None


def test_officer_signup_creates_only_officer_profile(session):
    request = SignupProvisionRequest(role="OFFICER", full_name="Officer Applicant")

    result = SignupProvisioningService().provision(session, auth_user("officer@example.test"), request)

    user = session.get(User, result.user_id)
    assert user.role == "OFFICER"
    assert user.officer_profile.user_id == user.id
    assert user.bidder_profile is None


def test_signup_rejects_every_non_canonical_role():
    for role in [None, "ADMIN", "admin", "procurement_officer", "MANAGER", "bidder"]:
        payload = {"role": role, "full_name": "Applicant"}
        with pytest.raises(ValidationError):
            SignupProvisionRequest.model_validate(payload)


def test_bidder_signup_requires_company_name(session):
    request = SignupProvisionRequest(role="BIDDER", full_name="Applicant")

    with pytest.raises(HTTPException) as exc_info:
        SignupProvisioningService().provision(session, auth_user("missing-company@example.test"), request)

    assert exc_info.value.status_code == 422
    assert "Company name" in exc_info.value.detail
    assert session.query(User).count() == 0


def test_signup_provisioning_does_not_depend_on_email_confirmation_state(session):
    request = SignupProvisionRequest(
        role="BIDDER",
        full_name="No Confirmation Applicant",
        legal_name="No Confirmation Ltd",
    )

    result = SignupProvisioningService().provision(session, auth_user("confirm-none@example.test"), request)

    created_user = session.get(User, result.user_id)
    assert created_user.role == "BIDDER"
    assert created_user.auth_user_id == result.auth_user_id
    assert created_user.bidder_profile is not None
    assert created_user.officer_profile is None


def test_duplicate_auth_identity_is_rejected_without_duplicate_profile(session):
    auth = auth_user("duplicate@example.test")
    first_request = SignupProvisionRequest(
        role="OFFICER",
        full_name="First Applicant",
    )
    SignupProvisioningService().provision(session, auth, first_request)

    second_request = SignupProvisionRequest(
        role="BIDDER",
        full_name="Second Applicant",
        legal_name="Second Applicant Ltd",
    )
    with pytest.raises(HTTPException) as exc_info:
        SignupProvisioningService().provision(session, auth, second_request)

    assert exc_info.value.status_code == 409
    assert session.query(User).count() == 1
    assert session.query(OfficerProfile).count() == 1
    assert session.query(Bidder).count() == 0


def test_duplicate_email_is_rejected(session):
    auth = auth_user("existing@example.test")
    session.add(User(email=auth.email, full_name="Existing", role="OFFICER"))
    session.commit()

    request = SignupProvisionRequest(role="OFFICER", full_name="Applicant")
    with pytest.raises(HTTPException) as exc_info:
        SignupProvisioningService().provision(session, auth, request)

    assert exc_info.value.status_code == 409
    assert session.query(User).count() == 1


def test_provision_endpoint_creates_role_selected_profile(session):
    auth = auth_user("api-bidder@example.test")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_supabase_auth_user] = lambda: auth
    try:
        response = TestClient(app).post(
            "/api/v1/auth/provision",
            json={
                "role": "BIDDER",
                "full_name": "API Applicant",
                "legal_name": "API Applicant Ltd",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "BIDDER"
    assert "password" not in body
    assert "access_token" not in body
    created_user = session.get(User, uuid.UUID(body["user_id"]))
    assert created_user.auth_user_id == auth.id
    assert created_user.bidder_profile is not None
    assert created_user.officer_profile is None
