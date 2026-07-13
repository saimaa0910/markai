# Sprint 0: Project Initialization and Development Environment Setup - Implementation Plan

This plan details the initialization of the Enterprise AI Marketing Operating System (EAIMOS) repository using a monorepo architecture. We establish the directory structure, package management, Docker orchestration, base DB models/migrations, and linting/formatting standards.

## Proposed Structure
- npm workspaces for TypeScript packages (`apps/web`, `packages/ui`, `packages/shared`, `packages/types`).
- Poetry for managing Python packages in the API package (`apps/api`).
- Docker Compose dev stack containing PostgreSQL (with `pgvector` enabled), Redis, and MinIO.

## Components Created

### 1. Root Workspace Configuration
- `package.json`: Configures workspaces.
- `tsconfig.json`: Declares base TS settings and path maps.
- `.gitignore`: Configures ignores for python, npm, environment secrets, and IDE configs.

### 2. Frontend Workspace (apps/web)
- Next.js App Router workspace with Tailwind CSS.
- Main landing page showcasing status checks.

### 3. Backend Workspace (apps/api)
- Poetry configuration (`pyproject.toml`).
- FastAPI entrypoint (`src/main.py`) with health routes.
- Base DB Model (`src/database/base.py`) with audit columns.
- Alembic database migration environment.

### 4. Shared Packages (packages/*)
- `@eaimos/types`: Common TypeScript types.
- `@eaimos/shared`: Tailwind class merger and date utility helpers.
- `@eaimos/ui`: Sleek glassmorphic shared card component.

### 5. Infrastructure (infra/*)
- Custom PostgreSQL + pgvector Dockerfile.
- Multi-stage Dockerfiles for Next.js Web and FastAPI API.
- Docker Compose orchestration.
