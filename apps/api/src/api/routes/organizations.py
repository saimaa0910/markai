import re
from typing import Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.schemas.organization import OrganizationCreate, OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


@router.post(
    "/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new organization and bind current user as OWNER.
    """
    base_slug = org_in.slug or slugify(org_in.name)

    # Ensure slug uniqueness
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=org_in.name, slug=slug)
    db.add(org)
    db.flush()

    # Link user to organization
    membership = UserOrganization(
        user_id=current_user.id, organization_id=org.id, role=UserRole.OWNER
    )
    db.add(membership)
    db.commit()
    db.refresh(org)

    return org


@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all organizations the current authenticated user belongs to.
    """
    memberships = (
        db.query(UserOrganization)
        .filter(UserOrganization.user_id == current_user.id)
        .all()
    )
    org_ids = [m.organization_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return orgs
