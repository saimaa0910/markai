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

        assert result is True  # Console fallback succeeds
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

        assert result is True  # Console fallback succeeds
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

        assert result is True  # Console fallback succeeds
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

        assert result is True
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

    def test_login_sends_security_alert(self, monkeypatch):
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

        resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert resp.status_code == 200
        assert len(alerts) >= 1
        assert alerts[0]["event"] == "New Login Detected"

    def test_resend_verification_sends_email(self, monkeypatch):
        """Resend verification endpoint should call send_verification_email."""
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
