import uuid

import pytest

from app.authz.dependencies import (
    require_document_access,
    require_authenticated_user,
    require_bidder_or_officer_bidder,
    require_evaluation_access,
    require_officer,
    require_owned_bidder,
    require_owned_bidder_by_id,
    require_tender_bidder_access,
)
from app.main import app
from app.models.bidder import Bidder
from app.models.user import User


def _apply_mock_auth():
    compatibility_user = User(
        id=uuid.UUID("c1111111-1111-1111-1111-111111111111"),
        email="legacy-test-officer@example.test",
        full_name="Legacy Contract Test Officer",
        role="OFFICER",
    )
    compatibility_bidder = Bidder(
        id=uuid.UUID("c2222222-2222-2222-2222-222222222222"),
        user_id=compatibility_user.id,
        legal_name="Legacy Contract Test Bidder",
    )
    app.dependency_overrides[require_officer] = lambda: compatibility_user
    app.dependency_overrides[require_owned_bidder] = lambda: compatibility_bidder
    app.dependency_overrides[require_owned_bidder_by_id] = lambda: compatibility_bidder
    app.dependency_overrides[require_document_access] = lambda: None
    app.dependency_overrides[require_authenticated_user] = lambda: compatibility_user
    app.dependency_overrides[require_bidder_or_officer_bidder] = lambda: compatibility_bidder
    app.dependency_overrides[require_tender_bidder_access] = lambda: compatibility_bidder
    app.dependency_overrides[require_evaluation_access] = lambda: None


def _clear_mock_auth():
    app.dependency_overrides.pop(require_officer, None)
    app.dependency_overrides.pop(require_owned_bidder, None)
    app.dependency_overrides.pop(require_owned_bidder_by_id, None)
    app.dependency_overrides.pop(require_document_access, None)
    app.dependency_overrides.pop(require_authenticated_user, None)
    app.dependency_overrides.pop(require_bidder_or_officer_bidder, None)
    app.dependency_overrides.pop(require_tender_bidder_access, None)
    app.dependency_overrides.pop(require_evaluation_access, None)


@pytest.fixture
def mock_auth():
    """Opt-in fixture for legacy service contract tests that need mocked auth dependencies."""
    _apply_mock_auth()
    try:
        yield
    finally:
        _clear_mock_auth()


@pytest.fixture
def legacy_contract_auth_compatibility(mock_auth):
    """Backward compatibility fixture name, now strictly opt-in."""
    yield


@pytest.fixture(autouse=True)
def _check_mock_auth_marker(request):
    """Opt-in mechanism via @pytest.mark.mock_auth marker.

    Only activates mock authentication if the test or test module is explicitly
    marked with @pytest.mark.mock_auth. All other tests run against real auth dependencies.
    """
    marker = request.node.get_closest_marker("mock_auth")
    if marker is not None:
        _apply_mock_auth()
        try:
            yield
        finally:
            _clear_mock_auth()
    else:
        yield
