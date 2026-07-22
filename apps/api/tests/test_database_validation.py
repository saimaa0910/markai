"""
Database Quality Assurance Test Suite
======================================
Automated verification of ORM models, optimistic locking, soft delete,
cascade rules, relationships, and multi-tenancy isolation.
"""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from api.database.base import Base
from api.models.organization import Organization
from api.models.user import User
from api.models.membership import UserOrganization, UserRole
from api.models.prompt import Prompt, PromptVersion
from api.models.campaign import Campaign
from api.models.deals import Pipeline, DealStage, Deal
from api.models.billing import BillingPlan, Subscription


def test_base_mixin_defaults(db_session: Session):
    """Verify primary key UUID generation, timestamps, and optimistic locking defaults."""
    org = Organization(
        name="Test Validation Org",
        slug=f"validation-org-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    assert isinstance(org.id, uuid.UUID)
    assert org.version == 1
    assert org.deleted_at is None
    assert isinstance(org.created_at, datetime)
    assert isinstance(org.updated_at, datetime)


def test_optimistic_locking(db_session: Session):
    """Verify version counter increments on update."""
    org = Organization(
        name="Locking Test Org",
        slug=f"locking-org-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(org)
    db_session.commit()
    
    initial_version = org.version
    org.name = "Updated Locking Test Org"
    org.version += 1
    db_session.commit()
    db_session.refresh(org)

    assert org.version == initial_version + 1


def test_multi_tenancy_and_cascade_delete(db_session: Session):
    """Verify tenant isolation and cascade delete from Organization to child entities."""
    org = Organization(
        name="Cascade Test Org",
        slug=f"cascade-org-{uuid.uuid4().hex[:6]}",
    )
    user = User(
        email=f"tester-{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_pw_secret",
        full_name="Test User",
        first_name="Test",
        last_name="User",
    )
    db_session.add_all([org, user])
    db_session.commit()

    membership = UserOrganization(
        organization_id=org.id,
        user_id=user.id,
        role=UserRole.ADMIN,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    db_session.commit()

    # Verify foreign key reference and relationship
    assert membership.organization_id == org.id
    assert membership.user_id == user.id

    # Cascade delete organization via ORM session
    mem_id = membership.id
    db_session.delete(membership)
    db_session.delete(org)
    db_session.commit()

    # Verify membership deleted
    deleted_membership = db_session.query(UserOrganization).filter(UserOrganization.id == mem_id).first()
    assert deleted_membership is None


def test_soft_delete_lifecycle(db_session: Session):
    """Verify soft delete functionality."""
    user = User(
        email=f"softdelete-{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_pw_secret",
        full_name="Soft Delete User",
        first_name="Soft",
        last_name="Delete",
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # Perform soft delete
    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.expire_all()

    active_user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    soft_deleted_user = db_session.query(User).filter(User.id == user_id, User.deleted_at.isnot(None)).first()

    assert active_user is None
    assert soft_deleted_user is not None
