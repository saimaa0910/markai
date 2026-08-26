# EAIMOS Account & Settings Navigation Specification

## Overview
This specification details the lifecycle and state transitions for the authenticated user profile and the contextual Settings navigation system.

---

## 1. Interaction State Machine

```mermaid
stateDiagram-v2
    [*] --> AvatarResting: User logged in

    state "Sidebar Profile (Bottom Left)" as ProfileArea {
        AvatarResting: Initial State (Avatar icon only)
        HoverCard: Hover/Focus State (Shows Name & Email tooltip)
        AccountMenu: Clicked State (Full Account Menu Dropdown)

        AvatarResting --> HoverCard: onMouseEnter / onFocus
        HoverCard --> AvatarResting: onMouseLeave / onBlur
        AvatarResting --> AccountMenu: onClick / Enter / Space
        HoverCard --> AccountMenu: onClick
        AccountMenu --> AvatarResting: Click outside / Escape / Select item
    }

    state "Sidebar Navigation List" as NavList {
        NormalNav: Standard Platforms (Dashboard, AI, Playground, etc.)
        SettingsContextNav: Standard Platforms + Contextual Settings Group

        NormalNav --> SettingsContextNav: Navigate to /dashboard/settings/*
        SettingsContextNav --> NormalNav: Navigate to non-settings route
    }
```

---

## 2. Route & Ownership Matrix

| Feature | Accessible via | Target Canonical Route | Backend Domain | RBAC Scoping |
| :--- | :--- | :--- | :--- | :--- |
| **Profile / Platform Settings** | Account Menu ➔ Profile Settings | `/dashboard/settings` | User / IAM Backend | All authenticated users |
| **Security & MFA** | Account Menu ➔ Security | `/dashboard/settings/security` | Auth / IAM Backend | User-scoped |
| **Active Sessions** | Account Menu ➔ Active Sessions | `/dashboard/settings/security` | Sessions Backend | User-scoped |
| **Users & Teams** | Account Menu ➔ Users & Teams | `/dashboard/settings/users` | IAM / Core Platform | Admin / Super Admin |
| **Integrations** | Account Menu ➔ Integrations | `/dashboard/settings/integrations` | Integrations Engine | Admin / Super Admin |
| **Sign Out** | Account Menu ➔ Sign Out | `/auth/login` | Auth Token Revocation | All authenticated users |
