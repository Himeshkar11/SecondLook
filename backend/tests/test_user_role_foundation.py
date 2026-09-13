import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.bidder import Bidder
from app.models.officer_profile import OfficerProfile
from app.models.tender import Tender
from app.models.tender_requirement import ComplianceEvaluation
from app.models.user import ApplicationRole, User
from app.review.models import OfficerReview


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


def make_user(email: str, role: str = ApplicationRole.BIDDER.value) -> User:
    return User(id=uuid.uuid4(), email=email, full_name="Test User", role=role)


def test_canonical_roles_are_valid(session):
    session.add_all([
        make_user("bidder@example.test", ApplicationRole.BIDDER.value),
        make_user("officer@example.test", ApplicationRole.OFFICER.value),
    ])
    session.commit()
    assert {user.role for user in session.query(User).all()} == {"BIDDER", "OFFICER"}


def test_arbitrary_role_is_rejected(session):
    session.add(make_user("invalid@example.test", "ADMIN"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_legacy_roles_remain_explicitly_compatible_during_migration(session):
    session.add_all([
        make_user("legacy-admin@example.test", "admin"),
        make_user("legacy-officer@example.test", "procurement_officer"),
    ])
    session.commit()
    assert {user.role for user in session.query(User).all()} == {"admin", "procurement_officer"}


def test_bidder_profile_is_one_to_one_with_user(session):
    user = make_user("bidder@example.test")
    session.add(user)
    session.flush()
    session.add(Bidder(user_id=user.id, legal_name="Bidder One"))
    session.commit()

    session.add(Bidder(user_id=user.id, legal_name="Bidder Duplicate"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_officer_profile_is_one_to_one_with_user(session):
    user = make_user("officer@example.test", ApplicationRole.OFFICER.value)
    session.add(user)
    session.flush()
    session.add(OfficerProfile(user_id=user.id))
    session.commit()

    session.add(OfficerProfile(user_id=user.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_existing_tender_and_review_foreign_keys_remain_valid(session):
    user = make_user("officer@example.test", ApplicationRole.OFFICER.value)
    bidder = Bidder(user=user, legal_name="Bidder One")
    tender = Tender(
        created_by=user.id,
        reference_number="TND-M02-001",
        title="M02 Tender",
    )
    session.add_all([user, bidder, tender])
    session.flush()
    evaluation = ComplianceEvaluation(tender_id=tender.id, bidder_id=bidder.id, status="COMPLETED")
    session.add(evaluation)
    session.flush()
    review = OfficerReview(evaluation_id=evaluation.id, reviewer_id=user.id)
    session.add(review)
    session.commit()

    assert session.get(Tender, tender.id).created_by == user.id
    assert session.get(OfficerReview, review.id).reviewer_id == user.id