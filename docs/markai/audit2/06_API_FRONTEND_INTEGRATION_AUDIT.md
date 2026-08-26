# EAIMOS API ↔ Frontend Integration Audit
## 06 — API / Frontend Integration Audit

Scope: every frontend consumer of Core Platform and AI Gateway functionality, verified against actual backend endpoints.

---

## 6.1 API client layer

File: `apps/web/src/services/api-client.ts` (89 lines)
- Base URL: `NEXT_PUBLIC_API_URL` env, else `http://localhost:8000/api/v1` (browser on :3000) or `/api/v1` (SSR). **No `.env*` in `apps/web` → env var never set → hardcoded localhost fallback in all non-proxy environments.** (`3-8`)
- Request interceptor reads `localStorage['eaimos-auth-storage']`, attaches `Authorization: Bearer` + `X-Organization-ID`. (`16-39`)
- Response interceptor: 401 → `POST /auth/refresh?refresh_token=...` → retry with `_retry`; refresh failure → clear storage + redirect `/auth/login?expired=true`. (`42-89`)
- Query defaults (provider): staleTime 60 s, refetchOnWindowFocus false, retry 1.

**Gaps**
| ID | Finding |
|----|---------|
| FE-01 | Access token in localStorage (XSS exposure); no httpOnly cookie; refresh token in URL query string (`:60`). |
| FE-02 | No `middleware.ts` → route protection is client-side only (`layouts/dashboard-layout.tsx:39-63`). |
| FE-03 | Hardcoded base URL fallback; no per-environment config committed. |

---

## 6.2 Core Platform consumers

| Page | Real API | Mocks / gaps |
|---|---|---|
| `auth/login/page.tsx` | POST /auth/login → GET /users/me → GET /organizations (`:52-66`) | none |
| `auth/register/page.tsx` | POST /auth/register (`:41`) | sends `org_name`, not org join |
| `forgot/reset/verify` | POST /auth/forgot-password, reset-password, verify-email | forgot-password prints recovery URL to **backend logs** (info leak) |
| `dashboard/users/page.tsx` | GET /organizations/{id}/members/ (+ /users fallback `:54-64`); invite → POST /auth/register (`:78`); deactivate → PATCH /users/{id} (`:96`) | ROLE_CONFIG hardcoded (`:34-39`); invites create users via public register |
| `dashboard/settings/page.tsx` | GET /users/me, members, invitations; PATCH /users/me (`:27-46,113`) | **API keys hardcoded local state (`:81-83`); avatar upload simulated (`:210`); `hasPermission` uses client-side `permissions.includes` (`:265-267`)** |
| `dashboard/page.tsx` | /crm/leads, /crm/contacts, /generator | **Mock chart data `// Visual Mock Chart Data` (`:74-85`)**; audit section text-only (`:261`) |
| `crm` (815 ln) | /crm/companies|contacts|leads|activities CRUD | none found |
| `campaigns` (400 ln) | /campaigns/ CRUD | analytics fallback hardcoded numbers (`:64-66`) |
| `files` (312 ln) | /files/ multipart upload/delete | none |
| `conversations` (1632 ln) | /chat/conversations CRUD + streaming `fetch` (`:802`) + export `window.open` (`:923`) | none major |

---

## 6.3 AI Gateway consumers

Real API layer: `features/ai-platform/hooks/index.ts` (668 ln) — useModels `/ai/models/`, useUsage `/ai/usage/`, useRouting `/ai/routing-rules/`, useProviderHealth `/ai/providers/{id}/health`, useIncidents `/ai/providers/health/incidents`, useAdminConsoleLimits `/ai/providers/limits|keys/`; `useObservability.ts` → `/observability/*`; knowledge/prompts services are real.

| Page | Real API | Mocks / gaps |
|---|---|---|
| `dashboard/ai/page.tsx` | conversations/prompts/messages real (`:51-67`) | **Mock streaming animation (`:44-46,132-134,162-176,399`)**; dropzone stores locally only (`:207-216`) |
| `playground.tsx` | real `POST /ai/playground/stream` (`:169`) | `TEMPLATES` hardcoded with `sampleResponse` (`:26-48+`) |
| `compare.tsx` | real `POST /ai/compare/` (`:135`) | `MODEL_PRESETS` hardcoded (`:28-79`); qualityScore hardcoded per provider (`:155`) |
| `health.tsx` | real health endpoint | mock timeline pulses (`:132-137`), mock retry/success % (`:179-183`) |
| `observability.tsx` | real `/observability/*` | "Simulated Alert Fired" toast (`:76`); mock child spans (`:541-547`); "Simulate Outage Events" (`:678-680`) |
| `analytics.tsx` | real usage | static `radarData` (`:81-86`); `heatmapData` uses `Math.random()` (`:96`) |
| `settings.tsx` | — | **API keys form is local-state only; save just toasts "saved" (`:79-86`); `API_KEYS_CONFIG` hardcoded (`:19-48`)** |
| `admin.tsx` | — | `MOCK_AUDITS` hardcoded (`:34-38`), seeded state (`:45`) |
| `infrastructure/page.tsx` | — | `CACHE_CHART_DATA` mock (`:19-27`) |
| `router/page.tsx` | real `POST /ai/router/simulate` (`:82-84`) | simulation endpoint (backend) |
| knowledge pages | real services | simulated progress intervals, mockStorage chart (`dashboard.tsx:44-60`), simulated step activation (`search:34`, `embeddings:26`) |
| prompts pages | real services | simulated typing (`testing.tsx:75`), "Simulation Complete" toast (`:109`), simulated editor wrapper (`editor.tsx:149`) |

---

## 6.4 Integration issues

| ID | Sev | Finding |
|----|-----|---------|
| INT-01 | HIGH | AI settings page cannot persist API keys (local-state only) → users cannot configure providers from UI despite backend endpoints existing. |
| INT-02 | HIGH | `useEmbeddings` model list hardcoded (`hooks/index.ts:388-392`) — diverges from backend registry. |
| INT-03 | MEDIUM | Usage/analytics dashboards mix backend synthetic rows (`seed_dummy_usages`) with real data → misleading figures. |
| INT-04 | MEDIUM | Backend contract drift: `Permission.resource/action/scope` missing in DB; frontend permission checks therefore unreliable. |
| INT-05 | MEDIUM | `PATCH /organizations/{id}` expects `name` query param — frontend sends body → likely silent 422/400. (Verify at runtime.) |
| INT-06 | LOW | Marketing/product "simulators" are client-side mock animations (acceptable for marketing pages; not to be mistaken for product). |
| INT-07 | LOW | No frontend automated tests configured (no jest/vitest/playwright/cypress in `package.json`). |

---

## 6.5 Verdict
Backend↔frontend wiring exists for most real features (auth, orgs, users, CRM, chat+streaming, knowledge, prompts, AI playground/compare/health/usage/routing). Gaps are concentrated in: AI settings key persistence, mock chart/animation data in production UI, localStorage token handling, and missing server-side route protection.