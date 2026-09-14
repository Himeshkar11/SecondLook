import uuid

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.auth.dependencies import get_bearer_token
from app.auth.service import SupabaseAuthConfigurationError, SupabaseAuthService
from app.config.settings import Settings, settings
from app.main import app
from app.models.base import Base
from app.models.user import User


AUTH_USER_ID = uuid.UUID("a1111111-1111-1111-1111-111111111111")
APPLICATION_USER_ID = uuid.UUID("b2222222-2222-2222-2222-222222222222")


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


def mock_client(status_code=200, payload=None):
    def handler(request):
        assert request.url.path == "/auth/v1/user"
        assert request.headers["authorization"] == "Bearer access-token"
        return httpx.Response(status_code, json=payload or {"id": str(AUTH_USER_ID)}, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_supabase_auth_identity_is_resolved_without_storing_password(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_key", "public-key")

    identity_id = SupabaseAuthService(http_client=mock_client()).resolve_auth_user("access-token")

    assert identity_id == AUTH_USER_ID
    assert not hasattr(User, "password")


def test_invalid_supabase_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_key", "public-key")

    with pytest.raises(HTTPException) as exc_info:
        SupabaseAuthService(http_client=mock_client(401, {"error": "invalid"})).resolve_auth_user("access-token")

    assert exc_info.value.status_code == 401
    assert "token" not in str(exc_info.value.detail).lower()


def test_service_role_key_is_supported_for_server_side_admin_usage(monkeypatch):
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    instance = Settings(
        supabase_url="",
        supabase_key="",
        supabase_service_role_key="service-role-key",
        vite_supabase_url="https://auth.example.test",
        vite_supabase_publishable_key="site-key",
        _env_file=None,
    )

    assert instance.supabase_key == "service-role-key"
    assert instance.supabase_service_role_key == "service-role-key"


def test_missing_supabase_configuration_fails_safely(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "")
    monkeypatch.setattr(settings, "supabase_key", "")

    with pytest.raises(SupabaseAuthConfigurationError):
        SupabaseAuthService().resolve_auth_user("access-token")


def test_authenticated_identity_maps_to_only_matching_application_user(session, monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_key", "public-key")
    user = User(
        id=APPLICATION_USER_ID,
        auth_user_id=AUTH_USER_ID,
        email="mapped@example.test",
        full_name="Mapped User",
        role="BIDDER",
    )
    session.add(user)
    session.commit()

    identity = SupabaseAuthService(http_client=mock_client()).resolve_application_identity(session, "access-token")

    assert identity.auth_user_id == AUTH_USER_ID
    assert identity.application_user.id == APPLICATION_USER_ID
    assert identity.application_user.role == "BIDDER"


def test_unmapped_or_inactive_application_user_is_rejected(session, monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_key", "public-key")
    session.add(User(
        id=APPLICATION_USER_ID,
        auth_user_id=AUTH_USER_ID,
        email="inactive@example.test",
        full_name="Inactive User",
        role="OFFICER",
        is_active=False,
    ))
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        SupabaseAuthService(http_client=mock_client()).resolve_application_identity(session, "access-token")

    assert exc_info.value.status_code == 403


def test_missing_application_user_is_lazy_provisioned_from_signup_metadata(session, monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_key", "public-key")

    identity = SupabaseAuthService(http_client=mock_client(payload={
        "id": str(AUTH_USER_ID),
        "email": "provisioned@example.test",
        "user_metadata": {
            "role": "BIDDER",
            "full_name": "Provisioned User",
            "legal_name": "Provisioned Co",
        },
    })).resolve_application_identity(session, "access-token")

    created_user = session.query(User).filter_by(auth_user_id=AUTH_USER_ID).one()
    assert identity.auth_user_id == AUTH_USER_ID
    assert identity.application_user.id == created_user.id
    assert created_user.role == "BIDDER"
    assert created_user.email == "provisioned@example.test"
    assert created_user.bidder_profile is not None


def test_missing_bearer_token_is_rejected():
    request = Request({"type": "http", "headers": []})

    with pytest.raises(HTTPException) as exc_info:
        get_bearer_token(request)

    assert exc_info.value.status_code == 401


def test_auth_me_rejects_missing_authentication():
    response = TestClient(app).get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication is required."}
