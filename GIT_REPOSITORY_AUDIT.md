# EAIMOS / MarkAI — Master Git Repository Forensic Audit & Existing-Codebase Workflow Analysis

**Audit Date**: August 31, 2026  
**Auditor**: Antigravity Forensic Git Auditor  
**Audit Target**: `d:\markai` repository  
**Mode**: READ-ONLY FORENSIC AUDIT (Zero changes made to Git history, branches, or code)  
**Primary Source of Truth**: Git commit graph, reflogs, branch metadata, remotes, working tree state, and active filesystem.

---

## Executive Summary

| Attribute | State | Details |
|---|---|---|
| **Current Branch** | `ps-f` | Head commit `611b89d` (matches `origin/ps-f`) |
| **Default Branch (Remote HEAD)** | `main` | Head commit `da2c27e` (matches `origin/main`) |
| **Total Local Branches** | 5 | `main`, `dev`, `aifeature`, `local`, `ps-f` |
| **Total Remote Branches** | 5 | `origin/main`, `origin/dev`, `origin/aifeature`, `origin/local`, `origin/ps-f` |
| **Working Tree Status** | **DIRTY** | 7 modified files, 8 deleted docs (relocated), 18 untracked architecture/audit files |
| **Unmerged Branches (vs main)** | 4 | `dev`, `aifeature`, `local`, `ps-f` (All 4 are unmerged into `main`) |
| **Topology Type** | **Strictly Linear Chain** | Every branch is a direct ancestor of `ps-f` along a single timeline |
| **Critical Discovery** | **`main` is empty** | `main` contains only 2 files (`.docx` + `README.md`). 100% of the application code exists ONLY on `ps-f` and its ancestors. |
| **Audit Classification** | `AUDITED ONLY` | No branches created, deleted, merged, rebased, or reset. Working tree preserved. |

---

## 1. Current Git State

### Command Output Summary: `git status --short --branch`
```text
## ps-f
 M apps/api/src/api/models/iam.py
 M apps/api/src/api/services/account_lifecycle_service.py
 M apps/web/public/android-chrome-192x192.png
 M apps/web/public/android-chrome-512x512.png
 M apps/web/src/app/favicon.ico
 M apps/web/src/components/ui/brand-logo.tsx
 M apps/web/src/services/api-client.ts
 D docs/architecture/EAIMOS_Enterprise_Database_Design.md
 D docs/architecture/backend.md
 D docs/architecture/background-processing.md
 D docs/architecture/database.md
 D docs/architecture/dependency-graph.md
 D docs/architecture/frontend.md
 D docs/architecture/service_layer.md
 D docs/architecture/sprint1_core_platform_services.md
?? ARCHITECTURE_FREEZE_REPORT.md
?? DRIFT-REGISTER.md
?? SOURCE_CODE_AUDIT_REPORT.md
?? apps/api/repo.yml
?? apps/api/tests/test_architecture_fitness.py
?? apps/web/public/apple-touch-icon.png
?? apps/web/public/favicon-16x16.png
?? apps/web/public/favicon-32x32.png
?? apps/web/public/favicon.ico
?? apps/web/repo.yml
?? apps/web/src/app/apple-icon.png
?? apps/web/src/app/icon.png
?? apps/web/src/platform/
?? context.yaml
?? docs/architecture/ARCHITECTURE.md
?? docs/architecture/BOUNDARIES.md
?? docs/architecture/DECISIONS.md
?? docs/architecture/DEPENDENCY-RULES.md
?? docs/audit/EAIMOS_Enterprise_Database_Design.md
?? docs/audit/backend.md
?? docs/audit/background-processing.md
?? docs/audit/database.md
?? docs/audit/dependency-graph.md
?? docs/audit/frontend.md
?? docs/audit/service_layer.md
?? docs/audit/sprint1_core_platform_services.md
?? packages/README.md
```

### Remote Configuration (`git remote -v`)
- `origin`: `https://github.com/saimaa0910/markai.git` (fetch)
- `origin`: `https://github.com/saimaa0910/markai.git` (push)

### Remote HEAD
- `remotes/origin/HEAD` -> `origin/main` (at `da2c27e`)

### Sync Status
- Local `ps-f` is at `611b89d9e4c3d053daf777f4d07a345f7d8960d5`
- Remote `origin/ps-f` is at `611b89d9e4c3d053daf777f4d07a345f7d8960d5`
- Ahead of remote: **0 commits** | Behind remote: **0 commits** (In sync)

---

## 2. Complete Branch Inventory

The repository contains exactly **5 branches** (all present locally and mirrored on `origin`).

```
cfa8e5f (Initial commit)
   │
   ▼
da2c27e [main, origin/main, origin/HEAD] (2026-07-13) "roadmap docx added"
   │
   ▼
12a9071 "project setup"
   │
   ▼
b8903c1 "basic site and backend added"
   │
   ▼
23db542 [dev, origin/dev] (2026-07-14) "new features added and depoly through docker is not working"
   │
   ▼ (5 commits: ac88ef0, 1cbf081, f18c616, 38be1a2, 3e8aea8)
   │
afc9377 [aifeature, origin/aifeature] (2026-07-24) "Update README.md"
   │
   ▼ (2 commits: b443ae7, c3f2150)
   │
c3f2150 [local, origin/local] (2026-07-28) "some changes are made. testing added."
   │
   ▼ (6 commits: 20ac55c, 5b098cc, 3041ce2, ee00347, 9c11102, 611b89d)
   │
611b89d [ps-f, origin/ps-f, HEAD] (2026-08-26) "feat: implement comprehensive AI gateway infrastructure..."
```

### Detailed Branch Matrix

| Branch Name | Type | Current Commit | Last Commit Date | Author | Ahead of `main` | Behind `main` | Merged into `main`? | Status / Disposition |
|---|---|---|---|---|---|---|---|---|
| **`main`** | Local / Tracking (`origin/main`) | `da2c27e` | 2026-07-13 11:56:01 +0530 | Saimukhesh | 0 | 0 | Base | **STALE BASELINE / EMPTY** |
| **`dev`** | Local / Tracking (`origin/dev`) | `23db542` | 2026-07-14 12:12:06 +0530 | saimaa0910 | +3 | 0 | No | **STALE CHECKPOINT** (100% in `ps-f`) |
| **`aifeature`**| Local / Tracking (`origin/aifeature`) | `afc9377` | 2026-07-24 10:19:56 +0530 | sai | +9 | 0 | No | **STALE CHECKPOINT** (100% in `ps-f`) |
| **`local`** | Local / Tracking (`origin/local`) | `c3f2150` | 2026-07-28 16:51:21 +0530 | saimaa0910 | +11 | 0 | No | **STALE CHECKPOINT** (100% in `ps-f`) |
| **`ps-f`** | Local / Tracking (`origin/ps-f`) | `611b89d` | 2026-08-26 13:13:26 +0530 | saimaa0910 | +17 | 0 | No | **ACTIVE PRODUCTION HEAD** |

---

## 3. Real Default / Main Branch Determination

- **Configured Default Branch**: `main` (Remote `origin/HEAD` points to `origin/main`).
- **Actual Content of `main`**:
  ```text
  EAIMOS_MVP_Master_Roadmap_Agent_Guide.docx
  README.md
  ```
  `main` contains **zero application code**. It has not been updated since July 13, 2026.
- **De-Facto Development Trunk**: `ps-f` is the true active codebase trunk containing 100% of all platform modules, migrations, tests, and configurations.

---

## 4. What is in `main`?

- **Latest Commit on `main`**: `da2c27e` (*"roadmap docx added"*, July 13, 2026).
- **Total Files in `main`**: 2 files.
- **Codebase Presence**: Zero backend code, zero frontend code, zero packages, zero Docker configurations.
- **Releases / Tags**: 0 tags found (`git tag -l` returns empty).
- **Unmerged Work**: 17 commits representing 1,727 files and 202,580 lines of code exist in `ps-f` that have never been merged back into `main`.

---

## 5. Branch-by-Branch Diff Analysis (vs `main`)

### 1. Branch: `dev`
- **Relationship to `main`**: Ahead by 3 commits, behind by 0 commits.
- **Unique Commits**: `12a9071` (project setup), `b8903c1` (basic site and backend added), `23db542` (new features added...).
- **Diff vs `main`**: 289 files changed, +41,468 insertions, -1 deletion.
- **Major Areas**: Initial FastAPI backend structure, Next.js landing page, base UI components, initial Docker compose.
- **Status**: Historical checkpoint. 100% included in `ps-f`.

### 2. Branch: `aifeature`
- **Relationship to `main`**: Ahead by 9 commits, behind by 0 commits.
- **Ahead of `dev`**: By 6 commits (`ac88ef0`, `1cbf081`, `f18c616`, `38be1a2`, `3e8aea8`, `afc9377`).
- **Diff vs `main`**: 686 files changed, +109,756 insertions, -1,829 deletions.
- **Major Areas**: AI platform core router, knowledge management pages, prompt templates, sprint documentation.
- **Status**: Historical checkpoint. 100% included in `ps-f`.

### 3. Branch: `local`
- **Relationship to `main`**: Ahead by 11 commits, behind by 0 commits.
- **Ahead of `aifeature`**: By 2 commits (`b443ae7`, `c3f2150`).
- **Diff vs `main`**: 928 files changed, +131,207 insertions, -2,221 deletions.
- **Major Areas**: Local email infrastructure testing, initial unit test harness, authentication token utilities.
- **Status**: Historical checkpoint. 100% included in `ps-f`.

### 4. Branch: `ps-f` (Active Working Branch)
- **Relationship to `main`**: Ahead by 17 commits, behind by 0 commits.
- **Ahead of `local`**: By 6 commits:
  - `20ac55c`: added image agent
  - `5b098cc`: fully postgresql integrated (pgvector, async SQLAlchemy session)
  - `3041ce2`: changes in database
  - `ee00347`: added changes in database (40 Alembic migration chain)
  - `9c11102`: feat: implement comprehensive security hardening, audit logging, auth lifecycle services
  - `611b89d`: feat: implement comprehensive AI gateway infrastructure, security hardening, and expanded dashboard feature support
- **Diff vs `main`**: 1,727 files changed, +202,580 insertions, -1 deletion.
- **Major Areas**: 
  - Complete AI Gateway (`coordinator.py`, 13 provider adapters, routing engine, cost accounting)
  - PostgreSQL schema + 40 unbroken Alembic migrations with `pgvector`
  - IAM Subsystem (JWT rotation, TOTP MFA, Account Lockout, Audit Logging)
  - Celery background workers (email, document ingestion, scheduled purge)
  - Next.js 16 App Router frontend (dashboard layouts, playground, settings console, image studio)
  - Comprehensive test suites (`apps/api/tests/`)
- **Status**: Active production-oriented codebase head.

---

## 6. Duplicate Branch Work

Because all 5 branches exist on a **single linear evolutionary line**, there is no branching divergence or competing parallel feature branches.

- `dev`, `aifeature`, and `local` are **sequential checkpoints** created at different dates during development.
- No branch has diverged from this linear spine.
- `ps-f` is the superset containing all changes from `dev`, `aifeature`, and `local`.

---

## 7. Merged and Unmerged Branches

| Branch | Merged into `main`? | Merged into `ps-f`? | Unique Commits not in `ps-f` |
|---|---|---|---|
| `main` | N/A (Baseline) | Yes (Ancestor) | 0 |
| `dev` | **No** | Yes (Ancestor) | 0 |
| `aifeature` | **No** | Yes (Ancestor) | 0 |
| `local` | **No** | Yes (Ancestor) | 0 |
| `ps-f` | **No** | N/A (HEAD) | 6 commits ahead of `local` |

**Conclusion**: All executable code in the repository is currently **unmerged into `main`**.

---

## 8. Current Working Tree Analysis

The working tree on `ps-f` contains unstaged modifications and untracked files:

### Staged Files (0 files)
- None.

### Unstaged Modified Files (7 files)
1. [`apps/api/src/api/models/iam.py`](file:///d:/markai/apps/api/src/api/models/iam.py): Added `last_activity_at` hybrid property alias on `UserSession` for contract backward-compatibility.
2. [`apps/api/src/api/services/account_lifecycle_service.py`](file:///d:/markai/apps/api/src/api/services/account_lifecycle_service.py): Added `export_account_data` alias pointing to `export_user_data`.
3. [`apps/web/src/components/ui/brand-logo.tsx`](file:///d:/markai/apps/web/src/components/ui/brand-logo.tsx): Updated Viptant brand SVG emblem and sizing.
4. [`apps/web/src/services/api-client.ts`](file:///d:/markai/apps/web/src/services/api-client.ts): Integrated `getSafeErrorMessage` error leak-stop into Axios response interceptor.
5. [`apps/web/public/android-chrome-192x192.png`](file:///d:/markai/apps/web/public/android-chrome-192x192.png): Updated branding icon binary.
6. [`apps/web/public/android-chrome-512x512.png`](file:///d:/markai/apps/web/public/android-chrome-512x512.png): Updated branding icon binary.
7. [`apps/web/src/app/favicon.ico`](file:///d:/markai/apps/web/src/app/favicon.ico): Updated branding icon binary.

### Unstaged Deleted Files (8 files - Relocated to `docs/audit/`)
- `docs/architecture/EAIMOS_Enterprise_Database_Design.md`
- `docs/architecture/backend.md`
- `docs/architecture/background-processing.md`
- `docs/architecture/database.md`
- `docs/architecture/dependency-graph.md`
- `docs/architecture/frontend.md`
- `docs/architecture/service_layer.md`
- `docs/architecture/sprint1_core_platform_services.md`

### Untracked Files (18 files / directories)
- **Architecture Governance & Drift**:
  - `SOURCE_CODE_AUDIT_REPORT.md`
  - `ARCHITECTURE_FREEZE_REPORT.md`
  - `DRIFT-REGISTER.md`
  - `context.yaml`
  - `apps/api/repo.yml`
  - `apps/web/repo.yml`
  - `packages/README.md`
- **Updated Architecture Specifications**:
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/BOUNDARIES.md`
  - `docs/architecture/DECISIONS.md`
  - `docs/architecture/DEPENDENCY-RULES.md`
- **Historical Audit Documents**:
  - `docs/audit/*` (8 relocated files)
- **Architecture Fitness Test**:
  - `apps/api/tests/test_architecture_fitness.py`
- **Web Platform Hardening**:
  - `apps/web/src/platform/auth/session-contract.ts`
  - `apps/web/src/platform/errors/user-message.ts`
- **Branding Assets**:
  - `apps/web/public/apple-touch-icon.png`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon.ico`, `src/app/apple-icon.png`, `src/app/icon.png`

---

## 9. Commit History Analysis

### Commit Style Evolution
1. **Early Phase (July 13 – July 28, 2026)**:
   - Ad-hoc, informal commit messages: `"project setup"`, `"basic site and backend added"`, `"new features added and depoly through docker is not working"`, `"some changes are made. testing added."`.
2. **Database Integration Phase (August 05 – August 10, 2026)**:
   - Concise database-focused messages: `"added image agent"`, `"fully postgresql integrated"`, `"changes in database"`, `"added changes in database"`.
3. **Enterprise Hardening Phase (August 20 – August 26, 2026)**:
   - Standardized Conventional Commits:
     - `feat: implement comprehensive security hardening, audit logging, and auth lifecycle services with updated API routing and web interface components.` (`9c11102`)
     - `feat: implement comprehensive AI gateway infrastructure, security hardening, and expanded dashboard feature support` (`611b89d`)

### Commit Size
- Commits are **extremely large and monolithic** (e.g. `611b89d` touches 258 files with 19,369 additions and 8,027 deletions).
- Commits bundle backend, frontend, database, configuration, and documentation changes together.

---

## 10. Current Git Workflow

### Observed Workflow Pattern
```
main (2 commits)
  │
  └── dev (pushed directly to origin/dev)
        │
        └── aifeature (pushed directly to origin/aifeature)
              │
              └── local (pushed directly to origin/local)
                    │
                    └── ps-f (pushed directly to origin/ps-f)
```

### Key Workflow Observations
1. **No Pull Requests to `main`**: Development progressed through linear branch hopping without merging back to `main`.
2. **CI Bypass**: `.github/workflows/ci-cd.yml` triggers on pushes/PRs to `main` and `master`. Because development was conducted on `dev`, `aifeature`, `local`, and `ps-f`, the CI workflow was never triggered on GitHub Actions.
3. **No Git Tags / Release Strategy**: No version tags exist in Git history.

---

## 11. Existing-Codebase Impact (Risk of Data Loss)

If the non-main branches were deleted, **100% of the active product would be lost**.

### Critical Subsystems Residing Exclusively in `ps-f`:
1. **Central AI Gateway & Provider Engine**: Coordinator, circuit breakers, fallback router, token cost accounting, 13 provider adapters.
2. **IAM & Security Subsystem**: Refresh token family rotation, TOTP MFA, bcrypt hashing, account lockout, audit logging.
3. **PostgreSQL & Database Migrations**: 40 linear Alembic revisions (`84fd17436689` to `9a1b2c3d4e5f`), pgvector schema, async SQLAlchemy.
4. **Celery Worker Engine**: Celery Beat schedules, email dispatchers (Resend + SMTP fallback), async ingestion.
5. **Next.js 16 Web Application**: Feature-based frontend (Playground, Compare Lab, Image Studio, Prompts, Knowledge, Settings).
6. **Backend Test Suites**: Sprint test suites and API integration test suites in `apps/api/tests/`.

---

## 12. Architecture Alignment Findings

- The code on `ps-f` implements the **Modular Monolith** target architecture (FastAPI backend + Next.js App Router + Celery + PostgreSQL + Redis + MinIO).
- 5 specific architectural drifts were cataloged in `DRIFT-REGISTER.md` (DRIFT-001: localStorage JWTs, DRIFT-002: In-memory events vs Outbox, DRIFT-003: Stub packages in `packages/*`, DRIFT-004: Test contract mismatches, DRIFT-005: Client error leak-stop).

---

## 13. Git Safety Check

- **Unpushed Commits**: 0 (All 5 branches are synced with their `origin` counterparts).
- **Detached HEAD**: No. HEAD is properly attached to branch `ps-f`.
- **Git Stashes**: 2 stashes present (`stash@{0}` on `aifeature`, `stash@{1}` on `main`).
- **Orphaned Commits**: None. All commits belong to the linear ancestry chain of `ps-f`.

---

## 14. Recommended EAIMOS Git Workflow

For this existing codebase, the recommended workflow is:

```
                  ┌─────────────────────────────────┐
                  │       main (Protected Trunk)    │
                  └────────────────┬────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌────────────────────────┐    ┌────────────────────────┐
       │ fix/api-test-baseline  │    │ feature/image-agent    │
       └────────────┬───────────┘    └────────────┬───────────┘
                    │                             │
                    ▼                             ▼
           [Quality Gates: CI]           [Quality Gates: CI]
           - Python lint & pytest        - Python lint & pytest
           - Next.js lint & build        - Next.js lint & build
           - Docker builds               - Docker builds
                    │                             │
                    └──────────────┬──────────────┘
                                   │ (Squash & Merge / Merge Commit)
                                   ▼
                  ┌─────────────────────────────────┐
                  │       main (Updated Trunk)      │
                  └─────────────────────────────────┘
```

### Why this fits EAIMOS:
1. Eliminates branch sprawl and stale linear chains.
2. Activates the existing GitHub Actions CI pipeline on every PR.
3. Enforces short-lived branches (1 task = 1 branch).
4. Keeps `main` deployable at all times.

---

## 15. Proposed Future Branch Structure

```text
main                    # Production-ready trunk (protected)

feature/<domain-topic>  # e.g. feature/social-agent-runtime
fix/<issue-topic>       # e.g. fix/userrole-model-collision
security/<scope>        # e.g. security/zero-token-bff
refactor/<subsystem>    # e.g. refactor/iam-service-consolidation
test/<gate-topic>       # e.g. test/ci-architecture-fitness
ci/<pipeline-topic>     # e.g. ci/docker-healthcheck-matrix
chore/<task-topic>      # e.g. chore/monorepo-package-consolidation
```

---

## 16. Existing Branch Disposition Plan (Recommended)

| Branch | Action | Justification |
|---|---|---|
| **`ps-f`** | **PROMOTE / BASELINE TO `main`** | Contains the entire active system. Must become `main` before starting new feature branches. |
| **`local`** | **ARCHIVE** | Historical checkpoint; 100% superseded by and contained within `ps-f`. |
| **`aifeature`** | **ARCHIVE** | Historical checkpoint; 100% superseded by and contained within `ps-f`. |
| **`dev`** | **ARCHIVE** | Historical checkpoint; 100% superseded by and contained within `ps-f`. |
| **`main`** | **ALIGN WITH `ps-f`** | Currently holds only 2 files; needs fast-forward / promotion to represent the true codebase. |

*Note: In accordance with audit constraints, NO actions have been taken. These are governance recommendations.*

---

## 17. Main Branch Policy

### Current State
- `main` is completely unpopulated (2 files), has no branch protection rules active, and receives no commits.

### Recommended State
1. **Branch Protection Enabled**: Require Pull Request before merging.
2. **Status Checks Required**:
   - `backend-lint-test` (flake8, black, pytest with coverage)
   - `frontend-lint-build` (npm run lint, npm run web:build)
   - `docker-build-check` (API & Web Docker builds)
3. **No Direct Pushes**: All changes must arrive via reviewed pull requests.
4. **Clean Git History**: Merge via linear merge or squash merge with Conventional Commit headers.

---

## 18. Commit Practice Standards

EAIMOS will enforce standard **Conventional Commits**:

```text
<type>(<scope>): <concise description in imperative present tense>

Types:
- feat: New feature or capability
- fix: Bug fix
- security: Security fix, auth hardening, isolation enforcement
- refactor: Code refactoring without behavioral changes
- test: Adding or updating tests
- ci: CI/CD workflow changes
- build: Dependency or build tooling changes
- chore: Routine maintenance tasks
- docs: Documentation changes
- perf: Performance improvements

Scopes:
- api, web, iam, ai-gateway, providers, agents, db, celery, security, shared
```

---

## 19. Risks

1. **Risk of Accidental Branch Deletion**: If `ps-f` were deleted or force-reset before promotion to `main`, all product code would be destroyed.
2. **CI Inactivity**: CI is currently silent because work is pushed to non-`main` branches.
3. **Uncommitted Working Tree**: 7 modified files and 18 untracked files on `ps-f` need review and structured commit before switching branches.

---

## 20. Next Safe Action

1. **Keep working tree and branches intact** (zero destructive Git actions).
2. Create an atomic commit on `ps-f` for the uncommitted architecture audit governance and platform hardening files.
3. Prepare a governed fast-forward / promotion of `ps-f` to `main` so the primary branch reflects the true state of the repository.
4. Transition to trunk-based short-lived branches (`fix/*`, `feat/*`) branching off `main`.
