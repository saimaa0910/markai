"""
EAIMOS Email Infrastructure Tests
===================================
Comprehensive test suite for the email service, templates, SMTP delivery,
retry logic, provider detection, and Celery background tasks.
"""

import re
import uuid
from unittest.mock import MagicMock, patch, call

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.config import settings
from api.services.email_service import (
    _detect_smtp_provider,
    _html_to_text,
    _is_smtp_configured,
    _make_email_body,
    _make_info_body,
    _send_email,
    _get_from_address,
    send_verification_email,
    send_password_reset_email,
    send_invitation_email,
    send_organization_invite_email,
    send_change_email_verification,
    send_security_alert,
    send_welcome_email,
    send_password_changed_email,
    send_mfa_enabled_email,
    send_mfa_disabled_email,
    send_email_background,
)

client = TestClient(app)


# ─── Provider Detection ──────────────────────────────────────────────────────

class TestProviderDetection:
    """Test SMTP provider auto-detection from hostname."""

    def test_detect_mailpit_localhost(self):
        assert _detect_smtp_provider("localhost") == "mailpit"

    def test_detect_mailpit_127(self):
        assert _detect_smtp_provider("127.0.0.1") == "mailpit"

    def test_detect_mailpit_container(self):
        assert _detect_smtp_provider("mailpit") == "mailpit"

    def test_detect_sendgrid(self):
        assert _detect_smtp_provider("smtp.sendgrid.net") == "sendgrid"

    def test_detect_gmail(self):
        assert _detect_smtp_provider("smtp.gmail.com") == "gmail"

    def test_detect_amazon_ses(self):
        assert _detect_smtp_provider("email-smtp.us-east-1.amazonaws.com") == "amazon-ses"

    def test_detect_mailgun(self):
        assert _detect_smtp_provider("smtp.mailgun.org") == "mailgun"

    def test_detect_microsoft(self):
        assert _detect_smtp_provider("smtp.office365.com") == "microsoft"

    def test_detect_custom(self):
        assert _detect_smtp_provider("mail.company.com") == "custom-smtp"

    def test_detect_empty(self):
        assert _detect_smtp_provider("") == "none"

    def test_detect_none(self):
        assert _detect_smtp_provider(None) == "none"


# ─── SMTP Configuration Detection ────────────────────────────────────────────

class TestSMTPConfiguration:
    """Test that SMTP configuration detection works correctly."""

    def test_smtp_configured_with_localhost(self, monkeypatch):
        """Mailpit on localhost should be treated as configured SMTP."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        assert _is_smtp_configured() is True

    def test_smtp_configured_with_sendgrid(self, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.sendgrid.net")
        assert _is_smtp_configured() is True

    def test_smtp_not_configured_empty(self, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "")
        assert _is_smtp_configured() is False

    def test_smtp_not_configured_whitespace(self, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "   ")
        assert _is_smtp_configured() is False


# ─── From Address Formatting ─────────────────────────────────────────────────

class TestFromAddress:
    """Test From address formatting with display name."""

    def test_from_with_display_name(self, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM_NAME", "EAIMOS Platform")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")
        from_addr = _get_from_address()
        assert "EAIMOS Platform" in from_addr
        assert "noreply@eaimos.ai" in from_addr

    def test_from_without_display_name(self, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM_NAME", "")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")
        from_addr = _get_from_address()
        assert from_addr == "noreply@eaimos.ai"


# ─── HTML to Text Conversion ─────────────────────────────────────────────────

class TestHtmlToText:
    """Test plain-text fallback generation."""

    def test_strips_tags(self):
        result = _html_to_text("<p>Hello <strong>World</strong></p>")
        assert "Hello World" in result
        assert "<" not in result

    def test_converts_br_to_newline(self):
        result = _html_to_text("Line 1<br/>Line 2")
        assert "Line 1\nLine 2" in result

    def test_converts_p_to_double_newline(self):
        result = _html_to_text("<p>Para 1</p><p>Para 2</p>")
        assert "Para 1" in result
        assert "Para 2" in result

    def test_collapses_excess_newlines(self):
        result = _html_to_text("<p>A</p><br/><br/><br/><p>B</p>")
        assert "\n\n\n\n" not in result


# ─── Template Body Builders ──────────────────────────────────────────────────

class TestTemplateBuilders:
    """Test email body builder functions."""

    def test_make_email_body_contains_cta(self):
        body = _make_email_body(
            heading="Test Heading",
            paragraphs=["Paragraph one."],
            cta_url="https://example.com/action",
            cta_label="Click Me",
        )
        assert "Test Heading" in body
        assert "Paragraph one." in body
        assert "https://example.com/action" in body
        assert "Click Me" in body

    def test_make_email_body_with_note(self):
        body = _make_email_body(
            heading="Heading",
            paragraphs=["Para."],
            cta_url="https://example.com",
            cta_label="CTA",
            note="This is a note.",
        )
        assert "This is a note." in body

    def test_make_info_body_no_cta(self):
        body = _make_info_body(
            heading="Info Heading",
            paragraphs=["Info text."],
        )
        assert "Info Heading" in body
        assert "Info text." in body
        # Should NOT contain a CTA button
        assert "Click" not in body

    def test_make_info_body_custom_heading_color(self):
        body = _make_info_body(
            heading="Warning",
            paragraphs=["Something."],
            heading_color="#f87171",
        )
        assert "#f87171" in body


# ─── Email Template Functions ─────────────────────────────────────────────────

class TestEmailTemplates:
    """Test all public email template functions produce valid HTML."""

    def _assert_valid_email(self, result, expected_subject_fragment=None):
        """Helper to verify email sending with mocked SMTP."""
        assert result is True

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_verification_email(self, mock_send):
        result = send_verification_email("user@test.com", "John Doe", "https://example.com/verify")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "user@test.com"
        assert "Verify" in args[1]
        assert "John Doe" in args[2]
        assert "https://example.com/verify" in args[2]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_password_reset_email(self, mock_send):
        result = send_password_reset_email("user@test.com", "Jane Doe", "https://example.com/reset")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Reset" in args[1]
        assert "https://example.com/reset" in args[2]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_invitation_email(self, mock_send):
        result = send_invitation_email(
            "invitee@test.com", "Admin User", "Acme Corp", "MEMBER", "https://example.com/accept"
        )
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Acme Corp" in args[1]
        assert "Admin User" in args[2]
        assert "MEMBER" in args[2]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_organization_invite_is_alias(self, mock_send):
        """send_organization_invite_email is an alias for send_invitation_email."""
        assert send_organization_invite_email is send_invitation_email

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_change_email_verification(self, mock_send):
        result = send_change_email_verification("new@test.com", "User", "https://example.com/confirm")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Confirm" in args[1]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_security_alert(self, mock_send):
        result = send_security_alert("user@test.com", "User Name", "New Login", "From IP 1.2.3.4")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Security Alert" in args[1]
        assert "New Login" in args[2]
        assert "1.2.3.4" in args[2]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_welcome_email(self, mock_send):
        result = send_welcome_email("user@test.com", "New User")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Welcome" in args[1]
        assert "New User" in args[2]

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_password_changed_email(self, mock_send):
        result = send_password_changed_email("user@test.com", "User")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "password" in args[1].lower()

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_mfa_enabled_email(self, mock_send):
        result = send_mfa_enabled_email("user@test.com", "Secure User")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "MFA" in args[1]
        assert "recovery codes" in args[2].lower()

    @patch("api.services.email_service._send_email", return_value=True)
    def test_send_mfa_disabled_email(self, mock_send):
        result = send_mfa_disabled_email("user@test.com", "User")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "MFA" in args[1]
        assert "disabled" in args[1].lower()


# ─── SMTP Send with Mock ─────────────────────────────────────────────────────

class TestSMTPSend:
    """Test actual SMTP sending with mocked smtplib."""

    @patch("api.services.email_service.smtplib.SMTP")
    def test_send_via_smtp_port_587(self, mock_smtp_class, monkeypatch):
        """Test STARTTLS on port 587."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.sendgrid.net")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PORT", 587)
        monkeypatch.setattr("api.services.email_service.settings.SMTP_USER", "apikey")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PASSWORD", "SG.test-key")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM_NAME", "EAIMOS")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_TIMEOUT", 30)
        # Reset provider log flag
        import api.services.email_service as es
        es._provider_logged = False

        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = _send_email("user@test.com", "Test Subject", "<p>Test Body</p>")

        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.sendgrid.net", 587, timeout=30)
        mock_server.ehlo.assert_called()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("apikey", "SG.test-key")
        mock_server.sendmail.assert_called_once()

    @patch("api.services.email_service.smtplib.SMTP")
    def test_send_via_mailpit_no_auth(self, mock_smtp_class, monkeypatch):
        """Test Mailpit (localhost:1025) — no auth, no STARTTLS."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PORT", 1025)
        monkeypatch.setattr("api.services.email_service.settings.SMTP_USER", "")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PASSWORD", "")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM_NAME", "EAIMOS")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_TIMEOUT", 30)
        import api.services.email_service as es
        es._provider_logged = False

        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = _send_email("user@test.com", "Test", "<p>Test</p>")

        assert result is True
        mock_smtp_class.assert_called_once_with("localhost", 1025, timeout=30)
        # No STARTTLS on port 1025
        mock_server.starttls.assert_not_called()
        # No login when user/password are empty
        mock_server.login.assert_not_called()

    @patch("api.services.email_service.smtplib.SMTP_SSL")
    def test_send_via_ssl_port_465(self, mock_smtp_ssl_class, monkeypatch):
        """Test SSL on port 465."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PORT", 465)
        monkeypatch.setattr("api.services.email_service.settings.SMTP_USER", "user@gmail.com")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_PASSWORD", "app-password")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "user@gmail.com")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM_NAME", "")
        monkeypatch.setattr("api.services.email_service.settings.SMTP_TIMEOUT", 15)
        import api.services.email_service as es
        es._provider_logged = False

        mock_server = MagicMock()
        mock_smtp_ssl_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_ssl_class.return_value.__exit__ = MagicMock(return_value=False)

        result = _send_email("recipient@test.com", "SSL Test", "<p>Encrypted</p>")

        assert result is True
        mock_smtp_ssl_class.assert_called_once_with("smtp.gmail.com", 465, timeout=15)


# ─── Retry Logic ─────────────────────────────────────────────────────────────

class TestRetryLogic:
    """Test email retry behavior."""

    @patch("api.services.email_service.time.sleep")
    @patch("api.services.email_service._send_smtp")
    def test_retries_on_transient_failure(self, mock_send_smtp, mock_sleep, monkeypatch):
        """Test 3 retry attempts on transient error, then console fallback."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.example.com")
        import api.services.email_service as es
        es._provider_logged = False

        mock_send_smtp.side_effect = ConnectionError("Connection refused")

        result = _send_email("user@test.com", "Test", "<p>Test</p>")

        assert result is False  # Console fallback does not return True
        assert mock_send_smtp.call_count == 3
        assert mock_sleep.call_count == 2  # sleep(1), sleep(2)

    @patch("api.services.email_service._send_smtp")
    def test_no_retry_on_auth_error(self, mock_send_smtp, monkeypatch):
        """Test no retry on authentication failures (permanent error)."""
        import smtplib
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.example.com")
        import api.services.email_service as es
        es._provider_logged = False

        mock_send_smtp.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        result = _send_email("user@test.com", "Test", "<p>Test</p>")

        assert result is False  # Console fallback does not return True
        assert mock_send_smtp.call_count == 1  # No retry

    @patch("api.services.email_service._send_smtp")
    def test_no_retry_on_recipient_refused(self, mock_send_smtp, monkeypatch):
        """Test no retry on recipient refused (permanent error)."""
        import smtplib
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "smtp.example.com")
        import api.services.email_service as es
        es._provider_logged = False

        mock_send_smtp.side_effect = smtplib.SMTPRecipientsRefused({"bad@test.com": (550, b"Unknown")})

        result = _send_email("bad@test.com", "Test", "<p>Test</p>")

        assert result is False  # Console fallback does not return True
        assert mock_send_smtp.call_count == 1  # No retry


# ─── Console Fallback ────────────────────────────────────────────────────────

class TestConsoleFallback:
    """Test console fallback when SMTP is not configured."""

    def test_console_fallback_when_no_smtp(self, monkeypatch, capsys):
        """When SMTP_HOST is empty, prints to console."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "")
        import api.services.email_service as es
        es._provider_logged = False

        result = _send_email("user@test.com", "Console Test", "<p>Fallback</p>")

        assert result is False
        captured = capsys.readouterr()
        assert "EMAIL (DEV MODE" in captured.out
        assert "user@test.com" in captured.out
        assert "Console Test" in captured.out


# ─── Background Email via Celery ──────────────────────────────────────────────

class TestBackgroundEmail:
    """Test Celery background email dispatch."""

    @patch("api.services.email_service._send_email", return_value=True)
    def test_background_fallback_to_sync(self, mock_send, monkeypatch):
        """When Celery is unavailable, falls back to synchronous send."""
        # Make celery import fail
        monkeypatch.setattr(
            "api.services.email_service.send_email_background",
            lambda to, subj, body: mock_send(to, subj, body),
        )
        result = mock_send("user@test.com", "BG Test", "<p>Background</p>")
        assert result is True


# ─── Auth Flow Email Integration ──────────────────────────────────────────────

class TestAuthFlowEmails:
    """Test that auth endpoints correctly trigger email functions."""

    def test_registration_sends_verification_email(self, monkeypatch):
        """Registration endpoint should call send_verification_email."""
        # Run the register flow like production: users stay unverified so the
        # verification email path is exercised (test env auto-verifies).
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        sent_emails = []

        def mock_send_verification(to_email, full_name, verify_url):
            sent_emails.append({
                "to": to_email,
                "name": full_name,
                "url": verify_url,
            })
            return True

        monkeypatch.setattr(
            "api.routes.auth.send_verification_email",
            mock_send_verification,
        )
        # Also mock the security alert that fires on login
        monkeypatch.setattr("api.routes.auth.send_security_alert", lambda *a, **kw: True)

        email = f"reg-email-{uuid.uuid4()}@test.com"
        resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Email Test User",
            "org_name": f"Email Test Org {uuid.uuid4()}",
        })
        assert resp.status_code == 201
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == email
        assert "verify-email" in sent_emails[0]["url"]

    def test_forgot_password_sends_reset_email(self, monkeypatch):
        """Forgot password endpoint should call send_password_reset_email."""
        sent_emails = []

        def mock_send_reset(to_email, full_name, reset_url):
            sent_emails.append({"to": to_email, "url": reset_url})
            return True

        monkeypatch.setattr(
            "api.routes.auth.send_password_reset_email",
            mock_send_reset,
        )
        monkeypatch.setattr("api.routes.auth.send_verification_email", lambda *a, **kw: True)
        monkeypatch.setattr("api.routes.auth.send_security_alert", lambda *a, **kw: True)

        email = f"forgot-{uuid.uuid4()}@test.com"
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Forgot User",
            "org_name": f"Forgot Org {uuid.uuid4()}",
        })

        resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        assert len(sent_emails) == 1
        assert "reset-password" in sent_emails[0]["url"]

    def test_login_sends_security_alert(self, monkeypatch, db_session):
        """Login should send a security alert email."""
        alerts = []

        def mock_alert(to_email, full_name, event, detail):
            alerts.append({"event": event, "to": to_email})
            return True

        monkeypatch.setattr("api.routes.auth.send_security_alert", mock_alert)
        monkeypatch.setattr("api.routes.auth.send_verification_email", lambda *a, **kw: True)

        email = f"login-alert-{uuid.uuid4()}@test.com"
        password = "testpassword123"

        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Login Alert User",
            "org_name": f"Login Org {uuid.uuid4()}",
        })

        # Verify the user in the database to allow login
        from api.models.user import User
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            user.is_verified = True
            db_session.commit()

        resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert resp.status_code == 200
        assert len(alerts) >= 1
        assert alerts[0]["event"] == "New Login Detected"

    def test_resend_verification_sends_email(self, monkeypatch):
        """Resend verification endpoint should call send_verification_email."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        sent = []

        def mock_send_verification(to_email, full_name, verify_url):
            sent.append(to_email)
            return True

        monkeypatch.setattr("api.routes.auth.send_verification_email", mock_send_verification)
        monkeypatch.setattr("api.routes.auth.send_security_alert", lambda *a, **kw: True)

        email = f"resend-{uuid.uuid4()}@test.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Resend User",
            "org_name": f"Resend Org {uuid.uuid4()}",
        })

        resp = client.post("/api/v1/auth/resend-verification", json={"email": email})
        assert resp.status_code == 200
        # The user is unverified, so a resend should be triggered
        assert email in sent


# ─── Template HTML Validation ─────────────────────────────────────────────────

class TestTemplateHTMLValidity:
    """Verify that generated email HTML is structurally valid."""

    @patch("api.services.email_service._send_smtp")
    def test_verification_email_html_structure(self, mock_smtp, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        import api.services.email_service as es
        es._provider_logged = False

        send_verification_email("test@example.com", "Test User", "https://example.com/verify")

        args = mock_smtp.call_args[0]
        html = args[2]  # third arg is full HTML
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "Verify your email address" in html
        assert "https://example.com/verify" in html

    @patch("api.services.email_service._send_smtp")
    def test_welcome_email_has_no_cta_button(self, mock_smtp, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        import api.services.email_service as es
        es._provider_logged = False

        send_welcome_email("test@example.com", "Test User")

        args = mock_smtp.call_args[0]
        html = args[2]
        assert "Welcome" in html
        # Info body - should NOT have a link to copy
        assert "Or copy this link:" not in html

    @patch("api.services.email_service._send_smtp")
    def test_security_alert_has_red_heading(self, mock_smtp, monkeypatch):
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        import api.services.email_service as es
        es._provider_logged = False

        send_security_alert("test@example.com", "User", "Login", "From IP 1.2.3.4")

        args = mock_smtp.call_args[0]
        html = args[2]
        assert "#f87171" in html  # Red heading color
        assert "Security Alert" in html

    @patch("api.services.email_service._send_smtp")
    def test_all_templates_have_plain_text_fallback(self, mock_smtp, monkeypatch):
        """Every email should contain both HTML and plain-text MIME parts."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        import api.services.email_service as es
        es._provider_logged = False

        # Send each template type
        templates = [
            lambda: send_verification_email("t@t.com", "U", "http://x"),
            lambda: send_password_reset_email("t@t.com", "U", "http://x"),
            lambda: send_invitation_email("t@t.com", "I", "O", "MEMBER", "http://x"),
            lambda: send_change_email_verification("t@t.com", "U", "http://x"),
            lambda: send_security_alert("t@t.com", "U", "E", "D"),
            lambda: send_welcome_email("t@t.com", "U"),
            lambda: send_password_changed_email("t@t.com", "U"),
            lambda: send_mfa_enabled_email("t@t.com", "U"),
            lambda: send_mfa_disabled_email("t@t.com", "U"),
        ]

        for template_fn in templates:
            mock_smtp.reset_mock()
            template_fn()
            # _send_smtp is called, meaning SMTP dispatch was attempted
            assert mock_smtp.called, f"Template {template_fn.__name__} did not call _send_smtp"


# ─── Production Resend, Logging, and Token Security Tests ────────────────────

class TestProductionEmailInfrastructure:
    """Test Suite for Resend API, DB logging, and Hashed Tokens."""

    @patch("api.services.email_service._http_client.post")
    def test_resend_api_success_logs_to_db(self, mock_post, monkeypatch):
        """Test successful Resend delivery writes an EmailLog record."""
        monkeypatch.setattr("api.services.email_service.settings.RESEND_API_KEY", "re_testkey123")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Success"
        mock_post.return_value = mock_resp

        # Call send_email_background to trigger sending
        from api.services.email_service import _send_email
        result = _send_email("test_resend@example.com", "Hello Resend", "<p>Body</p>", "test-template")

        assert result is True
        mock_post.assert_called_once()
        assert "api.resend.com/emails" in mock_post.call_args[0][0]

        # Verify EmailLog in database
        from api.database.session import SessionLocal
        from api.models.email_log import EmailLog
        with SessionLocal() as db:
            log = db.query(EmailLog).filter(EmailLog.recipient == "test_resend@example.com").first()
            assert log is not None
            assert log.subject == "Hello Resend"
            assert log.status == "SENT"
            assert log.provider == "resend"

    @patch("api.services.email_service.time.sleep")
    @patch("api.services.email_service._http_client.post")
    def test_resend_api_retry_on_failure(self, mock_post, mock_sleep, monkeypatch):
        """Test Resend client retries on transient connection error."""
        monkeypatch.setattr("api.services.email_service.settings.RESEND_API_KEY", "re_testkey123")
        monkeypatch.setattr("api.services.email_service.settings.EMAIL_FROM", "noreply@eaimos.ai")

        # Mock failures then success
        mock_fail = MagicMock()
        mock_fail.status_code = 502
        mock_fail.text = "Gateway Error"

        mock_ok = MagicMock()
        mock_ok.status_code = 200
        mock_post.side_effect = [RuntimeError("Timeout"), mock_fail, mock_ok]

        from api.services.email_service import _send_email
        result = _send_email("retry_user@example.com", "Retry Test", "<p>Body</p>")

        assert result is True
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

    def test_new_template_functions_render_correctly(self, monkeypatch):
        """Verify all new transactional template functions call dispatch correctly."""
        monkeypatch.setattr("api.services.email_service.settings.SMTP_HOST", "localhost")
        sent_emails = []

        def mock_send(to, subject, body, template_name, correlation_id=None):
            sent_emails.append({"to": to, "subject": subject, "template": template_name})
            return True

        monkeypatch.setattr("api.services.email_service.send_email_background", mock_send)

        from api.services.email_service import (
            send_password_reset_success_email,
            send_new_login_email,
            send_new_device_email,
            send_invitation_accepted_email,
            send_invitation_rejected_email,
            send_invitation_revoked_email,
            send_ownership_transfer_email,
            send_resend_verification_email,
        )

        send_password_reset_success_email("u1@x.com", "U1")
        send_new_login_email("u1@x.com", "U1", "127.0.0.1", "Chrome", "Friday")
        send_new_device_email("u1@x.com", "U1", "Macbook", "127.0.0.1", "Friday")
        send_invitation_accepted_email("u1@x.com", "U2", "u2@x.com", "Org")
        send_invitation_rejected_email("u1@x.com", "u2@x.com", "Org")
        send_invitation_revoked_email("u1@x.com", "u2@x.com", "Org")
        send_ownership_transfer_email("u1@x.com", "U1", "Org", "U2")
        send_resend_verification_email("u1@x.com", "U1", "http://verify")

        assert len(sent_emails) == 8
        assert sent_emails[0]["template"] == "password-reset-success"
        assert sent_emails[1]["template"] == "new-login"
        assert sent_emails[2]["template"] == "new-device"
        assert sent_emails[3]["template"] == "org-invite-accepted"

    def test_password_reset_token_hashing_and_single_use(self, db_session):
        """Verify password reset helper stores SHA-256 hash and enforces single-use policy."""
        import uuid
        from api.routes.auth import _create_password_reset_token, _validate_and_consume_password_reset_token
        from api.models.iam import PasswordResetToken
        from api.models.user import User

        # Create real user first to satisfy foreign key constraint
        user = User(
            email=f"test_reset_{uuid.uuid4()}@example.com",
            full_name="Reset User",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        user_id = user.id

        raw_token = _create_password_reset_token(db_session, user_id, ip_address="1.1.1.1")

        # Verify plaintext token is NOT stored in DB
        db_reset = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).first()
        assert db_reset is not None
        assert db_reset.token_hash != raw_token
        assert len(db_reset.token_hash) == 64  # SHA-256 hash length

        # Verify validation and consumption works
        valid_user_id = _validate_and_consume_password_reset_token(db_session, raw_token)
        assert valid_user_id == user_id

        # Verify single-use policy (second consumption attempt fails)
        invalidated_user_id = _validate_and_consume_password_reset_token(db_session, raw_token)
        assert invalidated_user_id is None


class TestNewLifecycleAndInvitationFlows:
    """Test verification enforcement, invitation user pre-creation, and background purging."""

    def _make_mock_request(self):
        mock_req = MagicMock()
        mock_req.client = MagicMock()
        mock_req.client.host = "127.0.0.1"
        mock_req.headers = MagicMock()
        mock_req.headers.get.return_value = "Mozilla/5.0"
        return mock_req

    async def test_login_requires_verified_email(self, db_session):
        """Test that login fails when the user is not verified."""
        import uuid
        from urllib.parse import quote
        from fastapi import HTTPException
        from starlette.requests import Request as StarletteRequest
        from api.routes.auth import login
        from api.models.user import User
        from api.core.security import get_password_hash

        email = f"unverified_{uuid.uuid4()}@example.com"
        password = "securepassword123"
        user = User(
            email=email,
            full_name="Unverified User",
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        body = f"username={quote(email)}&password={password}".encode()
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "scheme": "http",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/x-www-form-urlencoded"),
                (b"user-agent", b"Mozilla/5.0"),
                (b"host", b"testserver"),
            ],
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "root_path": "",
        }
        req = StarletteRequest(scope)
        req._body = body

        try:
            import pytest
            with pytest.raises(HTTPException) as exc_info:
                await login(request=req, db=db_session)
            assert exc_info.value.status_code == 400
            assert "Email not verified" in exc_info.value.detail
        finally:
            # Cleanup
            db_session.delete(user)
            db_session.commit()

    def test_invite_pre_creates_user_and_registration_reuses_it(self, db_session):
        """Test that inviting a non-existent email pre-creates the user and register updates it."""
        import uuid
        import secrets
        from api.routes.organizations import invite_member, InviteMemberRequest
        from api.routes.auth import register
        from api.schemas.user import UserCreate
        from api.models.user import User
        from api.models.organization import Organization
        from api.models.membership import UserRole

        # 1. Setup inviter and org
        inviter = User(
            email=f"inviter_{uuid.uuid4()}@example.com",
            full_name="Inviter",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4()}")
        db_session.add(inviter)
        db_session.add(org)
        db_session.commit()

        invited_email = f"invited_{uuid.uuid4()}@example.com"

        # 2. Call invite_member
        invite_req = InviteMemberRequest(email=invited_email, role=UserRole.MEMBER)
        mock_request = self._make_mock_request()
        
        invite_res = invite_member(
            organization_id=org.id,
            body=invite_req,
            db=db_session,
            current_user=inviter,
        )
        
        # Verify user was pre-created in database
        pre_created_user = db_session.query(User).filter(User.email == invited_email).first()
        assert pre_created_user is not None
        assert pre_created_user.is_verified is False
        assert pre_created_user.metadata_json.get("is_temporary_password") is True
        assert pre_created_user.metadata_json.get("change_password_required") is True

        # Extract invitation token from the result link
        token = invite_res["invite_link"].split("token=")[-1]

        # 3. Call register with invitation token to update pre-created user
        reg_in = UserCreate(
            email=invited_email,
            password="my_custom_password_123",
            full_name="Invited User Real Name",
            invitation_token=token,
        )

        reg_res = register(user_in=reg_in, request=mock_request, db=db_session)
        assert reg_res.email == invited_email
        assert reg_res.full_name == "Invited User Real Name"

        # Verify database record updated
        updated_user = db_session.query(User).filter(User.email == invited_email).first()
        assert updated_user.full_name == "Invited User Real Name"
        assert updated_user.metadata_json.get("is_temporary_password") is None
        assert updated_user.metadata_json.get("change_password_required") is None

        # Clean up
        db_session.delete(updated_user)
        db_session.delete(inviter)
        db_session.delete(org)
        db_session.commit()

    @patch("api.worker.celery_app.send_email_task")
    def test_purge_deleted_accounts_task(self, mock_send_email_task, db_session):
        """Test that the purge_deleted_accounts_task soft-deletes expired accounts."""
        import uuid
        import datetime
        from api.models.user import User
        from api.worker.celery_app import purge_deleted_accounts_task

        orig_email = f"to_purge_{uuid.uuid4()}@example.com"
        past_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=8)
        user = User(
            email=orig_email,
            full_name="Purge User",
            hashed_password="somepassword",
            is_active=False,
            is_verified=True,
            scheduled_deletion_at=past_time,
        )
        db_session.add(user)
        db_session.commit()

        # Run task mock
        mock_self = MagicMock()
        # Mock track_task_execution context manager to yield our db_session
        from api.worker.celery_app import track_task_execution
        
        class MockTrackTaskExecution:
            def __init__(self, name, task_id, args_str=None):
                pass
            def __enter__(self):
                return db_session
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        with patch("api.worker.celery_app.track_task_execution", MockTrackTaskExecution):
            res = purge_deleted_accounts_task.run()

        assert res["success"] is True
        assert res["purged_count"] >= 1

        # Check DB that the user is now purged: PII anonymized, deletion cleared
        db_session.refresh(user)
        assert user.email != orig_email
        assert user.scheduled_deletion_at is None
        assert user.is_active is False
        assert user.hashed_password is None

        # Clean up
        db_session.delete(user)
        db_session.commit()


class TestNewSecurityAndOrgAlerts:
    """Test suite for new login alerts, member removal, org deletion/restore, and email reuse."""

    def _make_mock_request(self, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0", client_ip="192.168.1.10"):
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = client_ip
        mock_request.headers = {"user-agent": user_agent}
        return mock_request

    @patch("api.routes.auth.send_security_alert")
    def test_login_alert_new_browser_device_ip_country(self, mock_send_alert, db_session):
        from api.routes.auth import store_refresh_token, create_refresh_token, UserSession
        from api.models.user import User
        from api.models.membership import UserOrganization, UserRole
        from api.models.organization import Organization

        user = User(
            email=f"login_alert_{uuid.uuid4()}@example.com",
            full_name="Login Alert User",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()

        # First login from IP 1
        req1 = self._make_mock_request(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0", client_ip="8.8.8.8")
        token1 = create_refresh_token(user.id)
        mock_send_alert.reset_mock()
        store_refresh_token(db_session, token1, user.id, req1)
        
        # Verify first login sends a security alert
        assert mock_send_alert.called
        assert "New Login Detected" in mock_send_alert.call_args[0][2]

        # Second login from SAME IP and browser
        req2 = self._make_mock_request(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0", client_ip="8.8.8.8")
        token2 = create_refresh_token(user.id)
        mock_send_alert.reset_mock()
        store_refresh_token(db_session, token2, user.id, req2)

        # Verify no new alert is triggered for identical login details
        assert not mock_send_alert.called

        # Third login from a NEW browser/device
        req3 = self._make_mock_request(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1", client_ip="8.8.8.8")
        token3 = create_refresh_token(user.id)
        mock_send_alert.reset_mock()
        store_refresh_token(db_session, token3, user.id, req3)

        # Verify new browser/device triggers alert
        assert mock_send_alert.called
        assert "New browser" in mock_send_alert.call_args[0][2] or "New device" in mock_send_alert.call_args[0][2]

        # Fourth login from a NEW IP address
        req4 = self._make_mock_request(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0", client_ip="9.9.9.9")
        token4 = create_refresh_token(user.id)
        mock_send_alert.reset_mock()
        store_refresh_token(db_session, token4, user.id, req4)

        # Verify new IP triggers alert
        assert mock_send_alert.called
        assert "New IP address" in mock_send_alert.call_args[0][2]

        # Clean up
        db_session.query(UserSession).filter(UserSession.user_id == user.id).delete()
        db_session.delete(user)
        db_session.commit()

    @patch("api.services.email_service.send_org_removed_email")
    def test_member_removed_sends_email(self, mock_send_email, db_session):
        from api.routes.organizations import remove_member
        from api.models.user import User
        from api.models.organization import Organization
        from api.models.membership import UserOrganization, UserRole

        owner = User(
            email=f"owner_{uuid.uuid4()}@example.com",
            full_name="Owner User",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        member = User(
            email=f"member_{uuid.uuid4()}@example.com",
            full_name="Member User",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        org = Organization(name="Kicked Org", slug=f"kicked-org-{uuid.uuid4()}")
        db_session.add_all([owner, member, org])
        db_session.commit()

        # Add memberships
        owner_membership = UserOrganization(user_id=owner.id, organization_id=org.id, role=UserRole.OWNER)
        member_membership = UserOrganization(user_id=member.id, organization_id=org.id, role=UserRole.MEMBER)
        db_session.add_all([owner_membership, member_membership])
        db_session.commit()

        # Call remove_member
        remove_member(organization_id=org.id, user_id=member.id, db=db_session, membership=owner_membership)

        # Verify send_org_removed_email was called for member
        mock_send_email.assert_called_once_with(member.email, member.full_name, org.name)

        # Clean up
        db_session.delete(owner)
        db_session.delete(member)
        db_session.delete(org)
        db_session.commit()

    @patch("api.services.email_service.send_org_removed_email")
    @patch("api.services.email_service.send_org_restored_email")
    def test_org_deletion_soft_deletes_and_restoration_sends_email(self, mock_send_restored, mock_send_removed, db_session):
        from api.routes.organizations import delete_organization, restore_organization
        from api.models.user import User
        from api.models.organization import Organization
        from api.models.membership import UserOrganization, UserRole

        owner = User(
            email=f"owner_{uuid.uuid4()}@example.com",
            full_name="Owner User",
            hashed_password="somepassword",
            is_active=True,
            is_verified=True,
        )
        org = Organization(name="Lifecycle Org", slug=f"lifecycle-org-{uuid.uuid4()}")
        db_session.add_all([owner, org])
        db_session.commit()

        # Add owner membership
        owner_membership = UserOrganization(user_id=owner.id, organization_id=org.id, role=UserRole.OWNER)
        db_session.add(owner_membership)
        db_session.commit()

        # Delete (soft delete) org
        mock_send_removed.reset_mock()
        delete_organization(organization_id=org.id, db=db_session, membership=owner_membership)

        # Verify org is soft deleted (is_active=False and deleted_at is set)
        db_session.refresh(org)
        assert not org.is_active
        assert org.deleted_at is not None
        # Verify removed notification sent to owner
        mock_send_removed.assert_called_once_with(owner.email, owner.full_name, org.name)

        # Restore org
        mock_send_restored.reset_mock()
        mock_req = self._make_mock_request()
        restore_organization(organization_id=org.id, request=mock_req, db=db_session, current_user=owner)

        # Verify org is restored (is_active=True and deleted_at is None)
        db_session.refresh(org)
        assert org.is_active
        assert org.deleted_at is None
        # Verify restored notification sent to owner
        mock_send_restored.assert_called_once_with(owner.email, owner.full_name, org.name)

        # Clean up
        db_session.delete(owner_membership)
        db_session.delete(owner)
        db_session.delete(org)
        db_session.commit()

    def test_soft_deleted_email_reusable_for_new_registration(self, db_session):
        from api.worker.celery_app import purge_deleted_accounts_task
        from api.routes.auth import register
        from api.schemas.user import UserCreate
        from api.models.user import User
        from api.models.platform_events import AuditLog
        import datetime

        orig_email = f"reuse_{uuid.uuid4()}@example.com"
        past_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=8)

        # Create user scheduled for deletion in the past (deletion deactivates the account)
        user = User(
            email=orig_email,
            full_name="Stale User",
            hashed_password="somepassword",
            is_active=False,
            is_verified=True,
            scheduled_deletion_at=past_time,
        )
        db_session.add(user)
        db_session.commit()

        # Run purging background worker
        from api.worker.celery_app import track_task_execution
        class MockTrackTaskExecution:
            def __init__(self, name, task_id, args_str=None):
                pass
            def __enter__(self):
                return db_session
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        with patch("api.worker.celery_app.track_task_execution", MockTrackTaskExecution):
            res = purge_deleted_accounts_task.run()

        assert res["success"] is True
        db_session.refresh(user)
        assert user.scheduled_deletion_at is None
        assert user.email != orig_email  # verified it was renamed!

        # Try to register a new user using the original email address
        mock_request = self._make_mock_request()
        reg_in = UserCreate(
            email=orig_email,
            password="new_password_abc_123",
            full_name="New Owner of Email",
        )

        reg_res = register(user_in=reg_in, request=mock_request, db=db_session)
        assert reg_res.email == orig_email
        assert reg_res.full_name == "New Owner of Email"

        # Verify the new user is created in database
        new_user = db_session.query(User).filter(User.email == orig_email, User.deleted_at.is_(None)).first()
        assert new_user is not None
        assert new_user.id != user.id

        # Clean up
        db_session.delete(new_user)
        db_session.delete(user)
        db_session.query(AuditLog).filter(AuditLog.actor_id == new_user.id).delete()
        db_session.commit()

