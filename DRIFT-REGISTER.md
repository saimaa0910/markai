# Enterprise Architecture Drift Register

**Product:** Enterprise AI Marketing Operating System (EAIMOS / Viptant)  
**Level:** L1 — Product  
**Status:** Active  
**Evidence State:** `verified`  
**Last Verified:** 2026-08-31  

This ledger records all verified divergences between architectural standards, documentation, and active codebase implementation. It protects deliberate design trade-offs and prevents silent, uncoordinated architectural drift.

---

### DRIFT-001: Client-Side JWT Storage in LocalStorage vs. Zero-Token BFF

| Field | Detail |
|---|---|
| **ID** | `DRIFT-001` |
| **Area** | `security` |
| **Claim** | Enterprise architecture standard mandates Zero-Token Browser Isolation with same-origin BFF and HttpOnly `__Host-` cookies. |
| **Reality** | Next.js frontend stores raw `accessToken` and `refreshToken` in `localStorage` under key `eaimos-auth-storage`. Next.js proxy uses `eaimos.session=1` purely as an unencrypted client-side route guard marker. |
| **Evidence** | Primary source: [`apps/web/src/store/auth.ts:48-79`](file:///d:/markai/apps/web/src/store/auth.ts#L48-L79), [`apps/web/src/proxy.ts:31-50`](file:///d:/markai/apps/web/src/proxy.ts#L31-L50), and [`apps/web/src/services/api-client.ts:18-42`](file:///d:/markai/apps/web/src/services/api-client.ts#L18-L42). |
| **Severity** | **high** (Tokens in browser storage are susceptible to client-side script inspection / XSS extraction). |
| **Affected repos** | `apps/web`, `apps/api` |
| **Owner level** | product |
| **Recommended action** | Execute planned migration to Next.js route handler BFF with encrypted HttpOnly session cookies and `PublicSession` metadata. |
| **Status** | `open` |
| **Last verified** | 2026-08-31 |

---

### DRIFT-002: In-Memory Event Dispatcher vs. Database Transactional Outbox

| Field | Detail |
|---|---|
| **ID** | `DRIFT-002` |
| **Area** | `contract` |
| **Claim** | Domain events and state mutations must be persisted atomically inside the same database transaction to guarantee at-least-once delivery. |
| **Reality** | Domain events are dispatched through in-memory `EventDispatcher` and Celery worker tasks without a dedicated atomic PostgreSQL `platform.outbox` table. |
| **Evidence** | Primary source: [`apps/api/src/api/services/base/event_dispatcher.py:19-115`](file:///d:/markai/apps/api/src/api/services/base/event_dispatcher.py#L19-L115) and [`apps/api/src/api/events/events.py:18-44`](file:///d:/markai/apps/api/src/api/events/events.py#L18-L44). |
| **Severity** | **medium** (Process crashes between DB commit and Celery enqueue risk losing outbound event delivery). |
| **Affected repos** | `apps/api` |
| **Owner level** | repository |
| **Recommended action** | Introduce `platform_outbox` table in a future migration with an asynchronous worker poll loop. |
| **Status** | `open` |
| **Last verified** | 2026-08-31 |

---

### DRIFT-003: Phantom Monorepo Package Stubs Violating Three-Use Rule

| Field | Detail |
|---|---|
| **ID** | `DRIFT-003` |
| **Area** | `distribution` |
| **Claim** | Monorepo packages in `packages/*` represent reusable, shared cross-project libraries with $\ge 2$ consumers. |
| **Reality** | 7 of 10 packages in `packages/*` (`sdk`, `api-client`, `config`, `database`, `feature-flags`, `logger`, `observability`) are single-file skeleton stubs with `TODO` comments that are not imported by `apps/web` or `apps/api`. |
| **Evidence** | Primary source: [`packages/sdk/src/index.ts`](file:///d:/markai/packages/sdk/src/index.ts), [`packages/api-client/src/index.ts`](file:///d:/markai/packages/api-client/src/index.ts), [`packages/database/src/index.ts`](file:///d:/markai/packages/database/src/index.ts). |
| **Severity** | **low** (Maintenance clutter and cognitive overhead). |
| **Affected repos** | `packages/*` |
| **Owner level** | product |
| **Recommended action** | Explicitly declare Tier-1 production packages (`shared`, `ui`, `types`) and consolidate or document stubs until multi-consumer requirements emerge. |
| **Status** | `in-progress` |
| **Last verified** | 2026-08-31 |

---

### DRIFT-004: Sprint 8.3.1 Service Contract vs. Test Signature Mismatch

| Field | Detail |
|---|---|
| **ID** | `DRIFT-004` |
| **Area** | `status` |
| **Claim** | All test suites in `apps/api/tests/` accurately exercise and validate production services. |
| **Reality** | Production services were upgraded to DDD-style `ServiceContext` + DTO contracts, while Sprint 8.3.1 tests invoked them with legacy plain kwargs (`db=...`), causing test suite failures. |
| **Evidence** | Primary source: [`docs/sprint_8_3_1_diagnosis.md`](file:///d:/markai/docs/sprint_8_3_1_diagnosis.md), [`apps/api/tests/sprint_8_3_1/`](file:///d:/markai/apps/api/tests/sprint_8_3_1). |
| **Severity** | **high** (CI quality gates blocked by contract mismatches). |
| **Affected repos** | `apps/api` |
| **Owner level** | repository |
| **Recommended action** | Fix model bugs (`UserSession` timezone import, column names, audit log imports) and align tests to production service contracts. |
| **Status** | `in-progress` |
| **Last verified** | 2026-08-31 |

---

### DRIFT-005: Absence of Centralized Client Error Leak-Stop

| Field | Detail |
|---|---|
| **ID** | `DRIFT-005` |
| **Area** | `security` |
| **Claim** | Frontend code must never render raw backend error strings, database schema exceptions, or stack traces directly in UI components. |
| **Reality** | Frontend components across `apps/web/src/features/` pass raw `err.response?.data?.detail` and `err.message` directly to `toast.error()`. |
| **Evidence** | Primary source: [`apps/web/src/features/prompts/hooks/index.ts:220`](file:///d:/markai/apps/web/src/features/prompts/hooks/index.ts#L220), [`apps/web/src/features/ai-platform/pages/conversations.tsx:647`](file:///d:/markai/apps/web/src/features/ai-platform/pages/conversations.tsx#L647). |
| **Severity** | **medium** (Internal details and technical errors exposed to end users). |
| **Affected repos** | `apps/web` |
| **Owner level** | repository |
| **Recommended action** | Implement `src/platform/errors/user-message.ts` mapping machine codes to localized safe UI copy. |
| **Status** | `in-progress` |
| **Last verified** | 2026-08-31 |
