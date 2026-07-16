import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    ALGORITHM,
)
from api.core.config import settings
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole
from api.models.auth import RefreshToken, AuditLog
from api.schemas.user import UserCreate, UserResponse
from api.schemas.token import Token
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["authentication"])


def slugify(text: str) -> str:
    """
    Generate url-friendly slug from string.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def log_audit(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    request: Optional[Request] = None,
    context: Optional[dict] = None,
) -> None:
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    audit = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        context=context,
    )
    db.add(audit)
    db.commit()


def store_refresh_token(db: Session, token: str, user_id: uuid.UUID) -> None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    except Exception:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )

    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(db_token)
    db.commit()


def rotate_refresh_token(db: Session, old_token_str: str) -> str:
    db_token = (
        db.query(RefreshToken).filter(RefreshToken.token == old_token_str).first()
    )
    if (
        not db_token
        or db_token.is_revoked
        or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old token
    db_token.is_revoked = True
    db.add(db_token)
    db.commit()

    # Generate new refresh token
    new_token_str = create_refresh_token(db_token.user_id)
    store_refresh_token(db, new_token_str, db_token.user_id)
    return new_token_str


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    user_in: UserCreate, request: Request, db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user and automatically create a default organization, or join an organization via invitation token.
    """
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        log_audit(
            db,
            None,
            "USER_REGISTER_FAILED",
            request,
            context={"email": user_in.email, "reason": "Email already exists"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    # Resolve invitation if token provided
    invitation = None
    if user_in.invitation_token:
        from api.models.membership import OrganizationInvitation
        invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.token == user_in.invitation_token,
                OrganizationInvitation.is_accepted == False,
                OrganizationInvitation.is_rejected == False,
                OrganizationInvitation.expires_at > datetime.now(timezone.utc)
            )
            .first()
        )
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token.",
            )

    # Create new User
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
        is_verified=True if invitation else False,  # Auto-verify if joining via invitation
    )
    db.add(user)
    db.flush()  # Populate user.id

    if invitation:
        # Bind user to the invitation's organization
        membership = UserOrganization(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role,
        )
        db.add(membership)
        invitation.is_accepted = True
        db.add(invitation)
        db.commit()
        db.refresh(user)

        log_audit(
            db,
            user.id,
            "USER_REGISTER_INVITATION",
            request,
            context={"organization_id": str(invitation.organization_id), "role": str(invitation.role)},
        )
    elif user_in.organization_id:
        org = db.query(Organization).filter(Organization.id == user_in.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target organization not found.",
            )
        membership = UserOrganization(
            user_id=user.id,
            organization_id=user_in.organization_id,
            role=user_in.role or UserRole.MEMBER,
        )
        db.add(membership)
        db.commit()
        db.refresh(user)
        log_audit(
            db,
            user.id,
            "USER_REGISTER_DIRECT",
            request,
            context={"organization_id": str(user_in.organization_id), "role": str(user_in.role)},
        )
    else:
        # Create default Organization
        org_name = user_in.org_name or f"{user_in.full_name}'s Org"
        base_slug = slugify(org_name)

        # Ensure slug uniqueness
        slug = base_slug
        counter = 1
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(name=org_name, slug=slug)
        db.add(org)
        db.flush()  # Populate org.id

        # Bind user to organization as OWNER
        membership = UserOrganization(
            user_id=user.id, organization_id=org.id, role=UserRole.OWNER
        )
        db.add(membership)
        db.commit()
        db.refresh(user)

        log_audit(
            db,
            user.id,
            "USER_REGISTER",
            request,
            context={"organization": org_name, "slug": slug},
        )

    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, retrieve access and refresh tokens.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        log_audit(
            db,
            None,
            "USER_LOGIN_FAILED",
            request,
            context={"email": form_data.username, "reason": "Incorrect password"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        log_audit(
            db,
            user.id,
            "USER_LOGIN_FAILED",
            request,
            context={"email": form_data.username, "reason": "Inactive user account"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account"
        )

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    # Store refresh token in db
    store_refresh_token(db, refresh_token_str, user.id)

    log_audit(db, user.id, "USER_LOGIN", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str, request: Request, db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access and refresh tokens.
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type"
            )
        user_id = payload.get("sub")
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.id == user_uuid, User.is_active).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive"
        )

    try:
        new_refresh_token_str = rotate_refresh_token(db, refresh_token)
    except HTTPException as he:
        log_audit(
            db,
            user.id,
            "TOKEN_REFRESH_FAILED",
            request,
            context={"reason": he.detail},
        )
        raise he
    except Exception:
        log_audit(
            db,
            user.id,
            "TOKEN_REFRESH_FAILED",
            request,
            context={"reason": "Invalid refresh token db status"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    log_audit(db, user.id, "TOKEN_REFRESH", request)

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }


from api.core.deps import get_current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Revoke user's refresh tokens on logout.
    """
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False
    ).update({RefreshToken.is_revoked: True})
    db.commit()
    log_audit(db, current_user.id, "USER_LOGOUT", request)
    return {"success": True, "message": "Successfully logged out"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    email: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Generate recovery link for forgotten passwords.
    """
    user = db.query(User).filter(User.email == email, User.is_active).first()
    if user:
        token = create_access_token(user.id, expires_delta=timedelta(hours=2))
        reset_url = f"http://localhost:3000/auth/reset-password?token={token}"
        print(f"\n========================================")
        print(f"PASSWORD RESET REQUEST FOR {email}")
        print(f"Reset Link: {reset_url}")
        print(f"========================================\n")
        log_audit(db, user.id, "FORGOT_PASSWORD_REQUEST", request)
    return {"success": True, "message": "Password reset instructions sent if email exists"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    token: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Accept dynamic reset token and update user password.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(User.id == user_uuid, User.is_active).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive"
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    log_audit(db, user.id, "PASSWORD_RESET_SUCCESS", request)
    return {"success": True, "message": "Password successfully updated"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Verify user account email with token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user = db.query(User).filter(User.id == user_uuid, User.is_active).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive"
        )

    user.is_verified = True
    db.commit()
    log_audit(db, user.id, "EMAIL_VERIFICATION_SUCCESS", request)
    return {"success": True, "message": "Email successfully verified"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(
    email: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Resend validation link for user verification.
    """
    user = db.query(User).filter(User.email == email, User.is_active).first()
    if user:
        token = create_access_token(user.id, expires_delta=timedelta(days=1))
        verify_url = f"http://localhost:3000/auth/verify-email?token={token}"
        print(f"\n========================================")
        print(f"EMAIL VERIFICATION LINK FOR {email}")
        print(f"Verify Link: {verify_url}")
        print(f"========================================\n")
        log_audit(db, user.id, "EMAIL_VERIFICATION_RESENT", request)
    return {"success": True, "message": "Verification link sent if email exists"}


@router.get("/token-validation", response_model=UserResponse)
def token_validation(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Simple check endpoint that returns current user context if valid.
    """
    return current_user


@router.post("/password-change", status_code=status.HTTP_200_OK)
def password_change(
    old_password: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    For logged-in users to update their credentials.
    """
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    log_audit(db, current_user.id, "PASSWORD_CHANGED_BY_USER", request)
    return {"success": True, "message": "Password successfully changed"}


