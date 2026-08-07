import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.deps import RoleChecker, get_current_user
from api.database.session import get_db
from api.models.membership import OrganizationInvitation, UserOrganization, UserRole
from api.models.organization import Organization
from api.models.user import User
from api.routes.auth import log_audit
from api.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationMemberResponse

from api.services.base import ServiceContext
from api.services.core import OrganizationService, CreateOrganizationDTO, get_organization_service
from api.services.email_service import send_invitation_email

router = APIRouter(prefix="/organizations", tags=["organizations"])


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


@router.post(
    "/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    org_service: OrganizationService = Depends(get_organization_service),
) -> Any:
    """
    Create a new organization using OrganizationService.
    """
    base_slug = org_in.slug or slugify(org_in.name)
    ctx = ServiceContext(user_id=current_user.id)

    dto = CreateOrganizationDTO(
        name=org_in.name,
        slug=base_slug,
    )
    result = await org_service.create(ctx, dto)
    if result.is_failure:
        raise HTTPException(status_code=result.status_code, detail=result.errors)

    org_res = result.unwrap()
    return {
        "id": org_res.id,
        "name": org_res.name,
        "slug": org_res.slug,
        "is_active": org_res.is_active,
        "created_at": org_res.created_at,
    }


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


owner_admin_checker = RoleChecker([UserRole.OWNER, UserRole.ADMIN])
owner_checker = RoleChecker([UserRole.OWNER])


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.MEMBER


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
    body: InviteMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """
    Invite a user to join organization. Only OWNER or ADMIN.
    """
    email = body.email
    role = body.role

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
        invited_by=current_user.id,
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

    org = db.query(Organization).filter(Organization.id == organization_id).first()
    org_name = org.name if org else "EAIMOS"
    invite_link = f"{settings.FRONTEND_URL}/auth/accept-invitation?token={token}"
    try:
        send_invitation_email(
            email,
            current_user.full_name,
            org_name,
            role.value if hasattr(role, "value") else str(role),
            invite_link,
        )
    except Exception as exc:
        import logging
        logging.getLogger("eaimos.organizations").error(f"Failed to send invitation email: {exc}")

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
            "invite_link": f"{settings.FRONTEND_URL}/auth/accept-invitation?token={i.token}",
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


# ─── Resend Invitation ────────────────────────────────────────────────────────

@router.post("/{organization_id}/invitations/{invitation_id}/resend", status_code=status.HTTP_200_OK)
def resend_invitation(
    organization_id: uuid.UUID,
    invitation_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """Resend an invitation email. Only OWNER or ADMIN."""
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
        )
        .first()
    )
    expires_at = invitation.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation has expired. Create a new one.")

    # Rate limit: max 5 resends
    if invitation.resent_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum resend limit reached. Revoke and create a new invitation.",
        )

    invitation.resent_count = (invitation.resent_count or 0) + 1
    invitation.last_resent_at = datetime.now(timezone.utc)
    db.commit()

    org = db.query(Organization).filter(Organization.id == organization_id).first()
    org_name = org.name if org else "EAIMOS"
    invite_link = f"{settings.FRONTEND_URL}/auth/accept-invitation?token={invitation.token}"

    try:
        send_invitation_email(
            invitation.email,
            current_user.full_name,
            org_name,
            invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
            invite_link,
        )
    except Exception as exc:
        import logging
        logging.getLogger("eaimos.organizations").error(f"Failed to resend invitation: {exc}")

    log_audit(db, current_user.id, "INVITATION_RESENT", request, {
        "invitation_id": str(invitation_id), "email": invitation.email
    })

    return {
        "success": True,
        "message": f"Invitation resent to {invitation.email}",
        "resent_count": invitation.resent_count,
    }


# ─── Revoke Invitation ────────────────────────────────────────────────────────

@router.delete("/{organization_id}/invitations/{invitation_id}", status_code=status.HTTP_200_OK)
def revoke_invitation(
    organization_id: uuid.UUID,
    invitation_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """Revoke (cancel) a pending invitation. Only OWNER or ADMIN."""
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.is_accepted == False,
            OrganizationInvitation.is_rejected == False,
        )
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already used")

    invitation.is_rejected = True
    invitation.revoked_by = current_user.id
    invitation.revoked_at = datetime.now(timezone.utc)
    db.commit()

    log_audit(db, current_user.id, "INVITATION_REVOKED", request, {
        "invitation_id": str(invitation_id), "email": invitation.email
    })

    return {"success": True, "message": f"Invitation for {invitation.email} revoked"}


# ─── Organization Settings & Branding ────────────────────────────────────────

class OrgSettingsUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    language: Optional[str] = None
    theme_color: Optional[str] = None
    billing_email: Optional[str] = None
    default_ai_provider: Optional[str] = None
    default_image_provider: Optional[str] = None
    default_ai_model: Optional[str] = None
    settings_json: Optional[dict] = None


@router.patch("/{organization_id}/settings", status_code=status.HTTP_200_OK)
def update_org_settings(
    organization_id: uuid.UUID,
    body: OrgSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_admin_checker),
) -> Any:
    """Update organization settings and branding. OWNER or ADMIN only."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if hasattr(org, field):
            setattr(org, field, value)

    db.commit()
    db.refresh(org)

    log_audit(db, current_user.id, "ORG_SETTINGS_UPDATED", request, {
        "org_id": str(organization_id), "fields": list(update_data.keys())
    })

    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "logo_url": org.logo_url,
        "website": org.website,
        "industry": org.industry,
        "timezone": org.timezone,
        "locale": org.locale,
        "language": org.language,
        "theme_color": org.theme_color,
        "billing_email": org.billing_email,
        "default_ai_provider": org.default_ai_provider,
        "default_image_provider": org.default_image_provider,
        "default_ai_model": org.default_ai_model,
        "is_active": org.is_active,
        "plan_tier": org.plan_tier,
        "settings_json": org.settings_json,
    }


# ─── Transfer Ownership ───────────────────────────────────────────────────────

class TransferOwnershipRequest(BaseModel):
    new_owner_user_id: uuid.UUID


@router.post("/{organization_id}/transfer-ownership", status_code=status.HTTP_200_OK)
def transfer_ownership(
    organization_id: uuid.UUID,
    body: TransferOwnershipRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_checker),
) -> Any:
    """Transfer organization ownership to another member. OWNER only."""
    # Verify target is a member
    target_membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == body.new_owner_user_id,
        )
        .first()
    )
    if not target_membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not a member of this organization")

    # Downgrade current owner to ADMIN
    membership.role = UserRole.ADMIN
    # Upgrade target to OWNER
    target_membership.role = UserRole.OWNER
    db.commit()

    log_audit(db, current_user.id, "ORG_OWNERSHIP_TRANSFERRED", request, {
        "org_id": str(organization_id),
        "new_owner_id": str(body.new_owner_user_id),
    })

    target_user = db.query(User).filter(User.id == body.new_owner_user_id).first()
    try:
        from api.services.email_service import send_role_changed_email
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if target_user and org:
            send_role_changed_email(target_user.email, target_user.full_name, org.name, "Owner")
    except Exception:
        pass

    return {"success": True, "message": "Ownership transferred successfully"}


# ─── Archive / Restore Org ────────────────────────────────────────────────────

@router.post("/{organization_id}/archive", status_code=status.HTTP_200_OK)
def archive_organization(
    organization_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: UserOrganization = Depends(owner_checker),
) -> Any:
    """Archive (hide but not delete) an organization. OWNER only."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    org.is_active = False
    db.commit()

    log_audit(db, current_user.id, "ORG_ARCHIVED", request, {"org_id": str(organization_id)})
    return {"success": True, "message": f"Organization '{org.name}' archived"}


@router.post("/{organization_id}/restore", status_code=status.HTTP_200_OK)
def restore_organization(
    organization_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Restore an archived organization. OWNER or superuser only."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check ownership
    if not current_user.is_superuser:
        m = db.query(UserOrganization).filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.user_id == current_user.id,
            UserOrganization.role == UserRole.OWNER,
        ).first()
        if not m:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OWNER access required")

    org.is_active = True
    db.commit()

    log_audit(db, current_user.id, "ORG_RESTORED", request, {"org_id": str(organization_id)})
    return {"success": True, "message": f"Organization '{org.name}' restored"}


# ─── Organization Switcher ────────────────────────────────────────────────────

@router.get("/me/current")
def get_current_org(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get the user's currently active organization from session/header."""
    header_val = request.headers.get("x-organization-id")
    org_id = None
    if header_val:
        try:
            org_id = uuid.UUID(header_val)
        except ValueError:
            pass

    if not org_id:
        m = db.query(UserOrganization).filter(
            UserOrganization.user_id == current_user.id,
        ).order_by(UserOrganization.joined_at).first()
        if m:
            org_id = m.organization_id

    if not org_id:
        return {"organization": None}

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"organization": None}

    m = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == org_id,
    ).first()

    return {
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "logo_url": org.logo_url,
            "plan_tier": org.plan_tier,
            "is_active": org.is_active,
        },
        "role": m.role.value if m and hasattr(m.role, "value") else "MEMBER",
    }
