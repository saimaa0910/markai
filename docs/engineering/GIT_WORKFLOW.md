# EAIMOS Engineering Git Workflow & Standards

## 1. Executive Summary & Trunk Policy

The Enterprise AI Marketing Operating System (EAIMOS / MarkAI) uses a disciplined, trunk-based product engineering Git workflow.

- **`main`**: The single source of truth and protected integration trunk.
  - Direct commits to `main` are strictly forbidden.
  - All modifications must arrive via Pull Requests (PR) from short-lived task branches.
  - Automated CI quality gates must pass before merge.
  - History is kept clean, linear, and reproducible.
- **Historical Branches**: `ps-f`, `dev`, `aifeature`, and `local` are preserved as immutable archive references.

---

## 2. Branch Naming Conventions

All engineering work must take place on short-lived branches created from the latest `main`.

| Prefix | Usage | Example |
| :--- | :--- | :--- |
| `feat/` | New features or platform capabilities | `feat/image-studio-generation` |
| `fix/` | Bug fixes and runtime corrections | `fix/userrole-tenant-isolation` |
| `security/` | IAM, cryptography, and vulnerability remediation | `security/jwt-rotation-killswitch` |
| `refactor/` | Structural code improvements with no contract change | `refactor/ai-gateway-adapter-isolation` |
| `test/` | Test suites, fixtures, and regression coverage | `test/vector-similarity-quality-gate` |
| `ci/` | CI/CD pipelines, Docker, and automation workflows | `ci/github-actions-service-containers` |
| `chore/` | Dependencies, configuration, and documentation | `chore/update-drift-register` |

### One Task Per Branch Rule
Branches must be atomic and scoped to **one logical engineering task**. Do not bundle unrelated IAM changes, AI Gateway modifications, and frontend features into a single branch.

---

## 3. Commit Convention (Conventional Commits)

All commits must follow the Conventional Commits specification:

```
<type>(<scope>): <short description in imperative mood>

[optional body explaining rationale and technical context]

[optional footer(s)]
```

### Allowed Types:
- `feat`: New user-facing or platform functionality
- `fix`: Bug fix in production or test runtime
- `security`: Security, authentication, and authorization hardening
- `refactor`: Code restructuring without functional changes
- `test`: Adding, updating, or correcting test contracts
- `ci`: CI pipeline and build automation adjustments
- `build`: Build system or dependency updates
- `docs`: Documentation updates
- `perf`: Performance improvements
- `chore`: Maintenance tasks

---

## 4. Standard Development Cycle

```
                       MAIN (latest)
                             │
                             ▼
                    Create Task Branch
                             │
                             ▼
                   Inspect Existing Code
                             │
                             ▼
                     Run Baseline Tests
                             │
                             ▼
                 Implement Minimal Change
                             │
                             ▼
                   Targeted Verification
                             │
                             ▼
                  Full Test Suite & Lints
                             │
                             ▼
                   Review Local Diff
                             │
                             ▼
                   Conventional Commit
                             │
                             ▼
                     Push & Open PR
                             │
                             ▼
                    Automated CI Gates
                             │
                             ▼
                   Peer Review & Approval
                             │
                             ▼
                 Squash & Merge to Main
                             │
                             ▼
                   Delete Remote Branch
                             │
                             ▼
                   Update Local Main
```

---

## 5. Pull Request Standards

Every Pull Request must include the standard EAIMOS PR description:

```markdown
## Problem
Summary of the problem or feature requirement being addressed.

## Solution
Technical overview of what was changed and why.

## Scope
List of modified modules and packages.

## Tests
- Automated test command and output summary (e.g., 668/668 passed).
- Architecture fitness verification (4/4 passed).

## Database
Schema migrations introduced (if any) and verified single alembic head.

## Security & Tenant Isolation
Impact on IAM, RBAC, tenant data isolation, or credentials.

## Architecture Boundaries
Verification that clean/hexagonal boundaries and central AI Gateway rules are preserved.

## Risk & Rollback
Potential failure modes and exact rollback procedure.
```

---

## 6. Automated CI Quality Gates

The GitHub Actions CI pipeline (`.github/workflows/ci.yml`) enforces the following quality gates on every Pull Request to `main`:

1. **Architecture Fitness Gate**: Zero layer boundary violations (`test_architecture_fitness.py`).
2. **Database Migration Verification Gate**: 
   - Verify single migration head (`alembic heads`).
   - Apply linear migrations to fresh database (`alembic upgrade head`).
   - Validate active revision matches single head (`alembic current`).
3. **Backend Pytest Suite Gate**: 100% green execution across all test suites with pgvector PostgreSQL and Redis service containers.
4. **Frontend TypeScript Check Gate**: `npm run typecheck` (`tsc --noEmit`) with 0 errors.
5. **Frontend Production Build Gate**: `npm run web:build` with Next.js Turbopack compilation.
6. **Docker Compose & Build Gate**: Validate compose specification (`docker compose config`) and build all application containers (`docker compose build`).
7. **Docker Runtime Smoke Test Gate**: Launch stack (`docker compose up -d`), verify health/readiness endpoints (`/health`, `/live`, `/ready`, `:3000`, `:80`), and cleanly tear down (`docker compose down -v`).

### Real AI Provider Testing Policy
- **Pull Request CI**: Strictly uses deterministic unit/integration mocks and contract tests. Zero external AI API calls (Groq, OpenAI, Google, Anthropic) are made in PR validation.
- **Staging / Nightly Validation**: Controlled live provider health circuits run separately via `.github/workflows/ai-smoke-tests.yml` with dedicated secrets on a scheduled/manual basis.

---

## 7. Code Review & Architecture Invariants

Reviewers must verify that every PR adheres to the frozen architecture invariants:
- **No IAM Bypass**: All tenant resources must enforce tenant boundaries via `UserOrganization` membership and context authorizers.
- **No Direct Provider Access**: All AI model queries must route through the central `AIGateway` (`src/api/ai/gateway/coordinator.py`). Frontend must never call external LLM providers directly.
- **No Duplicate Runtimes**: Agent workflows must leverage the generic agent orchestration platform.
- **Error Privacy**: API routes must catch and encapsulate internal error traces, emitting standard error envelopes.
- **Zero Committed Secrets**: `.env`, service keys, or certificates must never be committed.

---

## 8. Merge & Branch Cleanup Policy

- **Merge Method**: Prefer **Squash and Merge** for feature and task PRs to maintain a clean, readable integration history on `main`.
- **Branch Deletion**: Short-lived task branches must be deleted immediately upon successful merge.
- **Historical Branch Immunity**: Do not delete or rebase historical development branches (`ps-f`, `dev`, `aifeature`, `local`).

---

## 9. Emergency Hotfix Procedure

In the event of a production defect on `main`:
1. Create a `fix/hotfix-<issue>` branch directly from `main`.
2. Implement the minimal fix with accompanying regression test.
3. Verify test suite and architecture fitness locally.
4. Open an expedited PR with `[HOTFIX]` tag.
5. Merge via CI and deploy.
