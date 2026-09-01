"""
EAIMOS Email Service — Resend Integration
==========================================
Production-ready transactional email via Resend REST API.
Falls back to legacy SMTP if SMTP is configured and RESEND_API_KEY is not.
Falls back to dev-console output (and returns False) when neither is configured.

Retry: 3 attempts with exponential backoff (1s, 2s, 4s).
All functions return bool — True = delivered or queued, False = failed.
"""

import logging
import re
import smtplib
import time
import asyncio
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, List

import httpx

from api.core.config import settings
from api.models.email_log import EmailLog

logger = logging.getLogger("eaimos.email")

_RESEND_API_URL = "https://api.resend.com/emails"
_provider_logged: bool = False

# Reuse connection clients for pooling
_http_client = httpx.Client(timeout=15.0)
_async_http_client = httpx.AsyncClient(timeout=15.0)


# ─── Configuration Validation ──────────────────────────────────────────────────

def validate_email_config() -> None:
    """Validate email configurations on startup. Warns clearly if credentials are missing."""
    has_resend = bool(getattr(settings, "RESEND_API_KEY", "").strip())
    has_smtp = bool(getattr(settings, "SMTP_HOST", "").strip())

    if not has_resend:
        if has_smtp:
            logger.warning(
                "[CONFIG] RESEND_API_KEY is missing. Transactional emails will fall back to legacy SMTP server."
            )
        else:
            logger.warning(
                "[CONFIG] Neither RESEND_API_KEY nor SMTP_HOST is configured. "
                "The email service will run in development mode (printed to terminal) and will NOT report success."
            )
    else:
        # Check sender attributes
        from_email = getattr(settings, "EMAIL_FROM", "")
        if not from_email:
            logger.warning("[CONFIG] EMAIL_FROM address is not configured. Defaulting to noreply@eaimos.ai.")


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


# ─── Provider Checking & Config ──────────────────────────────────────────────

def _is_resend_configured() -> bool:
    return bool(getattr(settings, "RESEND_API_KEY", "").strip())


def _is_smtp_configured() -> bool:
    return bool(getattr(settings, "SMTP_HOST", "").strip())


def _get_from_address() -> str:
    name = getattr(settings, "EMAIL_FROM_NAME", "EAIMOS Platform")
    addr = getattr(settings, "EMAIL_FROM", "noreply@eaimos.ai")
    if name:
        return f"{name} <{addr}>"
    return addr


def _host_matches_domain(host: str, domain: str) -> bool:
    """Return True when host is exactly domain or a subdomain of domain."""
    return host == domain or host.endswith(f".{domain}")


def _detect_smtp_provider(host: Optional[str]) -> str:
    """Detect SMTP provider from hostname for logging purposes."""
    if not host:
        return "none"
    host_lower = host.lower()
    if host_lower in ("localhost", "127.0.0.1", "mailpit", "0.0.0.0"):
        return "mailpit"
    if _host_matches_domain(host_lower, "sendgrid.net"):
        return "sendgrid"
    if _host_matches_domain(host_lower, "gmail.com") or _host_matches_domain(host_lower, "google.com"):
        return "gmail"
    if _host_matches_domain(host_lower, "amazonaws.com") or _host_matches_domain(host_lower, "amazonses.com"):
        return "amazon-ses"
    if _host_matches_domain(host_lower, "mailgun.org") or _host_matches_domain(host_lower, "mailgun.net"):
        return "mailgun"
    if _host_matches_domain(host_lower, "outlook.com") or _host_matches_domain(host_lower, "office365.com"):
        return "microsoft"
    return "custom-smtp"


# ─── Database Logging Helpers ─────────────────────────────────────────────────

def _write_email_log(
    recipient: str,
    subject: str,
    template: str,
    status: str,
    provider: str,
    retries: int,
    latency: Optional[float] = None,
    correlation_id: Optional[str] = None,
    error_message: Optional[str] = None,
    log_id: Optional[str] = None,
) -> None:
    try:
        from api.database.session import SessionLocal
        with SessionLocal() as db:
            if log_id:
                log_record = db.query(EmailLog).filter(EmailLog.id == uuid.UUID(log_id)).first()
                if log_record:
                    log_record.status = status
                    log_record.retries = retries
                    log_record.latency = latency
                    log_record.error_message = error_message
                    db.commit()
                    return
            log_record = EmailLog(
                recipient=recipient,
                subject=subject,
                template=template,
                status=status,
                provider=provider,
                retries=retries,
                latency=latency,
                correlation_id=correlation_id,
                error_message=error_message,
            )
            db.add(log_record)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to write/update EmailLog: {e}")


# ─── Sync Delivery ────────────────────────────────────────────────────────────

def _send_via_resend(to_email: str, subject: str, html: str) -> None:
    """Send via Resend REST API synchronously. Raises on failure."""
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
    resp = _http_client.post(_RESEND_API_URL, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend API error {resp.status_code}: {resp.text}")


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


def _send_email(
    to_email: str,
    subject: str,
    html_body: str,
    template_name: str = "custom",
    correlation_id: Optional[str] = None,
    log_id: Optional[str] = None,
) -> bool:
    """
    Send transactional email synchronously.
    - If RESEND_API_KEY is set: sends via Resend with 3-attempt retry.
    - Else if SMTP is configured: sends via SMTP with 3-attempt retry.
    - Otherwise: prints to console (dev mode) and returns False.
    """
    full_html = _BASE_TEMPLATE.format(subject=subject, body=html_body)
    start_time = time.perf_counter()
    retries = 0

    # 1. Primary: Resend API
    if _is_resend_configured():
        backoff = 1
        last_exc = None
        for attempt in range(1, 4):
            try:
                _send_via_resend(to_email, subject, full_html)
                latency = time.perf_counter() - start_time
                _write_email_log(
                    to_email, subject, template_name, "SENT", "resend", retries,
                    latency, correlation_id, None, log_id
                )
                logger.info(
                    f"[Resend] Email sent: to={to_email}, subject={subject!r}, latency={latency:.3f}s, retries={retries}"
                )
                return True
            except Exception as exc:
                retries = attempt
                last_exc = exc
                logger.warning(f"[Resend] Attempt {attempt} failed for {to_email}: {exc}")
                if attempt < 3:
                    time.sleep(backoff)
                    backoff *= 2
        latency = time.perf_counter() - start_time
        _write_email_log(
            to_email, subject, template_name, "FAILED", "resend", retries,
            latency, correlation_id, f"All attempts failed. Last exception: {last_exc}", log_id
        )
        logger.error(f"[Resend] All retry attempts exhausted for {to_email}")
        return False

    # 2. Secondary: SMTP
    if _is_smtp_configured():
        smtp_success = False
        smtp_provider = _detect_smtp_provider(getattr(settings, "SMTP_HOST", ""))
        last_exc = None
        for attempt in range(1, 4):
            try:
                _send_smtp(to_email, subject, full_html)
                latency = time.perf_counter() - start_time
                _write_email_log(
                    to_email, subject, template_name, "SENT", smtp_provider, retries,
                    latency, correlation_id, None, log_id
                )
                logger.info(f"Email sent via SMTP: to={to_email}, subject={subject}, latency={latency:.3f}s")
                return True
            except smtplib.SMTPAuthenticationError as exc:
                last_exc = exc
                logger.error(f"SMTP authentication failed (no retry): {exc}")
                break
            except smtplib.SMTPRecipientsRefused as exc:
                last_exc = exc
                logger.error(f"SMTP recipient refused (no retry): {exc}")
                break
            except Exception as exc:
                retries = attempt
                last_exc = exc
                logger.error(f"SMTP send failed on attempt {attempt}: {exc}")
                if attempt < 3:
                    time.sleep(attempt)
        latency = time.perf_counter() - start_time
        _write_email_log(
            to_email, subject, template_name, "FAILED", smtp_provider, retries,
            latency, correlation_id, str(last_exc), log_id
        )
        return False

    # 3. Fallback: Dev console (never fake success, return False)
    urls = re.findall(r'href="(http[^"]+)"', full_html)
    print(f"\n{'='*60}")
    print(f"📧 EMAIL (DEV MODE - PROVIDER UNAVAILABLE)")
    print(f"   To:      {to_email}")
    print(f"   Subject: {subject}")
    if urls:
        print(f"   Links:   {len(urls)} link(s) redacted")
    print(f"{'='*60}\n")

    _write_email_log(
        to_email, subject, template_name, "FAILED", "dev-console", 0,
        None, correlation_id, "Resend key or SMTP server missing. Provider unavailable.", log_id
    )
    return False


# ─── Async Delivery ───────────────────────────────────────────────────────────

async def _send_via_resend_async(to_email: str, subject: str, html: str) -> None:
    """Send via Resend REST API asynchronously."""
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
    resp = await _async_http_client.post(_RESEND_API_URL, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend API error {resp.status_code}: {resp.text}")


async def _send_email_async(
    to_email: str,
    subject: str,
    html_body: str,
    template_name: str = "custom",
    correlation_id: Optional[str] = None,
    log_id: Optional[str] = None,
) -> bool:
    """
    Send transactional email asynchronously.
    Supports timeout and exponential retry.
    """
    full_html = _BASE_TEMPLATE.format(subject=subject, body=html_body)
    start_time = time.perf_counter()
    retries = 0

    if _is_resend_configured():
        backoff = 1
        last_exc = None
        for attempt in range(1, 4):
            try:
                await _send_via_resend_async(to_email, subject, full_html)
                latency = time.perf_counter() - start_time
                _write_email_log(
                    to_email, subject, template_name, "SENT", "resend", retries,
                    latency, correlation_id, None, log_id
                )
                return True
            except Exception as exc:
                retries = attempt
                last_exc = exc
                logger.warning(f"[Resend Async] Attempt {attempt} failed: {exc}")
                if attempt < 3:
                    await asyncio.sleep(backoff)
                    backoff *= 2
        latency = time.perf_counter() - start_time
        _write_email_log(
            to_email, subject, template_name, "FAILED", "resend", retries,
            latency, correlation_id, str(last_exc), log_id
        )
        return False

    if _is_smtp_configured():
        # SMTP library in python is inherently synchronous; wrap in executor
        loop = asyncio.get_running_loop()
        try:
            success = await loop.run_in_executor(
                None, _send_email, to_email, subject, html_body, template_name, correlation_id, log_id
            )
            return success
        except Exception as e:
            logger.error(f"[SMTP Async] Failed: {e}")
            return False

    # Dev Console Fallback
    urls = re.findall(r'href="(http[^"]+)"', full_html)
    print(f"\n{'='*60}")
    print(f"📧 EMAIL (DEV MODE - PROVIDER UNAVAILABLE - ASYNC)")
    print(f"   To:      {to_email}")
    print(f"   Subject: {subject}")
    for url in urls:
        print(f"   Link:    {url}")
    print(f"{'='*60}\n")

    _write_email_log(
        to_email, subject, template_name, "FAILED", "dev-console", 0,
        None, correlation_id, "Resend key or SMTP server missing.", log_id
    )
    return False


# ─── Public Email APIs (Template Renderers & Async Dispatch) ──────────────────

def send_email_background(
    to_email: str,
    subject: str,
    html_body: str,
    template_name: str = "custom",
    correlation_id: Optional[str] = None,
) -> bool:
    """
    Queue email delivery to the background queue (Celery task).
    Pre-creates an EmailLog in QUEUED state.
    """
    provider = "resend" if _is_resend_configured() else ("smtp" if _is_smtp_configured() else "dev-console")

    # Generate log record in DB
    try:
        from api.database.session import SessionLocal
        with SessionLocal() as db:
            log_record = EmailLog(
                recipient=to_email,
                subject=subject,
                template=template_name,
                status="QUEUED",
                provider=provider,
                correlation_id=correlation_id,
            )
            db.add(log_record)
            db.commit()
            log_id = str(log_record.id)
    except Exception as e:
        logger.error(f"Failed to create initial EmailLog: {e}")
        log_id = None

    try:
        from api.worker.celery_app import send_email_task
        send_email_task.delay(to_email, subject, html_body, template_name, log_id, correlation_id)
        logger.info(f"Email queued via Celery: to={to_email}, subject={subject!r}, log_id={log_id}")
        return True
    except Exception as exc:
        logger.warning(f"Celery queueing failed: {exc}. Processing synchronously.")
        success = _send_email(to_email, subject, html_body, template_name, correlation_id, log_id)
        return success


# ─── Auth Templates ───────────────────────────────────────────────────────────

def send_verification_email(to_email: str, full_name: str, verify_url: str) -> bool:
    """Send email address verification link."""
    body = _make_email_body(
        heading="Verify your email address",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Welcome to EAIMOS! Please verify your email address to activate your account.",
            "Click the button below to complete your verification. This link expires in <strong style='color:#fff;'>24 hours</strong>.",
        ],
        cta_url=verify_url,
        cta_label="Verify Email Address ✓",
        note="If you did not create an EAIMOS account, you can safely ignore this email.",
    )
    return send_email_background(to_email, "Verify your EAIMOS email address", body, "verify-email")


def send_resend_verification_email(to_email: str, full_name: str, verify_url: str) -> bool:
    """Send a fresh email verification link."""
    body = _make_email_body(
        heading="Verify your email address",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "You requested a new verification link for your EAIMOS account.",
            "Click the button below to verify your email. This link expires in <strong style='color:#fff;'>24 hours</strong>.",
        ],
        cta_url=verify_url,
        cta_label="Verify Email Address ✓",
        note="If you did not make this request, you can ignore this email.",
    )
    return send_email_background(to_email, "New verification link for your EAIMOS account", body, "resend-verification")


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
        note="If you did not request a password reset, please ignore this email. Your password will remain unchanged.",
    )
    return send_email_background(to_email, "Reset your EAIMOS password", body, "forgot-password")


def send_password_reset_success_email(to_email: str, full_name: str) -> bool:
    """Send alert that password was successfully reset."""
    body = _make_info_body(
        heading="✅ Password Reset Successful",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your password has been successfully reset.",
            "You can now sign in to your EAIMOS account with your new password.",
            "All active sessions have been revoked for your security.",
        ],
        note="If you did not make this change, please contact security@eaimos.ai immediately.",
    )
    return send_email_background(to_email, "Your EAIMOS password has been reset", body, "password-reset-success")


def send_welcome_email(to_email: str, full_name: str) -> bool:
    """Welcome email sent on successful email verification."""
    body = _make_info_body(
        heading="Welcome to EAIMOS! 🎉",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your email has been verified and your account is now active.",
            "You now have access to the Enterprise AI Marketing Operating System.",
            "<strong style='color:#fff;'>Next Steps:</strong>",
            "• Create your first campaign using AI agent models.<br/>"
            "• Invite your team to collaborate in your organization workspace.<br/>"
            "• Explore our custom AI capabilities.",
        ],
        note="Need help getting started? Visit our documentation or contact support.",
    )
    return send_email_background(to_email, "Welcome to EAIMOS — Your account is ready!", body, "welcome")


# ─── Security Templates ───────────────────────────────────────────────────────

def send_password_changed_email(to_email: str, full_name: str) -> bool:
    """Notify user of password change."""
    body = _make_info_body(
        heading="🔒 Password Changed Successfully",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account password was recently changed.",
            "If you made this change, no action is needed.",
        ],
        note="If you did not make this change, please reset your password immediately.",
    )
    return send_email_background(to_email, "Your EAIMOS password was changed", body, "password-changed")


def send_new_login_email(to_email: str, full_name: str, ip_address: str, browser: str, time_str: str) -> bool:
    """Notify user of a new login."""
    body = _make_info_body(
        heading="⚠️ New Login Detected",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We detected a new login to your EAIMOS account:",
            f"• <strong>Time:</strong> {time_str}<br/>"
            f"• <strong>IP Address:</strong> {ip_address}<br/>"
            f"• <strong>Device/Browser:</strong> {browser}",
        ],
        note="If this was not you, please change your password immediately to protect your account.",
        heading_color="#f87171"
    )
    return send_email_background(to_email, "EAIMOS Security Alert: New Login", body, "new-login")


def send_new_device_email(to_email: str, full_name: str, device_name: str, ip_address: str, time_str: str) -> bool:
    """Notify user of a login from a new device."""
    body = _make_info_body(
        heading="⚠️ New Device Detected",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"Your EAIMOS account was logged into from a new device: <strong>{device_name}</strong>.",
            f"• <strong>Time:</strong> {time_str}<br/>"
            f"• <strong>IP Address:</strong> {ip_address}",
        ],
        note="If this was not you, revoke this session from your settings page and change your password.",
        heading_color="#f87171"
    )
    return send_email_background(to_email, "EAIMOS Security Alert: New Device", body, "new-device")


def send_mfa_enabled_email(to_email: str, full_name: str) -> bool:
    """Notify user that MFA was enabled."""
    body = _make_info_body(
        heading="🛡️ Two-Factor Authentication Enabled",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Two-factor authentication (MFA) has been enabled on your account.",
            "You will need to provide an authenticator app code for future sign-ins.",
        ],
        note="Store your recovery codes in a safe place.",
    )
    return send_email_background(to_email, "MFA enabled on your EAIMOS account", body, "mfa-enabled")


def send_mfa_disabled_email(to_email: str, full_name: str) -> bool:
    """Warning notify user that MFA was disabled."""
    body = _make_info_body(
        heading="⚠️ Two-Factor Authentication Disabled",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Two-factor authentication (MFA) has been <strong style='color:#f87171;'>disabled</strong>.",
            "Your account is now protected only by your password. We recommend re-enabling MFA.",
        ],
        note="If you did not request this, contact security@eaimos.ai immediately.",
        heading_color="#f87171"
    )
    return send_email_background(to_email, "MFA disabled on your EAIMOS account", body, "mfa-disabled")


def send_security_alert(to_email: str, full_name: str, event: str, detail: str) -> bool:
    """General security event warning."""
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
        If this was not you, reset your password and contact support.
      </p>
    """
    return send_email_background(to_email, "EAIMOS Security Alert", body, "security-alert")


# ─── Organizations Templates ──────────────────────────────────────────────────

def send_invitation_email(
    to_email: str,
    inviter_name: str,
    org_name: str,
    role: str,
    accept_url: str,
    temp_password: Optional[str] = None,
) -> bool:
    """Send organization invite."""
    reject_url = f"{accept_url}&action=reject"
    
    temp_pw_section = ""
    if temp_password:
        temp_pw_section = f"""
        <div style="background:#1f1a2e;border:1px solid #7c3aed40;border-left:3px solid #e11d48;
                    border-radius:8px;padding:16px 20px;margin:20px 0;text-align:left;">
          <p style="margin:0;color:#f43f5e;font-weight:600;font-size:14px;">⚠️ Temporary Account Credentials</p>
          <p style="margin:8px 0 0;color:#d1d5db;font-size:13px;line-height:1.5;">
            An account has been pre-created for you. Use these credentials to sign in:<br/>
            <strong>Email:</strong> {to_email}<br/>
            <strong>Temporary Password:</strong> <code style="background:#0f0b1a;padding:2px 6px;border-radius:4px;color:#fff;">{temp_password}</code>
          </p>
          <p style="margin:8px 0 0;color:#9ca3af;font-size:11px;">You will be prompted to change this password upon email verification.</p>
        </div>
        """

    body = f"""
      <h2 style="margin:0 0 20px;color:#fff;font-size:22px;font-weight:700;">You're invited to join {org_name}</h2>
      <p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">
        Hi,
      </p>
      <p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">
        <strong style='color:#fff;'>{inviter_name}</strong> has invited you to join the team workspace for 
        <strong style='color:#fff;'>{org_name}</strong> as a 
        <strong style='color:#a78bfa;'>{role}</strong>.
      </p>
      
      {temp_pw_section}
      
      <p style="margin:0 0 16px;color:#d1d5db;font-size:15px;line-height:1.6;">
        This invitation will automatically expire in <strong style='color:#fff;'>48 hours</strong>.
      </p>

      <div style="margin:28px 0;">
        <a href="{accept_url}" style="{_BUTTON_STYLE}margin-right:12px;">Accept Invitation</a>
        <a href="{reject_url}" style="display:inline-block;background:#262626;color:#e5e5e5;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:600;font-size:15px;border:1px solid #404040;">Decline</a>
      </div>

      <p style="margin:20px 0 0;color:#6b7280;font-size:12px;word-break:break-all;">
        Or copy this accept link: <span style="color:#8b5cf6;">{accept_url}</span>
      </p>
      
      <p style="margin:24px 0 0;color:#9ca3af;font-size:13px;line-height:1.6;">
        If you have any questions, please contact our support team at <a href="mailto:support@eaimos.ai" style="color:#8b5cf6;text-decoration:none;">support@eaimos.ai</a>.
      </p>
    """
    return send_email_background(to_email, f"You're invited to join {org_name} on EAIMOS", body, "org-invite")


send_organization_invite_email = send_invitation_email


def send_invitation_accepted_email(to_email: str, invitee_name: str, invitee_email: str, org_name: str) -> bool:
    """Notify the inviter that an invitation was accepted."""
    body = _make_info_body(
        heading="🎉 Team Invitation Accepted",
        paragraphs=[
            f"Hi,",
            f"<strong style='color:#fff;'>{invitee_name}</strong> ({invitee_email}) has accepted the invitation "
            f"to join <strong style='color:#fff;'>{org_name}</strong>.",
            "They now have access to your organization's workspace.",
        ],
    )
    return send_email_background(to_email, f"{invitee_name} accepted the invite to {org_name}", body, "org-invite-accepted")


def send_invitation_rejected_email(to_email: str, invitee_email: str, org_name: str) -> bool:
    """Notify the inviter that an invitation was rejected."""
    body = _make_info_body(
        heading="Team Invitation Declined",
        paragraphs=[
            f"Hi,",
            f"The invitation sent to <strong style='color:#fff;'>{invitee_email}</strong> to join "
            f"<strong style='color:#fff;'>{org_name}</strong> was declined.",
        ],
        heading_color="#f87171"
    )
    return send_email_background(to_email, f"Invitation to {org_name} was declined", body, "org-invite-rejected")


def send_invitation_revoked_email(to_email: str, invitee_email: str, org_name: str) -> bool:
    """Notify the invitee that their invitation was revoked."""
    body = _make_info_body(
        heading="Invitation Revoked",
        paragraphs=[
            f"Hi,",
            f"The invitation for <strong style='color:#fff;'>{invitee_email}</strong> to join "
            f"<strong style='color:#fff;'>{org_name}</strong> has been cancelled.",
        ],
        heading_color="#f87171"
    )
    return send_email_background(to_email, f"Invitation to {org_name} revoked", body, "org-invite-revoked")


def send_role_changed_email(to_email: str, full_name: str, org_name: str, new_role: str) -> bool:
    """Notify user of role change."""
    body = _make_info_body(
        heading="Your role has been updated",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"Your role in <strong style='color:#fff;'>{org_name}</strong> has been changed to "
            f"<strong style='color:#a78bfa;'>{new_role}</strong>.",
        ],
    )
    return send_email_background(to_email, f"Your role in {org_name} has been updated", body, "role-changed")


def send_org_removed_email(to_email: str, full_name: str, org_name: str) -> bool:
    """Notify user of removal from organization."""
    body = _make_info_body(
        heading="You've been removed from an organization",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"You have been removed from <strong style='color:#fff;'>{org_name}</strong>.",
        ],
        heading_color="#f87171",
    )
    return send_email_background(to_email, f"You've been removed from {org_name}", body, "removed-from-org")


def send_org_restored_email(to_email: str, full_name: str, org_name: str) -> bool:
    """Notify user of organization restoration."""
    body = _make_info_body(
        heading="✅ Organization Restored",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"The organization <strong style='color:#fff;'>{org_name}</strong> has been restored successfully.",
            "You can now access your organization workspace and resources again.",
        ],
    )
    return send_email_background(to_email, f"Organization {org_name} has been restored", body, "org-restored")


def send_ownership_transfer_email(to_email: str, full_name: str, org_name: str, previous_owner_name: str) -> bool:
    """Notify user of organization ownership transfer."""
    body = _make_info_body(
        heading="👑 Organization Ownership Transferred",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            f"<strong style='color:#fff;'>{previous_owner_name}</strong> has transferred "
            f"ownership of <strong style='color:#fff;'>{org_name}</strong> to you.",
            "You are now the Owner of this organization workspace and have full control.",
        ],
    )
    return send_email_background(to_email, f"Ownership of {org_name} transferred to you", body, "ownership-transfer")


# ─── Account Lifecycle Templates ──────────────────────────────────────────────

def send_account_deletion_scheduled_email(to_email: str, full_name: str, deletion_date: str, restore_url: str) -> bool:
    """Notify user that account deletion is scheduled."""
    body = _make_email_body(
        heading="⚠️ Account Scheduled for Deletion",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We've received a request to delete your EAIMOS account.",
            f"Permanent deletion is scheduled for <strong style='color:#f87171;'>{deletion_date}</strong>.",
            "If you change your mind, restore your account before the deletion date:",
        ],
        cta_url=restore_url,
        cta_label="Restore My Account →",
        note="If you did not request this, please restore your account immediately.",
    )
    return send_email_background(to_email, "⚠️ Your EAIMOS account is scheduled for deletion", body, "account-deletion-scheduled")


def send_account_restored_email(to_email: str, full_name: str) -> bool:
    """Notify user that account was restored."""
    body = _make_info_body(
        heading="✅ Account Restored",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account deletion request was cancelled successfully.",
            "Your account is fully restored and active. Welcome back!",
        ],
    )
    return send_email_background(to_email, "Your EAIMOS account has been restored", body, "account-restored")


def send_account_permanently_deleted_email(to_email: str, full_name: str) -> bool:
    """Final notify user that account was permanently deleted."""
    body = _make_info_body(
        heading="Account Permanently Deleted",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "Your EAIMOS account has been permanently deleted.",
            "All associated data has been erased.",
        ],
    )
    return send_email_background(to_email, "Your EAIMOS account has been permanently deleted", body, "account-permanent-deletion")


def send_change_email_verification(to_email: str, full_name: str, verify_url: str) -> bool:
    """Send link to verify new email address."""
    body = _make_email_body(
        heading="Confirm your new email address",
        paragraphs=[
            f"Hi <strong style='color:#fff;'>{full_name}</strong>,",
            "We received a request to change the email address for your account.",
            "Click below to confirm this address. This link expires in <strong style='color:#fff;'>24 hours</strong>.",
        ],
        cta_url=verify_url,
        cta_label="Confirm New Email Address ✓",
    )
    return send_email_background(to_email, "Confirm your new EAIMOS email address", body, "email-change-verification")
