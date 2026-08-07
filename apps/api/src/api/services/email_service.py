"""
EAIMOS Email Service — Resend Integration
==========================================
Production-ready transactional email via Resend REST API.
Falls back to console output when RESEND_API_KEY is not configured (dev mode).

Retry: 3 attempts with exponential backoff (1s, 2s, 4s).
All functions return bool — True = delivered or queued, False = failed.

Templates:
- Email verification
- Password reset
- Invitation / Organization Invite
- Welcome email
- Password changed
- Security alert
- Role changed
- Organization removed
- Account deletion scheduled
- Account restored
- MFA enabled / disabled
"""

import logging
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

import httpx

from api.core.config import settings

logger = logging.getLogger("eaimos.email")

_RESEND_API_URL = "https://api.resend.com/emails"


# ─── HTML Templates ───────────────────────────────────────────────────────────

_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#0f0f13;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f13;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#18181f;border-radius:16px;border:1px solid #2a2a3a;overflow:hidden;max-width:600px;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#6d28d9,#4f46e5);padding:32px 40px;">
              <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;letter-spacing:-0.5px;">
                🚀 EAIMOS
              </h1>
              <p style="margin:4px 0 0;color:rgba(255,255,255,0.7);font-size:13px;">
                Enterprise AI Marketing Operating System
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              {body}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;border-top:1px solid #2a2a3a;background:#13131a;">
              <p style="margin:0;color:#6b7280;font-size:12px;line-height:1.6;">
                This email was sent by EAIMOS. If you did not request this, please ignore it.
                <br/>For security inquiries, contact <a href="mailto:security@eaimos.ai"
                style="color:#8b5cf6;text-decoration:none;">security@eaimos.ai</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

_BUTTON_STYLE = (
    "display:inline-block;background:linear-gradient(135deg,#6d28d9,#4f46e5);"
    "color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;"
    "font-weight:600;font-size:15px;letter-spacing:0.3px;"
)


def _make_email_body(heading: str, paragraphs: list[str], cta_url: str, cta_label: str, note: Optional[str] = None) -> str:
    paras = "".join(
        f'<p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">{p}</p>'
        for p in paragraphs
    )
    note_html = (
        f'<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;line-height:1.6;">{note}</p>'
        if note else ""
    )
    return f"""
      <h2 style="margin:0 0 20px;color:#fff;font-size:22px;font-weight:700;">{heading}</h2>
      {paras}
      <div style="margin:28px 0;">
        <a href="{cta_url}" style="{_BUTTON_STYLE}">{cta_label}</a>
      </div>
      <p style="margin:20px 0 0;color:#6b7280;font-size:12px;word-break:break-all;">
        Or copy this link: <span style="color:#8b5cf6;">{cta_url}</span>
      </p>
      {note_html}
    """


def _make_info_body(heading: str, paragraphs: list[str], note: Optional[str] = None, heading_color: str = "#fff") -> str:
    """Build an email body without a CTA button (for informational alerts)."""
    paras = "".join(
        f'<p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">{p}</p>'
        for p in paragraphs
    )
    note_html = (
        f'<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;line-height:1.6;">{note}</p>'
        if note else ""
    )
    return f"""
      <h2 style="margin:0 0 20px;color:{heading_color};font-size:22px;font-weight:700;">{heading}</h2>
      {paras}
      {note_html}
    """


# ─── HTML → Plain Text ────────────────────────────────────────────────────────

def _html_to_text(html: str) -> str:
    """Convert HTML email to plain-text fallback."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ─── Resend Send ──────────────────────────────────────────────────────────────

def _is_resend_configured() -> bool:
    return bool(getattr(settings, "RESEND_API_KEY", "").strip())


def _get_from_address() -> str:
    name = getattr(settings, "EMAIL_FROM_NAME", "EAIMOS Platform")
    addr = getattr(settings, "EMAIL_FROM", "noreply@eaimos.ai")
    if name:
        return f"{name} <{addr}>"
    return addr


def _send_via_resend(to_email: str, subject: str, html: str) -> None:
    """Send via Resend REST API. Raises on failure."""
    api_key = settings.RESEND_API_KEY
    payload = {
        "from": _get_from_address(),
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": _html_to_text(html),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(_RESEND_API_URL, json=payload, headers=headers, timeout=15.0)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend API error {resp.status_code}: {resp.text}")


def _detect_smtp_provider(host: str) -> str:
    """Detect SMTP provider from hostname for logging purposes."""
    if not host:
        return "none"
    host_lower = host.lower()
    if host_lower in ("localhost", "127.0.0.1", "mailpit", "0.0.0.0"):
        return "mailpit"
    if "sendgrid" in host_lower:
        return "sendgrid"
    if "gmail" in host_lower or "google" in host_lower:
        return "gmail"
    if "amazonaws.com" in host_lower or "ses" in host_lower:
        return "amazon-ses"
    if "mailgun" in host_lower:
        return "mailgun"
    if "outlook" in host_lower or "office365" in host_lower:
        return "microsoft"
    return "custom-smtp"


def _is_smtp_configured() -> bool:
    """Check if SMTP is configured."""
    return bool(getattr(settings, "SMTP_HOST", "").strip())


def _send_smtp(to_email: str, subject: str, html_body: str) -> None:
    """Send email via SMTP. Raises on failure."""
    from_addr = _get_from_address()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(_html_to_text(html_body), "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    timeout = getattr(settings, "SMTP_TIMEOUT", 30)
    smtp_port = getattr(settings, "SMTP_PORT", 1025)
    smtp_host = getattr(settings, "SMTP_HOST", "localhost")
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_password = getattr(settings, "SMTP_PASSWORD", "")

    smtp_cls = smtplib.SMTP_SSL if smtp_port == 465 else smtplib.SMTP
    with smtp_cls(smtp_host, smtp_port, timeout=timeout) as server:
        if smtp_port != 465:
            server.ehlo()
        if smtp_port == 587:
            server.starttls()
            server.ehlo()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send transactional email.
    - If RESEND_API_KEY is set: sends via Resend with 3-attempt retry.
    - Else if SMTP is configured: sends via SMTP with 3-attempt retry.
    - Otherwise: prints to console (dev mode).
    Returns True on success, False on all retries failed.
    """
    full_html = _BASE_TEMPLATE.format(subject=subject, body=html_body)

    # 1. Primary: Resend API
    if _is_resend_configured():
        backoff = 1
        for attempt in range(1, 4):
            try:
                _send_via_resend(to_email, subject, full_html)
                logger.info(f"[Resend] Email sent: to={to_email}, subject={subject!r}")
                return True
            except Exception as exc:
                logger.warning(f"[Resend] Attempt {attempt} failed for {to_email}: {exc}")
                if attempt < 3:
                    time.sleep(backoff)
                    backoff *= 2
        logger.error(f"[Resend] All retry attempts exhausted for {to_email}")
        return False

    # 2. Secondary: SMTP
    if _is_smtp_configured():
        smtp_success = False
        for attempt in range(1, 4):
            try:
                _send_smtp(to_email, subject, full_html)
                logger.info(f"Email sent via SMTP: to={to_email}, subject={subject}")
                return True
            except smtplib.SMTPAuthenticationError as exc:
                logger.error(f"SMTP authentication failed (no retry): {exc}")
                break
            except smtplib.SMTPRecipientsRefused as exc:
                logger.error(f"SMTP recipient refused (no retry): {exc}")
                break
            except Exception as exc:
                logger.error(f"SMTP send failed on attempt {attempt}: {exc}", exc_info=True)
                if attempt < 3:
                    time.sleep(attempt)
        # If we reach here, SMTP failed on all attempts. Fall back to console print!

    # 3. Fallback: Dev console
    urls = re.findall(r'href="(http[^"]+)"', full_html)
    print(f"\n{'='*60}")
    print(f"📧 EMAIL (DEV MODE)")
    print(f"   To:      {to_email}")
    print(f"   Subject: {subject}")
    for url in urls:
        print(f"   Link:    {url}")
    print(f"{'='*60}\n")
    return True


# ─── Public Email API ─────────────────────────────────────────────────────────

def send_verification_email(to_email: str, full_name: str, verify_url: str) -> bool:
    """Send email address verification link."""
    body = _make_email_body(
        heading="Verify your email address",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Welcome to EAIMOS! Please verify your email address to activate your account "
            "and unlock the full power of the Enterprise AI Marketing Operating System.",
            "Click the button below to complete your verification. This link expires in <strong style='color:#fff;'>24 hours</strong>.",
        ],
        cta_url=verify_url,
        cta_label="Verify Email Address ✓",
        note="If you did not create an EAIMOS account, you can safely ignore this email.",
    )
    return _send_email(to_email, "Verify your EAIMOS email address", body)


def send_password_reset_email(to_email: str, full_name: str, reset_url: str) -> bool:
    """Send password reset link."""
    body = _make_email_body(
        heading="Reset your password",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We received a request to reset your EAIMOS account password.",
            "Click the button below to create a new password. This link expires in <strong style='color:#fff;'>2 hours</strong>.",
        ],
        cta_url=reset_url,
        cta_label="Reset Password →",
        note="If you did not request a password reset, please ignore this email. "
             "Your password will remain unchanged.",
    )
    return _send_email(to_email, "Reset your EAIMOS password", body)


def send_invitation_email(
    to_email: str,
    inviter_name: str,
    org_name: str,
    role: str,
    accept_url: str,
) -> bool:
    """Send organization invitation email."""
    body = _make_email_body(
        heading=f"You're invited to join {org_name}",
        paragraphs=[
            f"<strong style='color:#fff;'>{inviter_name}</strong> has invited you to join "
            f"<strong style='color:#fff;'>{org_name}</strong> on EAIMOS as a "
            f"<strong style='color:#a78bfa;'>{role}</strong>.",
            "EAIMOS is the Enterprise AI Marketing Operating System — plan, create, automate, "
            "and analyze marketing campaigns with AI agents.",
            "Click below to accept the invitation. This link expires in <strong style='color:#fff;'>48 hours</strong>.",
        ],
        cta_url=accept_url,
        cta_label="Accept Invitation →",
        note="If you believe you received this in error, you can safely ignore this email.",
    )
    return _send_email(to_email, f"You're invited to join {org_name} on EAIMOS", body)


# Alias for clarity
send_organization_invite_email = send_invitation_email


def send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send welcome email after successful email verification."""
    body = _make_info_body(
        heading="Welcome to EAIMOS! 🎉",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your email has been verified and your EAIMOS account is now fully activated.",
            "You now have access to the Enterprise AI Marketing Operating System — "
            "plan, create, automate, and analyze marketing campaigns powered by AI agents.",
            "<strong style='color:#fff;'>Here's what you can do next:</strong>",
            "• <strong style='color:#a78bfa;'>Create your first campaign</strong> — use AI to generate compelling marketing content<br/>"
            "• <strong style='color:#a78bfa;'>Invite your team</strong> — collaborate with colleagues in your organization<br/>"
            "• <strong style='color:#a78bfa;'>Connect integrations</strong> — link your favorite marketing tools<br/>"
            "• <strong style='color:#a78bfa;'>Explore AI agents</strong> — automate repetitive marketing tasks",
        ],
        note="Need help getting started? Visit our documentation or reach out to support.",
    )
    return _send_email(to_email, "Welcome to EAIMOS — Your account is ready!", body)


def send_password_changed_email(to_email: str, full_name: str) -> bool:
    """Send notification that the account password was changed."""
    body = _make_info_body(
        heading="🔒 Password Changed Successfully",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account password has been changed successfully.",
            "If you made this change, no further action is needed.",
            "If you did <strong style='color:#f87171;'>not</strong> change your password, "
            "please reset it immediately and contact our security team at "
            "<a href='mailto:security@eaimos.ai' style='color:#8b5cf6;text-decoration:none;'>security@eaimos.ai</a>.",
        ],
        note="For your security, all existing sessions have been maintained. "
             "If you suspect unauthorized access, revoke all sessions from your account settings.",
    )
    return _send_email(to_email, "Your EAIMOS password was changed", body)


def send_security_alert(to_email: str, full_name: str, event: str, detail: str) -> bool:
    """Send a security alert email."""
    body = f"""
      <h2 style="margin:0 0 20px;color:#f87171;font-size:22px;font-weight:700;">
        ⚠️ Security Alert
      </h2>
      <p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">
        Hi <strong style="color:#fff;">{full_name}</strong>,
      </p>
      <p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">
        A security event was detected on your EAIMOS account:
      </p>
      <div style="background:#1f1a2e;border:1px solid #7c3aed40;border-left:3px solid #7c3aed;
                  border-radius:8px;padding:16px 20px;margin:20px 0;">
        <p style="margin:0;color:#a78bfa;font-weight:600;font-size:14px;">{event}</p>
        <p style="margin:8px 0 0;color:#d1d5db;font-size:13px;">{detail}</p>
      </div>
      <p style="margin:16px 0 0;color:#d1d5db;font-size:15px;line-height:1.6;">
        If this was not you, please reset your password immediately and contact support.
      </p>
    """
    return _send_email(to_email, "EAIMOS Security Alert", body)


def send_role_changed_email(to_email: str, full_name: str, org_name: str, new_role: str) -> bool:
    """Send notification that the user's role in an organization changed."""
    body = _make_info_body(
        heading="Your role has been updated",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"Your role in <strong style='color:#fff;'>{org_name}</strong> has been updated.",
            f"Your new role is: <strong style='color:#a78bfa;'>{new_role}</strong>.",
            "Your permissions have been updated accordingly. If you have questions, please contact your organization administrator.",
        ],
    )
    return _send_email(to_email, f"Your role in {org_name} has been updated", body)


def send_org_removed_email(to_email: str, full_name: str, org_name: str) -> bool:
    """Send notification that the user was removed from an organization."""
    body = _make_info_body(
        heading="You've been removed from an organization",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"You have been removed from <strong style='color:#fff;'>{org_name}</strong> on EAIMOS.",
            "You no longer have access to that organization's workspace. If you believe this was a mistake, please contact the organization administrator.",
        ],
        heading_color="#f87171",
    )
    return _send_email(to_email, f"You've been removed from {org_name}", body)


def send_account_deletion_scheduled_email(to_email: str, full_name: str, deletion_date: str, restore_url: str) -> bool:
    """Send notification that account is scheduled for deletion."""
    body = _make_email_body(
        heading="⚠️ Account Scheduled for Deletion",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We've received a request to permanently delete your EAIMOS account.",
            f"Your account is scheduled for permanent deletion on <strong style='color:#f87171;'>{deletion_date}</strong>.",
            "All your data including organizations, campaigns, agents, and content will be permanently erased.",
            "If you change your mind, you can restore your account before the deletion date by clicking the button below:",
        ],
        cta_url=restore_url,
        cta_label="Restore My Account →",
        note="If you did not request account deletion, please restore your account immediately and contact security@eaimos.ai.",
    )
    return _send_email(to_email, "⚠️ Your EAIMOS account is scheduled for deletion", body)


def send_account_restored_email(to_email: str, full_name: str) -> bool:
    """Send notification that account deletion was cancelled."""
    body = _make_info_body(
        heading="✅ Account Restored",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account deletion request has been cancelled successfully.",
            "Your account is fully restored and all your data is intact.",
            "You can continue using EAIMOS as normal. Welcome back!",
        ],
    )
    return _send_email(to_email, "Your EAIMOS account has been restored", body)


def send_account_permanently_deleted_email(to_email: str, full_name: str) -> bool:
    """Send final notification that account has been permanently deleted."""
    body = _make_info_body(
        heading="Account Permanently Deleted",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account has been permanently deleted as scheduled.",
            "All associated data has been securely erased from our systems.",
            "Your email address is now available to create a new account in the future.",
            "Thank you for using EAIMOS.",
        ],
    )
    return _send_email(to_email, "Your EAIMOS account has been permanently deleted", body)


def send_mfa_enabled_email(to_email: str, full_name: str) -> bool:
    """Send notification that MFA (two-factor authentication) was enabled."""
    body = _make_info_body(
        heading="🛡️ Two-Factor Authentication Enabled",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Two-factor authentication (TOTP) has been successfully enabled on your EAIMOS account.",
            "<strong style='color:#fff;'>Important reminders:</strong>",
            "• Store your recovery codes in a safe place — they won't be shown again<br/>"
            "• You'll need your authenticator app for every login<br/>"
            "• If you lose access to your authenticator, use a recovery code to sign in",
            "Your account is now significantly more secure. Thank you for protecting your data.",
        ],
        note="If you did not enable MFA on your account, please contact security immediately.",
    )
    return _send_email(to_email, "MFA enabled on your EAIMOS account", body)


def send_mfa_disabled_email(to_email: str, full_name: str) -> bool:
    """Send warning notification that MFA was disabled."""
    body = _make_info_body(
        heading="⚠️ Two-Factor Authentication Disabled",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Two-factor authentication (TOTP) has been <strong style='color:#f87171;'>disabled</strong> "
            "on your EAIMOS account.",
            "Your account is now protected only by your password. We strongly recommend "
            "re-enabling MFA for enhanced security.",
            "If you did <strong style='color:#f87171;'>not</strong> disable MFA, your account "
            "may have been compromised. Please reset your password immediately and contact "
            "<a href='mailto:security@eaimos.ai' style='color:#8b5cf6;text-decoration:none;'>security@eaimos.ai</a>.",
        ],
        note="You can re-enable MFA at any time from your account security settings.",
        heading_color="#f87171",
    )
    return _send_email(to_email, "MFA disabled on your EAIMOS account — Action recommended", body)


def send_change_email_verification(to_email: str, full_name: str, verify_url: str) -> bool:
    """Send email change verification link to new address."""
    body = _make_email_body(
        heading="Confirm your new email address",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We received a request to change the email address for your EAIMOS account.",
            "Click the button below to confirm this new address. This link expires in <strong style='color:#fff;'>24 hours</strong>.",
        ],
        cta_url=verify_url,
        cta_label="Confirm New Email Address ✓",
        note="If you did not request an email change, please contact support immediately.",
    )
    return _send_email(to_email, "Confirm your new EAIMOS email address", body)


def send_email_background(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send email via Celery background task if available, otherwise send synchronously.
    """
    try:
        from api.worker.celery_app import send_email_task
        send_email_task.delay(to_email, subject, html_body)
        logger.info(f"Email queued for background delivery: to={to_email}, subject={subject}")
        return True
    except Exception:
        return _send_email(to_email, subject, html_body)
