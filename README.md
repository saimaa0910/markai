# Viptant - Enterprise AI Marketing System platform

Viptant (MarkAI) is a multi-tenant Enterprise AI Platform and Marketing System Platform. It enables organizations to coordinate campaign channels, generate copywriting variant drafts, swap and monitor LLM providers, override dynamic model routing paths, track token consumption rates, and control credit budgets.

## Documentation

For full details on directories, technology stack, SQLAlchemy schemas, backend routers, custom Zustand/Query hooks, and the dashboard modules, see:

- [Project Architecture Documentation](file:///d:/markai/docs/project_architecture_documentation.md)

## Apps and Workspaces

- **FastAPI backend**: Located in `apps/api/`
- **Next.js web client**: Located in `apps/web/`
- **Shared packages**: Located in `packages/shared/`

---

## How to Run

Before running the application, make sure you copy the environment template `.env.example` to `.env` in the root directory:
```bash
cp .env.example .env
```

### Running with Docker Compose (Recommended)

To run the entire platform with all dependencies (PostgreSQL, Redis, MinIO, Celery worker/scheduler, Prometheus, Grafana, OpenTelemetry Collector) preconfigured and integrated:

```bash
# Start all services
docker compose up --build

# Run only the backend and its databases (Postgres, Redis, MinIO)
docker compose up api db redis minio --build

# Run only the frontend web client
docker compose up web --build
```

---

### Running Manually

Ensure you have a PostgreSQL instance running with the databases `eaimos_local` and `eaimos_test` created (with `pgvector`, `uuid-ossp`, `pg_trgm`, and `unaccent` extensions enabled), a running Redis server, and a running MinIO server.

#### 1. Backend (FastAPI) Setup

Navigate to the backend directory:
```bash
cd apps/api
```

Install python dependencies:
```bash
poetry install
```

Apply Alembic migrations to your database:
```bash
poetry run alembic upgrade head
```

Run the FastAPI development server:
```bash
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Run the Celery worker for asynchronous jobs (in a separate terminal):
```bash
poetry run celery -A api.worker.celery_app worker --loglevel=info
```

#### 2. Frontend (Next.js) Setup

From the root directory of the workspace, install all Node.js workspace dependencies:
```bash
npm install
```

Start the Next.js development server:
```bash
npm run web:dev
```
*(Or navigate to `apps/web/` and run `npm run dev` directly).*

