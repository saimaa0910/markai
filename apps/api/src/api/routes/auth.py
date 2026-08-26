"""
EAIMOS Authentication Routes — Production-Ready
================================================
Complete auth module: register, login, logout, refresh, MFA, OAuth,
password management, email verification, session management, invitations.

Security Features:
- Account lockout (failed_login_count, locked_until)
- Login tracking (last_login_at, last_login_ip, login_count)
- TOTP MFA with recovery codes
- Family-based refresh token rotation
- Real email delivery
- Rate limiting via slowapi
"""

import base64
import hashlib
import io
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.deps import get_current_user, get_current_user_allow_inactive
from api.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from api.database.session import get_db
from api.models.auth import AuditLog, RefreshToken
from api.models.iam import UserSession
from api.models.membership import UserOrganization, UserRole
from api.models.organization import Organization
from api.models.user import User
from api.schemas.token import Token, RefreshTokenRequest
from api.schemas.user import UserCreate, UserResponse
from api.services.email_service import (
    send_password_reset_email,
    send_password_reset_success_email,
    send_verification_email,
    send_security_alert,
    send_welcome_email,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ─── Pydantic Request Models ──────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LogoutAllRequest(BaseModel):
    reason: Optional[str] = "logout_all"


class MFASetupRequest(BaseModel):
    pass


class MFAVerifyRequest(BaseModel):
    code: str


class MFALoginRequest(BaseModel):
    mfa_token: str
    code: str


class MFADisableRequest(BaseModel):
    password: str
    code: Optional[str] = None


class OAuthTokenRequest(BaseModel):
    provider: Optional[str] = None
    access_token: str
    id_token: Optional[str] = None
    invitation_token: Optional[str] = None


class InvitationActionRequest(BaseModel):
    token: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def log_audit(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    request: Optional[Request] = None,
    context: Optional[dict] = None,
    organization_id: Optional[uuid.UUID] = None,
    risk_level: str = "low",
) -> None:
    """Persist an immutable audit log entry.

    Phase 21 hardening:
    - Organization attribution so org-scoped audit queries (routes/audit.py)
      can surface auth events. Resolved from the X-Organization-Id header or
      the actor's first active membership when not supplied.
    - Audit logging is best-effort: a failure here must never break the
      primary request it is recording.
    """
    try:
        if organization_id is None:
            header_val = request.headers.get("x-organization-id") if request else None
            if header_val:
                try:
                    organization_id = uuid.UUID(header_val)
                except ValueError:
                    organization_id = None
        if organization_id is None and user_id is not None:
            from api.models.membership import UserOrganization

            membership = (
                db.query(UserOrganization)
                .filter(
                    UserOrganization.user_id == user_id,
                    UserOrganization.deleted_at == None,
                )
                .first()
            )
            if membership:
                organization_id = membership.organization_id

        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        description = f"Action: {action}"
        if context:
            description += f" - {context}"

        audit = AuditLog(
            organization_id=organization_id,
            actor_id=user_id,
            action=action,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            entity_type="users",
            entity_id=user_id,
            description=description[:255] if description else None,
            risk_level=risk_level,
        )
        db.add(audit)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to write audit log for action={action!r}: {exc}")


import httpx

def parse_user_agent(user_agent: str):
    user_agent = user_agent.lower()
    # OS
    if "windows" in user_agent:
        os = "Windows"
    elif "macintosh" in user_agent or "mac os" in user_agent:
        os = "macOS"
    elif "linux" in user_agent:
        os = "Linux"
    elif "iphone" in user_agent or "ipad" in user_agent:
        os = "iOS"
    elif "android" in user_agent:
        os = "Android"
    else:
        os = "Unknown OS"

    # Browser
    if "chrome" in user_agent or "chromium" in user_agent:
        browser = "Chrome"
    elif "firefox" in user_agent:
        browser = "Firefox"
    elif "safari" in user_agent:
        browser = "Safari"
    elif "edge" in user_agent:
        browser = "Edge"
    elif "opr/" in user_agent or "opera" in user_agent:
        browser = "Opera"
    else:
        browser = "Unknown Browser"

    # Device
    if "mobile" in user_agent or "iphone" in user_agent or "android" in user_agent:
        device = "Mobile"
    elif "tablet" in user_agent or "ipad" in user_agent:
        device = "Tablet"
    else:
        device = "Desktop"

    return device, browser, os


def resolve_location(ip: str) -> dict:
    default_loc = {
        "city": "Unknown City",
        "country": "Unknown Country",
        "country_code": "UN"
    }
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return {
            "city": "Localhost",
            "country": "Localhost",
            "country_code": "LH"
        }
    try:
        # Fetch from http://ip-api.com/json/ (free, no API key needed)
        resp = httpx.get(f"http://ip-api.com/json/{ip}", timeout=1.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "city": data.get("city", "Unknown City"),
                    "country": data.get("country", "Unknown Country"),
                    "country_code": (data.get("countryCode", "UN"))[:2]
                }
    except Exception:
        pass
    return default_loc


def check_for_login_alerts(db: Session, user: User, current_session: UserSession) -> None:
    ip = current_session.ip_address or "Unknown"
    ua = current_session.user_agent or "Unknown"
    device, browser, os = parse_user_agent(ua)
    
    loc = resolve_location(ip)
    current_session.city = loc["city"]
    current_session.country_code = (loc["country_code"] or "UN")[:2]
    db.add(current_session)
    db.flush()
    
    # Query past successful login sessions (exclude the current one)
    past_sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.id != current_session.id,
    ).all()
    
    if not past_sessions:
        # First login - send a standard login alert
        detail_msg = (
            f"Device: {device}\n"
            f"Browser: {browser}\n"
            f"OS: {os}\n"
            f"IP Address: {ip}\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Location: {loc['city']}, {loc['country']}"
        )
        try:
            send_security_alert(
                user.email,
                user.full_name,
                "New Login Detected",
                detail_msg
            )
        except Exception:
            pass
        return
        
    past_ips = {s.ip_address for s in past_sessions if s.ip_address}
    past_countries = {s.country_code for s in past_sessions if s.country_code}
    past_user_agents = [s.user_agent for s in past_sessions if s.user_agent]
    
    past_browsers = set()
    past_devices = set()
    for p_ua in past_user_agents:
        p_dev, p_brow, _ = parse_user_agent(p_ua)
        past_browsers.add(p_brow)
        past_devices.add(p_dev)
        
    new_ip = ip not in past_ips and ip != "127.0.0.1"
    new_country = current_session.country_code not in past_countries and current_session.country_code not in ("Unknown", "LH")
    new_browser = browser not in past_browsers and browser != "Unknown Browser"
    new_device = device not in past_devices and device != "Unknown Device"
    suspicious = (new_ip and new_country) or (new_country and new_device)
    
    trigger_alert = new_ip or new_country or new_browser or new_device or suspicious
    
    if trigger_alert:
        reasons = []
        if suspicious: reasons.append("Suspicious login pattern detected")
        if new_country: reasons.append(f"New country ({loc['country']})")
        if new_ip: reasons.append(f"New IP address ({ip})")
        if new_browser: reasons.append(f"New browser ({browser})")
        if new_device: reasons.append(f"New device ({device})")
        
        reason_str = ", ".join(reasons)
        
        detail_msg = (
            f"Alert Reason: {reason_str}\n\n"
            f"Device: {device}\n"
            f"Browser: {browser}\n"
            f"OS: {os}\n"
            f"IP Address: {ip}\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Location: {loc['city']}, {loc['country']}"
        )
        
        try:
            send_security_alert(
                user.email,
                user.full_name,
                f"Security Alert: New Login Detected ({reason_str})",
                detail_msg
            )
        except Exception:
            pass


def store_refresh_token(db: Session, token: str, user_id: uuid.UUID, request: Optional[Request] = None) -> uuid.UUID:
    """Store refresh token in DB and create UserSession. Returns session_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        jti = payload.get("jti")
        session_id = uuid.UUID(jti) if jti else uuid.uuid4()
    except Exception:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        session_id = uuid.uuid4()

    ip_address = "127.0.0.1"
    user_agent_str = "Unknown"
    if request:
        ip_address = request.client.host if request.client else "127.0.0.1"
        user_agent_str = request.headers.get("user-agent", "Unknown")

    # Get user's primary organization context
    m = db.query(UserOrganization).filter(
        UserOrganization.user_id == user_id,
        UserOrganization.deleted_at == None,
    ).first()
    org_id = m.organization_id if m else None

    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        session = UserSession(
            id=session_id,
            user_id=user_id,
            organization_id=org_id,
            ip_address=ip_address,
            user_agent=user_agent_str,
            expires_at=expires_at,
            last_active_at=datetime.now(timezone.utc),
            is_revoked=False,
        )
        db.add(session)
        db.flush()
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            check_for_login_alerts(db, user, session)

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        session_id=session_id,
        family_id=uuid.uuid4(),
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(db_token)
    db.commit()
    return session_id


def _revoke_token_family(db: Session, family_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Revoke every token in the family and every session of the user (Phase 11)."""
    db.query(RefreshToken).filter(RefreshToken.family_id == family_id).update(
        {"is_revoked": True, "is_used": True}
    )
    now = datetime.now(timezone.utc)
    db.query(UserSession).filter(UserSession.user_id == user_id).update(
        {"is_revoked": True, "revoked_at": now}
    )
    db.commit()


def rotate_refresh_token(
    db: Session, old_token_str: str, request: Optional[Request] = None
) -> str:
    old_hash = hashlib.sha256(old_token_str.encode("utf-8")).hexdigest()
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
    now = datetime.now(timezone.utc)
    if not db_token or db_token.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Phase 11: reuse detection. A token already consumed in a rotation cycle
    # (is_used=True) being presented again indicates possible theft → revoke the
    # entire family and every session of the user, then audit + alert.
    if db_token.is_used:
        _revoke_token_family(db, db_token.family_id, db_token.user_id)
        if request is not None:
            log_audit(
                db,
                db_token.user_id,
                "REFRESH_TOKEN_REUSE",
                request,
                {"family_id": str(db_token.family_id)},
            )
            try:
                user = db.query(User).filter(User.id == db_token.user_id).first()
                if user:
                    send_security_alert(
                        user.email,
                        user.full_name,
                        "Refresh token reuse detected",
                        "A previously rotated refresh token was presented again. "
                        "All sessions for this account have been revoked for security.",
                    )
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected; your session has been revoked for security",
        )

    if db_token.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Revoke old token
    db_token.is_revoked = True
    db_token.is_used = True
    db_token.used_at = now
    db.add(db_token)

    # Generate new refresh token
    new_token_str = create_refresh_token(db_token.user_id)

    try:
        payload = jwt.decode(new_token_str, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    except Exception:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    session_id = db_token.session_id

    new_db_token = RefreshToken(
        token_hash=hashlib.sha256(new_token_str.encode("utf-8")).hexdigest(),
        user_id=db_token.user_id,
        session_id=session_id,
        family_id=db_token.family_id,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(new_db_token)
    db.flush()

    db_token.replaced_by = new_db_token.id
    db.add(db_token)
    db.commit()

    return new_token_str


def _check_account_lockout(user: User, db: Session) -> None:
    """Raise 403 if account is currently locked."""
    if user.locked_until:
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > datetime.now(timezone.utc):
            remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to too many failed login attempts. Try again in {remaining} minutes.",
            )
        else:
            # Lock expired — reset
            user.locked_until = None
            user.failed_login_count = 0
            db.add(user)
            db.commit()


def _handle_failed_login(user: User, db: Session) -> None:
    """Increment failed login counter and lock account if threshold exceeded."""
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
    db.add(user)
    db.commit()


def _handle_successful_login(user: User, request: Optional[Request], db: Session) -> None:
    """Reset lockout counters and update login tracking on successful login."""
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.login_count = (user.login_count or 0) + 1
    if request and request.client:
        user.last_login_ip = request.client.host
    db.add(user)
    db.commit()


def _generate_recovery_codes(count: int = 10) -> List[str]:
    """Generate cryptographically secure numeric recovery codes."""
    return [str(secrets.randbelow(10**8)).zfill(8) for _ in range(count)]


def _create_email_verification_token(db: Session, user_id: uuid.UUID) -> str:
    """
    Create a single-use email verification token.
    Invalidates any previously unused tokens for this user.
    Returns the raw token (to be sent via email, not stored).
    """
    from api.models.email_verification import EmailVerificationToken

    # Invalidate all existing unused tokens for this user
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
        EmailVerificationToken.is_used == False,
    ).update({"is_used": True})

    # Generate new 128-bit secure token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    db_token = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        is_used=False,
    )
    db.add(db_token)
    db.commit()
    return raw_token


def _validate_and_consume_verification_token(
    db: Session, raw_token: str, request: Optional[Request] = None
) -> Optional[uuid.UUID]:
    """
    Validate a raw verification token.
    Returns user_id if valid, None otherwise.
    Marks token as used on success.
    """
    from api.models.email_verification import EmailVerificationToken

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db_token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.is_used == False,
    ).first()

    if not db_token:
        return None

    # Check expiry
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None

    # Consume token
    db_token.is_used = True
    db_token.used_at = datetime.now(timezone.utc)
    if request and request.client:
        db_token.ip_address = request.client.host
    db.add(db_token)
    db.commit()
    return db_token.user_id


def _create_password_reset_token(db: Session, user_id: uuid.UUID, ip_address: Optional[str] = None) -> str:
    """
    Create a single-use password reset token.
    Invalidates any previously unused reset tokens for this user.
    Returns the raw token (to be sent via email, not stored).
    """
    from api.models.iam import PasswordResetToken

    # Invalidate all existing unused reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.is_used == False,
    ).update({"is_used": True})

    # Generate new 128-bit secure token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    db_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        is_used=False,
        ip_address=ip_address,
    )
    db.add(db_token)
    db.commit()
    return raw_token


def _validate_and_consume_password_reset_token(
    db: Session, raw_token: str
) -> Optional[uuid.UUID]:
    """
    Validate a raw password reset token.
    Returns user_id if valid, None otherwise.
    Marks token as used on success.
    """
    from api.models.iam import PasswordResetToken

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False,
    ).first()

    if not db_token:
        return None

    # Check expiry
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None

    # Consume token
    db_token.is_used = True
    db_token.used_at = datetime.now(timezone.utc)
    db.add(db_token)
    db.commit()
    return db_token.user_id


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)) -> Any:
    """Register a new user. Creates default org, or joins org via invitation token."""
    existing_user = db.query(User).filter(User.email == user_in.email, User.deleted_at.is_(None)).first()

    # Resolve invitation
    invitation = None
    if user_in.invitation_token:
        invitation = _find_pending_invitation(db, user_in.invitation_token)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token.")
        if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token.")
        # Phase 10: the registering email must match the invited email, so an
        # invite cannot be claimed by an unrelated address.
        if invitation.email and invitation.email.lower() != user_in.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation was issued to a different email address",
            )

    # Check if we can update a pre-created temporary user
    is_temp_user = False
    if existing_user:
        metadata = existing_user.metadata_json or {}
        if metadata.get("is_temporary_password"):
            is_temp_user = True
        else:
            log_audit(db, None, "USER_REGISTER_FAILED", request, {"email": user_in.email, "reason": "Email already exists"})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The user with this email already exists.")

    hashed_password = get_password_hash(user_in.password)

    if is_temp_user:
        user = existing_user
        user.full_name = user_in.full_name
        user.hashed_password = hashed_password
        user.is_active = True
        user.is_verified = True if invitation else False
        # Clean up metadata
        metadata = user.metadata_json or {}
        new_metadata = {k: v for k, v in metadata.items() if k not in ("is_temporary_password", "change_password_required")}
        user.metadata_json = new_metadata
        db.add(user)
    else:
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False,
            is_verified=True if (invitation or settings.ENVIRONMENT == "test") else False,
        )
        db.add(user)

    db.flush()

    if invitation:
        membership = UserOrganization(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(membership)
        invitation.is_accepted = True
        db.add(invitation)
        db.commit()
        db.refresh(user)
        log_audit(db, user.id, "USER_REGISTER_INVITATION", request, {"organization_id": str(invitation.organization_id)})
    else:
        org_name = user_in.org_name or f"{user_in.full_name}'s Organization"
        base_slug = slugify(org_name)
        slug = base_slug
        counter = 1
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(name=org_name, slug=slug)
        db.add(org)
        db.flush()

        membership = UserOrganization(
            user_id=user.id,
            organization_id=org.id,
            role=UserRole.OWNER,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(membership)
        db.commit()
        db.refresh(user)
        log_audit(db, user.id, "USER_REGISTER", request, {"organization": org_name})

    # Send verification email using secure DB token (non-blocking)
    if not user.is_verified:
        try:
            raw_token = _create_email_verification_token(db, user.id)
            verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_token}"
            send_verification_email(user.email, user.full_name, verify_url)
        except Exception as e:
            import logging
            logging.getLogger("eaimos.auth").warning(f"Failed to send verification email: {e}")

    return user


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """Login endpoint. Accepts JSON (email/password) or form (username/password).

    Enforces lockout (403), rate limiting (429), tracks logins, issues token pair.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        username = payload.get("email") or payload.get("username")
        password = payload.get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    from api.models.security import RateLimitLog

    # Deterministic short identifier so it fits the varchar(45) ip_address column.
    rl_identifier = hashlib.sha256(username.encode("utf-8")).hexdigest()[:40]

    now = datetime.now(timezone.utc)
    # Rate limit (per-identifier sliding window) — check BEFORE lockout so the
    # 6th rapid failed attempt returns 429, while a pre-set lock returns 403.
    recent_count = db.query(RateLimitLog).filter(
        RateLimitLog.endpoint == "login",
        RateLimitLog.ip_address == rl_identifier,
        RateLimitLog.window_end > now,
    ).count()
    if recent_count >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = db.query(User).filter(User.email == username).first()

    if not user or not user.hashed_password:
        log_audit(db, None, "USER_LOGIN_FAILED", request, {"email": username, "reason": "User not found"}, risk_level="medium")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Check account lockout BEFORE verifying password (prevents timing attacks on lock status)
    _check_account_lockout(user, db)

    if not verify_password(password, user.hashed_password):
        _handle_failed_login(user, db)
        # Record the failed attempt for rate limiting
        db.add(RateLimitLog(
            endpoint="login",
            ip_address=rl_identifier,
            user_id=user.id,
            attempt_count=1,
            window_start=now,
            window_end=now + timedelta(seconds=300),
            blocked=False,
        ))
        db.commit()
        log_audit(db, user.id, "USER_LOGIN_FAILED", request, {"reason": "Incorrect password"}, risk_level="medium")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        scheduled = user.scheduled_deletion_at
        if scheduled and scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        is_pending_deletion = (
            user.deletion_requested_at is not None
            and scheduled is not None
            and scheduled > datetime.now(timezone.utc)
        )
        if not is_pending_deletion:
            log_audit(db, user.id, "USER_LOGIN_FAILED", request, {"reason": "Inactive account"}, risk_level="medium")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    # Verify email before issuing tokens (unverified accounts cannot log in).
    # Exception: temporary-password invitees sign in once with the
    # admin-issued temp password before verifying their email address
    # (login is then gated behind a forced password change).
    temp_expires = getattr(user, "temporary_password_expires_at", None)
    if temp_expires and temp_expires.tzinfo is None:
        temp_expires = temp_expires.replace(tzinfo=timezone.utc)
    using_temp_password = bool(
        getattr(user, "change_password_required", False)
        and getattr(user, "temporary_password", None)
        and (temp_expires is None or temp_expires > datetime.now(timezone.utc))
    )
    if not user.is_verified and not using_temp_password:
        log_audit(db, user.id, "USER_LOGIN_FAILED", request, {"reason": "Email not verified"}, risk_level="medium")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified")

    # Check if MFA is enabled
    if user.mfa_enabled:
        mfa_payload = {
            "sub": str(user.id),
            "type": "mfa_pending",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        mfa_token = jwt.encode(mfa_payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        log_audit(db, user.id, "USER_LOGIN_MFA_REQUIRED", request)
        return {
            "mfa_required": True,
            "mfa_token": mfa_token,
        }

    # Successful login (no MFA)
    _handle_successful_login(user, request, db)

    refresh_token_str = create_refresh_token(user.id)
    session_id = store_refresh_token(db, refresh_token_str, user.id, request)
    access_token = create_access_token(user.id, token_id=session_id)

    log_audit(db, user.id, "login", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/restore-account", status_code=status.HTTP_200_OK)
def auth_restore_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_allow_inactive),
) -> Any:
    """Proxy route to restore inactive account using auth routing prefix."""
    from api.routes.users import restore_account
    return restore_account(request=request, db=db, current_user=current_user)


# ─── Get Me ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get the currently authenticated user's profile."""
    from api.routes.users import resolve_user_response
    return resolve_user_response(current_user, db)


# ─── Refresh ─────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=Token)
def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """Rotate the refresh token and issue a new access token."""
    refresh_token = body.refresh_token
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
        user_id = payload.get("sub")
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")

    try:
        new_refresh_token_str = rotate_refresh_token(db, refresh_token, request)
    except HTTPException as he:
        log_audit(db, user.id, "TOKEN_REFRESH_FAILED", request, {"reason": he.detail}, risk_level="medium")
        raise he

    log_audit(db, user.id, "TOKEN_REFRESH", request)
    session_id = None
    old_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    old_db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
    if old_db_token:
        session_id = old_db_token.session_id

    return {
        "access_token": create_access_token(user.id, token_id=session_id),
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }


# ─── Logout ───────────────────────────────────────────────────────────────────

def _get_current_session_id(request: Request) -> Optional[uuid.UUID]:
    """Extract the current session ID from the request's access token."""
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            claim = payload.get("session_id") or payload.get("jti")
            if claim:
                return uuid.UUID(str(claim))
    except (JWTError, ValueError):
        pass
    return None


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Revoke the current session and its associated refresh tokens."""
    session_id = _get_current_session_id(request)
    now = datetime.now(timezone.utc)

    # If the token's session claim does not match a real session owned by this
    # user (e.g. a jti-only token), fall back to revoking all of their tokens.
    if session_id:
        real_session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        ).first()
        if not real_session:
            session_id = None

    # Phase 2: logout must revoke the active UserSession, not just tokens.
    if session_id:
        db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False,
        ).update({
            UserSession.is_revoked: True,
            UserSession.revoked_at: now,
            UserSession.revocation_reason: "logout",
        })

    # Revoke refresh tokens scoped to this session (fall back to all user tokens).
    if session_id:
        token_query = db.query(RefreshToken).filter(
            RefreshToken.session_id == session_id,
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
        )
    else:
        token_query = db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
        )
    token_query.update({RefreshToken.is_revoked: True})

    db.commit()
    log_audit(db, current_user.id, "USER_LOGOUT", request)
    return {"success": True, "message": "Successfully logged out"}


# ─── Logout All Devices ───────────────────────────────────────────────────────

@router.post("/logout-all", status_code=status.HTTP_200_OK)
def logout_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Revoke ALL refresh tokens and sessions for the current user."""
    # Revoke all refresh tokens
    revoked_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,
    ).update({RefreshToken.is_revoked: True})

    # Revoke all sessions
    now = datetime.now(timezone.utc)
    revoked_sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    ).update({
        UserSession.is_revoked: True,
        UserSession.revoked_at: now,
        UserSession.revocation_reason: "logout_all",
    })

    db.commit()
    log_audit(db, current_user.id, "USER_LOGOUT_ALL", request, {"sessions": revoked_sessions, "tokens": revoked_tokens})
    return {"success": True, "message": f"Successfully logged out {revoked_sessions} sessions on all devices"}


# ─── Token Validation ─────────────────────────────────────────────────────────

@router.get("/token-validation", response_model=UserResponse)
def token_validation(current_user: User = Depends(get_current_user)) -> Any:
    """Check token validity and return current user."""
    return current_user


# ─── Forgot Password ─────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    request: Request,
    body: Optional[ForgotPasswordRequest] = None,
    email: Optional[EmailStr] = None,
    db: Session = Depends(get_db),
) -> Any:
    """Send password reset email to the user."""
    target_email = email
    if body and body.email:
        target_email = body.email

    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    user = db.query(User).filter(User.email == target_email, User.is_active == True).first()
    if user:
        raw_token = _create_password_reset_token(db, user.id, ip_address=request.client.host if request.client else None)
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
        try:
            send_password_reset_email(user.email, user.full_name, reset_url)
        except Exception as e:
            import logging
            logging.getLogger("eaimos.auth").error(f"Failed to send reset email: {e}")
        log_audit(db, user.id, "FORGOT_PASSWORD_REQUEST", request)
    # Always return success to prevent email enumeration
    return {"success": True, "message": "If an account exists with that email, a reset link has been sent."}


# ─── Reset Password ───────────────────────────────────────────────────────────

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    request: Request,
    body: Optional[ResetPasswordRequest] = None,
    token: Optional[str] = None,
    new_password: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """Reset password using the token from the reset email."""
    target_token = token
    target_password = new_password
    if body:
        if body.token:
            target_token = body.token
        if body.new_password:
            target_password = body.new_password

    if not target_token or not target_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token and new password are required")

    # Try DB-backed hashed token first
    user_uuid = _validate_and_consume_password_reset_token(db, target_token)

    if not user_uuid:
        # Fallback to legacy JWT token decoding (backward compatibility)
        try:
            payload = jwt.decode(target_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            user_uuid = uuid.UUID(str(user_id))
        except (JWTError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or inactive")

    if len(target_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")

    user.hashed_password = get_password_hash(target_password)
    user.password_changed_at = datetime.now(timezone.utc)

    # Phase 3: password reset revokes ALL sessions (revoking old access
    # tokens) and all refresh tokens, logging the user out everywhere.
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.is_revoked == False
    ).update({RefreshToken.is_revoked: True})
    db.query(UserSession).filter(
        UserSession.user_id == user.id, UserSession.is_revoked == False
    ).update({
        UserSession.is_revoked: True,
        UserSession.revoked_at: now,
        UserSession.revocation_reason: "password_reset",
    })
    db.commit()
    try:
        send_password_reset_success_email(user.email, user.full_name)
    except Exception as e:
        import logging
        logging.getLogger("eaimos.auth").error(f"Failed to send password reset success email: {e}")
    log_audit(db, user.id, "PASSWORD_RESET_SUCCESS", request)
    return {"success": True, "message": "Password successfully updated. Please sign in with your new password."}


# ─── Verify Email ─────────────────────────────────────────────────────────────

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(
    request: Request,
    body: Optional[VerifyEmailRequest] = None,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """Verify user's email address using the secure single-use DB token."""
    target_token = token
    if body and body.token:
        target_token = body.token

    if not target_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is required")

    # Try DB token first (new secure flow)
    user_id = _validate_and_consume_verification_token(db, target_token, request)

    if not user_id:
        # Fallback: try legacy JWT token (backwards compat for tokens already in-flight)
        try:
            payload = jwt.decode(target_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            user_id = uuid.UUID(str(sub))
        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token. Please request a new one.",
            )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or inactive")

    if user.is_verified:
        return {"success": True, "message": "Email already verified"}

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    log_audit(db, user.id, "EMAIL_VERIFICATION_SUCCESS", request)

    # Send welcome email
    try:
        send_welcome_email(user.email, user.full_name)
    except Exception:
        pass

    return {"success": True, "message": "Email successfully verified. Welcome to EAIMOS!"}


# ─── Resend Verification ─────────────────────────────────────────────────────

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(
    request: Request,
    body: Optional[ResendVerificationRequest] = None,
    email: Optional[EmailStr] = None,
    db: Session = Depends(get_db),
) -> Any:
    """Resend email verification link."""
    target_email = email
    if body and body.email:
        target_email = body.email

    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    user = db.query(User).filter(User.email == target_email, User.is_active == True).first()
    if user and not user.is_verified:
        try:
            raw_token = _create_email_verification_token(db, user.id)
            verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_token}"
            send_verification_email(user.email, user.full_name, verify_url)
        except Exception as e:
            import logging
            logging.getLogger("eaimos.auth").error(f"Failed to resend verification email: {e}")
        log_audit(db, user.id, "EMAIL_VERIFICATION_RESENT", request)
    # Always return success to prevent enumeration
    return {"success": True, "message": "If an unverified account exists with that email, a verification link has been sent."}



# ─── MFA Setup ────────────────────────────────────────────────────────────────

@router.post("/mfa/setup", status_code=status.HTTP_200_OK)
def mfa_setup(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Initiate TOTP MFA setup.
    Returns TOTP secret, provisioning URI, and QR code as base64 PNG.
    """
    if current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled for this account")

    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Build provisioning URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name=settings.MFA_ISSUER,
    )

    # Generate QR code as base64
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Store secret temporarily (unconfirmed — stored as pending)
    # We store in mfa_secret but mfa_enabled stays False until /mfa/verify
    current_user.mfa_secret = secret
    current_user.mfa_method = "totp"
    db.commit()

    log_audit(db, current_user.id, "MFA_SETUP_INITIATED", request)
    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code": f"data:image/png;base64,{qr_base64}",
    }


@router.post("/mfa/verify", status_code=status.HTTP_200_OK)
def mfa_verify(
    body: MFAVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Verify TOTP code and enable MFA on the account.
    Also generates and returns one-time recovery codes.
    """
    if current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled")

    if not current_user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA setup not initiated. Call /auth/mfa/setup first.")

    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code. Please try again.")

    # Enable MFA
    current_user.mfa_enabled = True
    current_user.mfa_method = "totp"

    # Generate recovery codes and store as hashed list in preferences
    recovery_codes = _generate_recovery_codes(settings.MFA_RECOVERY_CODE_COUNT)
    hashed_codes = [hashlib.sha256(c.encode()).hexdigest() for c in recovery_codes]

    prefs = current_user.preferences or {}
    prefs["mfa_recovery_codes"] = hashed_codes
    prefs["mfa_recovery_codes_remaining"] = len(recovery_codes)
    current_user.preferences = prefs

    db.commit()
    try:
        send_security_alert(
            current_user.email,
            current_user.full_name,
            "MFA Enabled",
            "Two-factor authentication (TOTP) has been successfully enabled on your account. Recovery codes have been generated."
        )
    except Exception as e:
        import logging
        logging.getLogger("eaimos.auth").error(f"Failed to send MFA enabled alert email: {e}")
    log_audit(db, current_user.id, "MFA_ENABLED", request)

    return {
        "success": True,
        "message": "MFA successfully enabled",
        "recovery_codes": recovery_codes,
        "warning": "Store these recovery codes securely. They will NOT be shown again.",
    }


@router.post("/mfa/disable", status_code=status.HTTP_200_OK)
def mfa_disable(
    body: MFADisableRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Disable MFA. Requires current password."""
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled on this account")

    if not current_user.hashed_password or not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_method = None

    prefs = current_user.preferences or {}
    prefs.pop("mfa_recovery_codes", None)
    prefs.pop("mfa_recovery_codes_remaining", None)
    current_user.preferences = prefs

    db.commit()
    try:
        send_security_alert(
            current_user.email,
            current_user.full_name,
            "MFA Disabled",
            "Two-factor authentication (TOTP) has been disabled on your account. If you did not perform this action, please secure your account immediately."
        )
    except Exception as e:
        import logging
        logging.getLogger("eaimos.auth").error(f"Failed to send MFA disabled alert email: {e}")
    log_audit(db, current_user.id, "MFA_DISABLED", request, risk_level="medium")
    return {"success": True, "message": "MFA has been disabled"}


@router.get("/mfa/status", status_code=status.HTTP_200_OK)
def mfa_status(current_user: User = Depends(get_current_user)) -> Any:
    """Get current MFA status for the authenticated user."""
    prefs = current_user.preferences or {}
    remaining = prefs.get("mfa_recovery_codes_remaining", 0)
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_method": current_user.mfa_method,
        "recovery_codes_remaining": remaining if current_user.mfa_enabled else 0,
    }


@router.post("/mfa/login", response_model=Token)
def mfa_login(
    body: MFALoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """Validate TOTP or recovery code and finalize login, returning tokens."""
    try:
        payload = jwt.decode(body.mfa_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "mfa_pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA token type")
        user_id = payload.get("sub")
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired MFA login token")

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")

    # Verify TOTP code or recovery code
    is_valid = False
    if user.mfa_secret and len(body.code) == 6:
        totp = pyotp.TOTP(user.mfa_secret)
        is_valid = totp.verify(body.code, valid_window=1)

    # Check recovery codes if TOTP failed
    if not is_valid:
        prefs = user.preferences or {}
        hashed_codes = prefs.get("mfa_recovery_codes", [])
        input_hash = hashlib.sha256(body.code.encode()).hexdigest()
        if input_hash in hashed_codes:
            # Consume recovery code
            hashed_codes.remove(input_hash)
            prefs["mfa_recovery_codes"] = hashed_codes
            prefs["mfa_recovery_codes_remaining"] = len(hashed_codes)
            user.preferences = prefs
            db.add(user)
            db.commit()
            is_valid = True

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    # Successful login
    _handle_successful_login(user, request, db)
    refresh_token_str = create_refresh_token(user.id)
    session_id = store_refresh_token(db, refresh_token_str, user.id, request)
    access_token = create_access_token(user.id, token_id=session_id)



    log_audit(db, user.id, "USER_LOGIN_MFA_SUCCESS", request)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


# ─── OAuth ────────────────────────────────────────────────────────────────────

@router.post("/oauth/{provider}", status_code=status.HTTP_200_OK)
def oauth_token_exchange(
    provider: str,
    body: OAuthTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth token exchange endpoint.
    Frontend passes the provider access token; backend validates it,
    finds or creates a user, and returns EAIMOS JWT tokens.
    """
    SUPPORTED_PROVIDERS = {"google", "microsoft", "github", "okta"}
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported OAuth provider: {provider}")

    # Validate token and extract user info from provider
    user_info = _validate_oauth_token(provider, body.access_token, body.id_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid {provider} token")

    provider_email = user_info.get("email")
    provider_name = user_info.get("name", provider_email)
    provider_user_id = user_info.get("sub") or user_info.get("id")

    if not provider_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider did not return email")

    # Find or create user
    user = db.query(User).filter(User.email == provider_email).first()
    if not user:
        # Check if invitation token is provided
        invitation = None
        if body.invitation_token:
            from api.models.membership import OrganizationInvitation
            invitation = _find_pending_invitation(db, body.invitation_token)
            if invitation and invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
                invitation = None
            # Phase 10: OAuth email must match the invited email.
            if invitation and invitation.email and invitation.email.lower() != provider_email.lower():
                invitation = None

        # Auto-provision user from OAuth
        user = User(
            email=provider_email,
            full_name=provider_name or provider_email,
            hashed_password=None,  # OAuth-only account
            is_active=True,
            is_verified=True,  # Email verified by OAuth provider
            is_superuser=False,
        )
        db.add(user)
        db.flush()

        if invitation:
            # Bind user to the invitation's organization
            membership = UserOrganization(
                user_id=user.id,
                organization_id=invitation.organization_id,
                role=invitation.role,
                joined_at=datetime.now(timezone.utc),
            )
            db.add(membership)
            invitation.is_accepted = True
            db.add(invitation)
            db.commit()
            log_audit(db, user.id, f"OAUTH_USER_PROVISIONED_INVITATION_{provider.upper()}", request)
        else:
            # Create default org
            org_name = f"{provider_name or provider_email}'s Organization"
            base_slug = slugify(org_name)
            slug = base_slug
            counter = 1
            while db.query(Organization).filter(Organization.slug == slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            org = Organization(name=org_name, slug=slug)
            db.add(org)
            db.flush()

            membership = UserOrganization(
                user_id=user.id,
                organization_id=org.id,
                role=UserRole.OWNER,
                joined_at=datetime.now(timezone.utc),
            )
            db.add(membership)
            db.commit()
            log_audit(db, user.id, f"OAUTH_USER_PROVISIONED_{provider.upper()}", request)

    # Store OAuth account link
    from api.models.iam import OAuthAccount
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.provider == provider,
        OAuthAccount.user_id == user.id,
    ).first()
    if not oauth_account:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=str(provider_user_id),
            provider_email=provider_email,
            provider_data=user_info,
        )
        db.add(oauth_account)
        db.commit()

    _handle_successful_login(user, request, db)
    refresh_token_str = create_refresh_token(user.id)
    session_id = store_refresh_token(db, refresh_token_str, user.id, request)
    access_token = create_access_token(user.id, token_id=session_id)
    log_audit(db, user.id, f"OAUTH_LOGIN_{provider.upper()}", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


def _validate_oauth_token(provider: str, access_token: str, id_token: Optional[str] = None) -> Optional[dict]:
    """Validate OAuth token with the provider and return user info."""
    # Local development bypass for testing & UI compatibility
    if settings.ENVIRONMENT == "test" and access_token.startswith("mock_"):
        email = f"{access_token.replace('mock_', '')}@example.com"
        name = access_token.replace('mock_', '').replace('_', ' ').title()
        return {
            "email": email,
            "name": name,
            "sub": f"mock_sub_{access_token}",
        }

    import httpx
    try:
        if provider == "google":
            # Verify with Google's tokeninfo endpoint
            resp = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()

        elif provider == "github":
            resp = httpx.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github.v3+json"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                # GitHub may not return email in main response — fetch emails
                if not data.get("email"):
                    email_resp = httpx.get(
                        "https://api.github.com/user/emails",
                        headers={"Authorization": f"token {access_token}"},
                        timeout=10.0,
                    )
                    if email_resp.status_code == 200:
                        emails = email_resp.json()
                        primary = next((e["email"] for e in emails if e.get("primary")), None)
                        data["email"] = primary
                data["sub"] = str(data.get("id"))
                return data

        elif provider == "microsoft":
            resp = httpx.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["email"] = data.get("mail") or data.get("userPrincipalName")
                data["sub"] = data.get("id")
                return data

        elif provider == "okta":
            # Okta userinfo — requires OKTA_DOMAIN to be configured
            okta_domain = getattr(settings, "OKTA_DOMAIN", "")
            if okta_domain:
                resp = httpx.get(
                    f"https://{okta_domain}/oauth2/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json()

    except Exception as e:
        import logging
        logging.getLogger("eaimos.auth").error(f"OAuth token validation failed for {provider}: {e}")

    return None


# ─── Invitations ─────────────────────────────────────────────────────────────

def _find_pending_invitation(db: Session, token: str):
    """
    Locate a pending (unaccepted, unrejected) invitation.
    Tolerates both a raw plaintext token and a stored SHA-256 hash so clients
    may present either representation (Phase 8.4/10).
    """
    from api.models.membership import OrganizationInvitation

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    for candidate in (token_hash, token):
        invitation = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.token == candidate,
                OrganizationInvitation.is_accepted == False,
                OrganizationInvitation.is_rejected == False,
            )
            .first()
        )
        if invitation:
            return invitation
    return None


@router.get("/invitations/{token}", status_code=status.HTTP_200_OK)
def get_invitation(token: str, db: Session = Depends(get_db)) -> Any:
    """Get invitation details by token (public endpoint for invitation preview)."""
    invitation = _find_pending_invitation(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already used")

    if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation has expired")

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    return {
        "token": token,
        "email": invitation.email,
        "role": invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
        "organization_name": org.name if org else "Unknown",
        "organization_id": str(invitation.organization_id),
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
    }


@router.post("/invitations/accept", status_code=status.HTTP_200_OK)
def accept_invitation(
    body: InvitationActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Accept an organization invitation for the currently authenticated user."""
    invitation = _find_pending_invitation(db, body.token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already used")

    if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation has expired")

    # Phase 10: bind the invitation to the authenticated user's email so an
    # invite intended for one address cannot be claimed by another account.
    if invitation.email and invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was issued to a different email address",
        )

    # Check not already a member
    existing = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == invitation.organization_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already a member of this organization")

    membership = UserOrganization(
        user_id=current_user.id,
        organization_id=invitation.organization_id,
        role=invitation.role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    invitation.is_accepted = True
    db.add(invitation)
    db.commit()

    # Notify inviter of acceptance
    try:
        org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
        org_name = org.name if org else "the organization"
        inviter = db.query(User).filter(User.id == invitation.invited_by).first()
        if inviter:
            from api.services.email_service import send_invitation_accepted_email
            send_invitation_accepted_email(inviter.email, current_user.full_name, current_user.email, org_name)
    except Exception as exc:
        import logging
        logging.getLogger("eaimos.auth").error(f"Failed to send acceptance email: {exc}")

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    log_audit(db, current_user.id, "INVITATION_ACCEPTED", request, {"organization_id": str(invitation.organization_id)})
    return {
        "success": True,
        "message": f"Successfully joined {org.name if org else 'the organization'}",
        "organization_id": str(invitation.organization_id),
        "role": invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
    }


@router.post("/invitations/reject", status_code=status.HTTP_200_OK)
def reject_invitation(
    body: InvitationActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Reject an organization invitation."""
    invitation = _find_pending_invitation(db, body.token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already used")

    # Phase 10: only the invited email's owner may reject the invitation.
    if invitation.email and invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was issued to a different email address",
        )

    invitation.is_rejected = True
    db.commit()

    # Notify inviter of rejection
    try:
        org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
        org_name = org.name if org else "the organization"
        inviter = db.query(User).filter(User.id == invitation.invited_by).first()
        if inviter:
            from api.services.email_service import send_invitation_rejected_email
            send_invitation_rejected_email(inviter.email, invitation.email, org_name)
    except Exception as exc:
        import logging
        logging.getLogger("eaimos.auth").error(f"Failed to send rejection email: {exc}")
    return {"success": True, "message": "Invitation declined"}
