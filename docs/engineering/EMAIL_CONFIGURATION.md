# EAIMOS Email Environment Configuration: Mailpit & Brevo SMTP

## Overview

EAIMOS provides a centralized, environment-driven transactional email architecture supporting multiple delivery channels:

1. **Local Development**: Mailpit (default, fully containerized SMTP + Web UI sandbox).
2. **Real-Email Testing / Staging**: Brevo SMTP (opt-in transactional delivery with personal verified sender).
3. **Production**: Resend REST API or Custom Enterprise SMTP.

All outbound transactional email flows (account verification, password reset, invitations, security alerts, notifications) traverse the central `api.services.email_service` abstraction.

---

## 1. Local Development Mode (Mailpit)

When developing locally or spinning up the Docker stack (`docker compose up -d`), Mailpit captures all outbound emails without transmitting messages to the public internet.

### Configuration (`.env` or Docker Defaults)

```dotenv
EMAIL_PROVIDER=mailpit
EMAIL_FROM=developer@example.test
EMAIL_FROM_NAME=EAIMOS Platform

SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
```

### Accessing the Mailpit Inbox UI

* **URL**: [http://localhost:8025](http://localhost:8025)
* **SMTP Port**: `localhost:1025` (inside Docker network: `mailpit:1025`)
* **Features**:
  * Real-time WebSocket inbox updates.
  * Full HTML rendering and plain-text inspection.
  * Direct clickable verification and password reset action buttons.
  * Zero external internet access or credentials required.

---

## 2. Real-Email Testing Mode (Brevo SMTP)

For manual staging verification or testing real inbox delivery without purchasing/owning a custom domain, Brevo SMTP can be enabled.

### Requirements

* A free/standard [Brevo (formerly Sendinblue)](https://www.brevo.com/) account.
* A verified sender email address (e.g., your personal Gmail or work email verified in Brevo Sender Management).
* Brevo SMTP key (generated in *SMTP & API* settings).

> [!NOTE]
> **No Custom Domain Required for Dev Testing**: Brevo permits sending transactional emails from verified personal email addresses without configuring DKIM/SPF DNS records on a custom domain.

### Configuration (`.env` — NEVER commit to Git)

```dotenv
EMAIL_PROVIDER=brevo_smtp

# Sender MUST be verified in Brevo Send & API settings
EMAIL_FROM=your_verified_personal_email@gmail.com
EMAIL_FROM_NAME=EAIMOS Platform

# Brevo SMTP Relay
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_brevo_smtp_login
SMTP_PASSWORD=your_brevo_smtp_key
SMTP_TIMEOUT=30
```

### Invariant & Error Handling

* If `EMAIL_PROVIDER=brevo_smtp` and `SMTP_USER` or `SMTP_PASSWORD` is missing, the service logs a clear configuration error, writes a `FAILED` log, and **will NOT silently fall back to Mailpit**.
* Connections to port 587 automatically execute `STARTTLS` negotiation.

---

## 3. Production Delivery (Resend REST API)

For production deployment with verified domains:

```dotenv
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=EAIMOS Platform
```

---

## 4. Security Invariants

* **Backend-Only**: SMTP credentials and Resend API keys are strictly confined to the backend API (`api.core.config`). No `NEXT_PUBLIC_*` email variables exist in the frontend.
* **Redaction & Logging**: SMTP passwords, API keys, and Authorization headers are never logged. Log messages only report `recipient`, `subject`, `latency`, and `provider`.
* **CI Determinism**: GitHub Actions PR CI runs deterministically with `EMAIL_PROVIDER=mailpit` (or test doubles). Real external network calls to Brevo or Resend are never required for PR quality gates.
