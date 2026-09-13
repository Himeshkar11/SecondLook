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


@pytest.fixture(autouse=True)
def legacy_contract_auth_compatibility(request):
    """Keep pre-M4 contract tests focused on service behavior.

    Dedicated authorization tests opt out and exercise the real dependencies.
    This fixture never runs in production and does not weaken runtime routes.
    """
    if request.path.name in {
        "test_authorization_boundaries.py",
        "test_bidder_workspace_foundation.py",
        "test_bid_submission_foundation.py",
    }:
        yield
        return


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
    try:
        yield
    finally:
        app.dependency_overrides.pop(require_officer, None)
        app.dependency_overrides.pop(require_owned_bidder, None)
        app.dependency_overrides.pop(require_owned_bidder_by_id, None)
        app.dependency_overrides.pop(require_document_access, None)
        app.dependency_overrides.pop(require_authenticated_user, None)
        app.dependency_overrides.pop(require_bidder_or_officer_bidder, None)
        app.dependency_overrides.pop(require_tender_bidder_access, None)
        app.dependency_overrides.pop(require_evaluation_access, None)
