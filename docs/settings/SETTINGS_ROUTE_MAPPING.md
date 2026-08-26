# EAIMOS Settings Platform — Comprehensive Information Architecture & Route Mapping

**Version:** EAIMOS Enterprise v2.4  
**Date:** 2026-08-26  
**Status:** COMPLETE & VERIFIED  

---

## 1. Full Settings Architecture Hierarchy

```
Settings
│
├── Platform Settings (/dashboard/settings)
│   ├── General
│   │   ├── Platform Name
│   │   ├── Default Landing Page
│   │   ├── Default Dashboard
│   │   └── General Platform Configuration
│   │
│   ├── Localization
│   │   ├── Default Language
│   │   ├── Default Time Zone
│   │   ├── Date Format
│   │   └── Number Format
│   │
│   ├── Regional Settings
│   │   ├── Country / Region
│   │   ├── Currency
│   │   └── Regional Defaults
│   │
│   ├── System Behavior
│   │   ├── Default Pagination
│   │   ├── Session Preferences
│   │   ├── Auto Refresh
│   │   └── Default View Preferences
│   │
│   └── Platform Defaults
│       ├── Default AI Model
│       ├── Default AI Provider
│       ├── Default Notification Behavior
│       └── Default Platform Preferences
│
├── Account & Profile (/dashboard/settings/account, /dashboard/settings/profile)
│   ├── Profile Information
│   ├── Email Address
│   ├── Email Verification
│   ├── Profile Picture
│   └── Account Status
│
├── Security & Passwords (/dashboard/settings/security)
│   ├── Change Password
│   ├── Password Security
│   ├── Two-Factor Authentication
│   │   ├── MFA Status
│   │   ├── Setup Authenticator
│   │   ├── Verify Authenticator
│   │   └── Recovery Codes
│   ├── Security Alerts
│   └── Active Sessions
│
├── Users & Teams (/dashboard/settings/users)
│   ├── Users
│   ├── Teams
│   ├── Invitations
│   ├── Roles
│   ├── Permissions
│   └── Organization Memberships
│
├── Integrations (/dashboard/settings/integrations, /dashboard/settings/connected-apps)
│   ├── Connected Integrations
│   ├── OAuth Applications
│   ├── API Integrations
│   ├── Webhooks
│   ├── Integration Credentials
│   ├── Sync Jobs
│   └── Integration Logs
│
├── Organization (/dashboard/settings/organization)
│   ├── Organization Profile
│   ├── Organization Name
│   ├── Organization Slug
│   ├── Organization Members
│   ├── Roles & Access
│   ├── Plan & Tier
│   ├── Usage & Limits
│   └── Organization Security
│
├── Privacy & Data (/dashboard/settings/privacy)
│   ├── Privacy Settings
│   ├── Data Management
│   ├── Data Export
│   ├── Account Deactivation
│   ├── Account Deletion
│   └── Data Retention
│
├── Billing & Subscriptions (/dashboard/settings/billing)
│   ├── Current Plan
│   ├── Subscription
│   ├── Payment Methods
│   ├── Invoices
│   ├── Credits
│   ├── Usage & Metering
│   └── Billing Alerts
│
├── API Credentials (/dashboard/settings/credentials)
│   ├── API Keys
│   ├── Key Permissions / Scopes
│   ├── IP Allowlist
│   ├── Expiration
│   ├── Revoke Key
│   └── API Key Activity
│
├── Connected Apps (/dashboard/settings/connected-apps)
│   ├── OAuth Accounts
│   ├── Connected Providers
│   ├── Authorized Applications
│   ├── Permissions
│   └── Revoke Access
│
└── Preferences (/dashboard/settings/preferences)
    ├── Appearance
    ├── Notifications
    ├── Email Preferences
    ├── Language
    ├── Time Zone
    └── Other User Preferences
```

---

## 2. Canonical Route Mapping Table

| Section | Frontend Canonical Route | Component Location | Backing APIs / Services |
| :--- | :--- | :--- | :--- |
| **Platform Settings** | `/dashboard/settings` | `src/app/dashboard/settings/page.tsx` | `GET /users/me`, `PATCH /users/me/preferences` |
| **Account & Profile** | `/dashboard/settings/account` | `src/app/dashboard/settings/account/page.tsx` | `GET /users/me`, `PATCH /users/me`, `POST /users/me/avatar` |
| **Profile Alias** | `/dashboard/settings/profile` | `src/app/dashboard/settings/profile/page.tsx` | Re-exports `AccountSettingsPage` |
| **Security & Passwords** | `/dashboard/settings/security` | `src/app/dashboard/settings/security/page.tsx` | `POST /auth/password-change`, `GET /security/sessions`, `GET /security/recovery-codes` |
| **Users & Teams** | `/dashboard/settings/users` | `src/app/dashboard/settings/users/page.tsx` | `GET /organizations/{id}/members/`, `POST /organizations/{id}/invitations/` |
| **Integrations** | `/dashboard/settings/integrations` | `src/app/dashboard/settings/integrations/page.tsx` | `GET /integrations/providers`, `POST /integrations/connect` |
| **Connected Apps** | `/dashboard/settings/connected-apps`| `src/app/dashboard/settings/connected-apps/page.tsx` | Connected OAuth applications & integration tokens |
| **Organization** | `/dashboard/settings/organization` | `src/app/dashboard/settings/organization/page.tsx` | `GET /organizations/{id}/settings`, `PATCH /organizations/{id}/settings` |
| **Privacy & Data** | `/dashboard/settings/privacy` | `src/app/dashboard/settings/privacy/page.tsx` | `GET /account/privacy-dashboard`, `POST /account/export`, `POST /account/deletion/request` |
| **Billing & Subscriptions** | `/dashboard/settings/billing` | `src/app/dashboard/settings/billing/page.tsx` | `GET /billing/subscription`, `GET /billing/plans`, `POST /billing/checkout` |
| **API Credentials** | `/dashboard/settings/credentials` | `src/app/dashboard/settings/credentials/page.tsx` | `GET /api-keys/`, `POST /api-keys/`, IP allowlist |
| **Preferences** | `/dashboard/settings/preferences` | `src/app/dashboard/settings/preferences/page.tsx` | `PATCH /users/me/preferences`, `ThemeSwitcher` |
| **Canonical Dashboard** | `/dashboard` | `src/app/dashboard/page.tsx` | Core platform overview |
