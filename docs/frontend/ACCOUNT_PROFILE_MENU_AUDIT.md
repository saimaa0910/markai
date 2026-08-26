# EAIMOS Account Profile Menu & Contextual Settings Audit

## Executive Summary
This audit documents the frontend architecture and user interaction design for the authenticated-user profile area, account menu popover, and contextual settings navigation across EAIMOS.

---

## 1. Information Architecture & Navigation Rules

### Sidebar Profile State (Bottom-Left)
1. **Initial State**:
   - Only the user's circular avatar / dynamic initial (`U` or full name initials) is rendered.
   - User full name and email are **hidden by default** in the resting sidebar state.
   - Profile image is rendered dynamically if `user.metadata_json.avatar_url` is present, otherwise computed initials.
2. **Hover / Focus State**:
   - Hovering or keyboard-focusing the avatar reveals a floating account info card (`Avatar + User Name + Email`).
   - The card appears adjacent to the avatar without expanding the entire sidebar or causing layout shift.
   - Debounced pointer handlers prevent UI flickering when moving cursor between avatar and card.
3. **Click / Activation State**:
   - Clicking the avatar or pressing `Enter`/`Space` opens the enterprise-grade **Account Menu**.
   - Contains: User preview header with role badge, navigation links to Settings, Security & MFA, Active Sessions, Users & Teams, Integrations, and a direct Sign Out action.
   - Accessibility: Keyboard dismiss via `Escape`, outside click backdrop, `aria-haspopup="menu"`, `aria-expanded`.

---

## 2. Contextual Settings Navigation Rules

1. **Normal Dashboard Browsing**:
   - `Settings` is **NOT** present in the default sidebar navigation list.
   - Navigation focuses strictly on core workflows: Dashboard, AI Platform, Playground, Prompt Platform, Knowledge Platform, AI Agents, Workflow Engine, Marketing, CRM, and Analytics.
2. **Inside Settings Area (`/dashboard/settings` and child routes)**:
   - When the user accesses Settings (via Account Menu, direct URL, or Command Palette), the sidebar dynamically displays **Settings** as the active contextual section.
   - It exposes:
     - `Users & Teams` (`/dashboard/settings/users`)
     - `Integrations` (`/dashboard/settings/integrations`)
     - `Security & Sessions` (`/dashboard/settings/security`)
     - `Platform Settings` (`/dashboard/settings`)
3. **Leaving Settings Area**:
   - When the user navigates back to any platform section (e.g., AI Platform, Playground, Dashboard), the contextual Settings item disappears from the sidebar.

---

## 3. Files Inspected & Modified

| File Path | Nature of Inspection / Change |
| :--- | :--- |
| `apps/web/src/layouts/dashboard-layout.tsx` | Implemented avatar initial state, hover tooltip card, click popover menu, and `isInsideSettings` contextual group. |
| `apps/web/src/store/auth.ts` | Verified `useAuthStore`, user profile attributes (`full_name`, `email`, `role`, `is_superuser`, `metadata_json`), and `logout()` flow. |
| `apps/web/src/app/dashboard/settings/*` | Audited existing settings pages (`page.tsx`, `account`, `security`, `privacy`, `organization`, `members`, `users`, `integrations`). |
