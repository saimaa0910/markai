import re
import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationMemberResponse

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


@router.get("/{organization_id}/members/", response_model=List[OrganizationMemberResponse])
def get_organization_members(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all members belonging to the specified organization.
    """
    membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == organization_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )

    memberships = (
        db.query(UserOrganization)
        .filter(UserOrganization.organization_id == organization_id)
        .all()
    )

    results = []
    for m in memberships:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            results.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                "created_at": None,
            })
    return results


from datetime import datetime, timedelta, timezone
import secrets
from api.core.deps import RoleChecker
from api.models.membership import OrganizationInvitation
from api.routes.auth import log_audit


owner_admin_checker = RoleChecker([UserRole.OWNER, UserRole.ADMIN])
owner_checker = RoleChecker([UserRole.OWNER])


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: uuid.UUID,
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """
    Update organization name. Only OWNER or ADMIN.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    org.name = name
    db.commit()
    db.refresh(org)
    return org


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_checker),
) -> None:
    """
    Delete organization. Only OWNER.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    db.delete(org)
    db.commit()


@router.patch("/{organization_id}/members/{user_id}", response_model=OrganizationMemberResponse)
def update_member_role(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """
    Update member role in the organization. Only OWNER or ADMIN.
    """
    target_membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == user_id,
        )
        .first()
    )
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in organization",
        )

    if (role == UserRole.OWNER or target_membership.role == UserRole.OWNER) and membership.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Owner can manage Owner roles.",
        )

    target_membership.role = role
    db.commit()
    db.refresh(target_membership)

    user = db.query(User).filter(User.id == user_id).first()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "role": target_membership.role.value if hasattr(target_membership.role, "value") else str(target_membership.role),
        "created_at": None,
    }


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> None:
    """
    Remove member from organization. Only OWNER or ADMIN.
    """
    if user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the organization.",
        )

    target_membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == user_id,
        )
        .first()
    )
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in organization",
        )

    if target_membership.role == UserRole.OWNER and membership.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Owner can remove an Owner.",
        )

    db.delete(target_membership)
    db.commit()


@router.post("/{organization_id}/invitations/")
def invite_member(
    organization_id: uuid.UUID,
    email: str,
    role: UserRole = UserRole.MEMBER,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """
    Invite a user to join organization. Only OWNER or ADMIN.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        existing_membership = (
            db.query(UserOrganization)
            .filter(
                UserOrganization.organization_id == organization_id,
                UserOrganization.user_id == user.id,
            )
            .first()
        )
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization",
            )

    existing_invite = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
            OrganizationInvitation.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invitation already exists for this email.",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invitation = OrganizationInvitation(
        organization_id=organization_id,
        email=email,
        role=role,
        token=token,
        expires_at=expires_at,
        is_accepted=False,
        is_rejected=False,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    invite_link = f"http://localhost:3000/auth/register?token={token}&email={email}"
    print(f"\n========================================")
    print(f"ORGANIZATION INVITATION TO {email}")
    print(f"Invite Link: {invite_link}")
    print(f"========================================\n")

    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
        "expires_at": invitation.expires_at,
        "invite_link": invite_link,
    }


@router.get("/{organization_id}/invitations/")
def list_invitations(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """
    List pending invitations for the organization. Only OWNER or ADMIN.
    """
    invites = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
            OrganizationInvitation.expires_at > datetime.now(timezone.utc),
        )
        .all()
    )
    return [
        {
            "id": i.id,
            "email": i.email,
            "role": i.role.value if hasattr(i.role, "value") else str(i.role),
            "expires_at": i.expires_at,
            "invite_link": f"http://localhost:3000/auth/register?token={i.token}&email={i.email}",
        }
        for i in invites
    ]


@router.post("/invitations/{invitation_id}/accept/")
def accept_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Accept invitation for a logged-in user.
    """
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
            OrganizationInvitation.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired.",
        )

    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address.",
        )

    membership = UserOrganization(
        user_id=current_user.id,
        organization_id=invitation.organization_id,
        role=invitation.role,
    )
    db.add(membership)
    invitation.is_accepted = True
    db.add(invitation)
    db.commit()

    return {"success": True, "message": "Invitation accepted successfully"}


@router.post("/invitations/{invitation_id}/reject/")
def reject_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Reject/decline invitation for a logged-in user.
    """
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
        )
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found.",
        )

    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address.",
        )

    invitation.is_rejected = True
    db.add(invitation)
    db.commit()

    return {"success": True, "message": "Invitation declined successfully"}
