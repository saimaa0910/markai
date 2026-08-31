# EAIMOS Monorepo Packages Workspace

This workspace manages shared packages for the **Enterprise AI Marketing Operating System (EAIMOS)** monorepo.

In accordance with the **Three-Use Rule for Abstraction** ([`enterprise-software-engineering`](file:///C:/Users/admin/.gemini/config/skills/enterprise-software-engineering/SKILL.md)), shared packages are classified into explicit lifecycle tiers:

---

## 1. Tier-1: Active Production Packages

These packages are actively consumed by the frontend (`apps/web`) and build targets:

| Package | Location | Responsibility | Consumer(s) |
|---|---|---|---|
| **`@eaimos/shared`** | [`packages/shared`](file:///d:/markai/packages/shared) | Pure, domain-agnostic utilities (`cn` classnames merger, date formatters). | `apps/web`, `@eaimos/ui` |
| **`@eaimos/ui`** | [`packages/ui`](file:///d:/markai/packages/ui) | Shared domain-agnostic React 19 UI component primitives (`Card`). | `apps/web` |
| **`@eaimos/types`** | [`packages/types`](file:///d:/markai/packages/types) | Shared API response envelopes, audit metadata, and user role types. | `apps/web`, `packages/*` |

---

## 2. Tier-2: Incubation Skeletons (Three-Use Rule Governance)

The following packages are reserved contract interfaces. Per the Three-Use Rule, internal logic remains localized inside `apps/api` and `apps/web` until at least 3 distinct production modules share the exact same lifecycle:

- [`packages/sdk`](file:///d:/markai/packages/sdk): Client SDK interface skeleton.
- [`packages/api-client`](file:///d:/markai/packages/api-client): Isomorphic API client contract skeleton.
- [`packages/feature-flags`](file:///d:/markai/packages/feature-flags): In-memory feature flag engine skeleton.
- [`packages/logger`](file:///d:/markai/packages/logger): TypeScript structured logging utility.
- [`packages/observability`](file:///d:/markai/packages/observability): Tracing and OpenTelemetry wrapper skeleton.
- [`packages/database`](file:///d:/markai/packages/database): Database connection client abstraction.
- [`packages/config`](file:///d:/markai/packages/config): Shared environment configuration skeleton.

> [!NOTE]
> For details on drift tracking and future consolidation roadmaps, see [`DRIFT-REGISTER.md`](file:///d:/markai/DRIFT-REGISTER.md).
