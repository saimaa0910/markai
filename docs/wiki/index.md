# Developer Onboarding & Navigation Guide

## Welcome to the MarkAI Engineering Wiki

This guide provides a step-by-step onboarding walkthrough for software engineers joining the **MarkAI** (EAIMOS) project.

---

## 1. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose
- Poetry (for Python dependency management)

### Setting Up the Environment

1. **Clone & Configure Environment**:
   ```bash
   cp .env.example .env
   ```
2. **Start Infrastructure Services (Database, Redis, MinIO)**:
   ```bash
   docker-compose up -d db redis minio
   ```
3. **Initialize Backend API**:
   ```bash
   cd apps/api
   poetry install
   poetry run alembic upgrade head
   poetry run uvicorn api.main:app --reload --port 8000
   ```
4. **Initialize Web Frontend**:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

---

## 2. Key Code Location Quick Links

- **FastAPI Entry Point**: [main.py](file:///d:/markai/apps/api/src/api/main.py)
- **AI Gateway Proxy**: [coordinator.py](file:///d:/markai/apps/api/src/api/ai/gateway/coordinator.py)
- **Agent Executor**: [agent_executor.py](file:///d:/markai/apps/api/src/api/services/agent_executor.py)
- **RAG Engine**: [rag_engine.py](file:///d:/markai/apps/api/src/api/services/rag_engine.py)
- **Workflow Engine**: [workflow_engine.py](file:///d:/markai/apps/api/src/api/services/workflow_engine.py)
- **Celery Tasks**: [celery_app.py](file:///d:/markai/apps/api/src/api/worker/celery_app.py)
- **Next.js Dashboard App**: [app/dashboard/page.tsx](file:///d:/markai/apps/web/src/app/dashboard/page.tsx)

---

## 3. Engineering Documentation Navigation

- 📘 [Executive Summary](file:///d:/markai/docs/executive-summary.md)
- 📗 [Backend Architecture](file:///d:/markai/docs/architecture/backend.md)
- 📙 [Frontend Architecture](file:///d:/markai/docs/architecture/frontend.md)
- 📕 [AI Platform & Gateway 2.0](file:///d:/markai/docs/ai/ai-platform.md)
- 📓 [Complete API Endpoint Reference](file:///d:/markai/docs/api/reference.md)
- 📒 [Database Architecture & ER Diagrams](file:///d:/markai/docs/architecture/database.md)
