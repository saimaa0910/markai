# MarkAI Engineering Documentation Master Index

Welcome to the official engineering documentation for **MarkAI** (**Enterprise AI Marketing Operating System - EAIMOS**).

This documentation was generated through a comprehensive code audit of the entire repository. Every section references actual source code files, database models, API controllers, React components, and infrastructure setups.

---

## Documentation Directory Map

### 1. High-Level Overviews
- 📄 [Executive Summary](file:///d:/markai/docs/executive-summary.md) — Purpose, current capabilities, tech stack, maturity assessment.
- 📋 [Feature Inventory](file:///d:/markai/docs/features/inventory.md) — Comprehensive catalog of all implemented platform features.
- 📦 [Module Documentation Index](file:///d:/markai/docs/modules/index.md) — Deep-dive breakdown into every application module.

---

### 2. Architecture & Subsystems
- ⚙️ [Backend Architecture](file:///d:/markai/docs/architecture/backend.md) — FastAPI layered architecture, dependency injection, request lifecycle.
- 🖥️ [Frontend Architecture](file:///d:/markai/docs/architecture/frontend.md) — Next.js 15 App Router, Zustand state stores, Axios API client.
- 🤖 [AI Platform & Gateway 2.0](file:///d:/markai/docs/ai/ai-platform.md) — Multi-provider proxying, SSE streaming, router engine, security pipeline.
- 🕵️ [AI Agent Engine & Tooling](file:///d:/markai/docs/ai/ai-agents.md) — Autonomous agent runtime, multi-step planner, memory manager, tool registry.
- 🔄 [Workflow Automation Engine](file:///d:/markai/docs/workflow/engine.md) — Node-graph execution engine, condition evaluation, step statuses.
- ⚡ [Background Processing (Celery & Redis)](file:///d:/markai/docs/architecture/background-processing.md) — Distributed worker pipeline, cron schedules, telemetry tracking.
- 🔒 [Security Architecture, Auth & RBAC](file:///d:/markai/docs/security/security-architecture.md) — JWT tokens, multi-tenancy, RBAC permissions, encryption.
- 📊 [System Dependency Graphs](file:///d:/markai/docs/architecture/dependency-graph.md) — Module, service, database, and API dependency diagrams.

---

### 3. API & Database Specifications
- 📡 [API Endpoint Reference](file:///d:/markai/docs/api/reference.md) — Method, route, auth requirements, request/response models, source file links.
- 🗄️ [Database Architecture & ER Diagrams](file:///d:/markai/docs/architecture/database.md) — Entity-relationship diagram, 32 table schema specifications.
- 🛠️ [Service Catalog](file:///d:/markai/docs/services/catalog.md) — Operational specifications for all 19 FastAPI service classes.

---

### 4. Code Audit & Quality Reports
- 🔍 [Database Audit Report](file:///d:/markai/docs/audit/database-audit.md) — Missing indexes, potential N+1 query patterns, unused tables.
- 📈 [Code Quality Audit](file:///d:/markai/docs/audit/code-quality-audit.md) — Maintainability, large file analysis, refactoring recommendations.
- ⚠️ [Technical Debt & TODOs Report](file:///d:/markai/docs/reports/technical-debt.md) — Mocked integrations, fallback simulations, temporary workarounds.
- 🚀 [Production Readiness Matrix](file:///d:/markai/docs/reports/production-readiness.md) — Operational readiness evaluation across 9 enterprise pillars.

---

### 5. Infrastructure & Operations
- 🐳 [Infrastructure & Docker Setup](file:///d:/markai/docs/devops/infrastructure.md) — 11-container topology, Nginx reverse proxy, OpenTelemetry, Prometheus.
- 🔧 [Configuration Reference](file:///d:/markai/docs/devops/configuration.md) — Environment variables, default settings, Pydantic BaseSettings.
- 🧪 [Testing Suite & Coverage Inventory](file:///d:/markai/docs/testing/test-suite.md) — Inventory of 30 backend test files, fixtures, testing gaps.
- 🖼️ [Visual Architecture & Sequence Diagrams](file:///d:/markai/docs/diagrams/architecture-diagrams.md) — Architecture, SSE streaming, and RAG sequence diagrams.
- 📖 [Developer Onboarding Wiki Guide](file:///d:/markai/docs/wiki/index.md) — Setup instructions and navigation quick links.
