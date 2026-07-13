# Running the EAIMOS MVP Stack

This guide details how to configure, run, and verify the Enterprise AI Marketing Operating System (EAIMOS) stack locally.

---

## 1. Development Prerequisites

Ensure you have the following installed on your machine:
1. **Node.js** (v20+ recommended, v26.5.0 verified)
2. **Python** (v3.13+ recommended, v3.13.7 verified)
3. **Poetry** (Python dependency manager, v2.0+ verified)
4. **Docker & Docker Compose**

---

## 2. Environment Variables Configuration

Create a `.env` file in the root directory (or update `/apps/api/.env` and `/apps/web/.env.local`) to configure the services.

### API Environment Variables (`apps/api/.env`)

These variables govern backend services, databases, caching, storage, and authentication.

| Variable | Default Value | Description / Options |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/eaimos` | SQLAlchemy Connection URI. Update to point to your target Postgres host. |
| `REDIS_URL` | `redis://localhost:6379/0` | Connection URI for the Redis caching store. |
| `SECRET_KEY` | `SUPER_SECRET_JWT_KEY_MIN_32_CHARS_LONG_...` | JWT secret signature key. Change this to a secure random hash in production. |
| `MINIO_ENDPOINT` | `localhost:9000` | S3-compatible storage host endpoint. |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key credentials for MinIO storage bucket. |
| `MINIO_SECRET_KEY` | `minioadmin` | Secret key credentials for MinIO storage bucket. |

### Web Environment Variables (`apps/web/.env.local`)

These variables govern frontend interactions with external APIs.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Address of the running FastAPI backend server. |

---

## 3. Launching the Services

### Option A: Using Docker Compose (Recommended)

To run the entire ecosystem (DB with vector support, Redis, MinIO storage, FastAPI Backend, Next.js Frontend) simultaneously:

```bash
# From the root directory, build and run the services in the background
docker compose -f infra/docker/docker-compose.yml up --build -d
```

#### Accessing Services
- **Next.js Web Frontend:** `http://localhost:3000`
- **FastAPI Backend (Swagger API Docs):** `http://localhost:8000/api/v1/docs`
- **MinIO Storage Dashboard:** `http://localhost:9001` (User: `minioadmin`, Pass: `minioadmin`)
- **PostgreSQL Database:** `localhost:5432`

---

### Option B: Running Services Locally (Without Docker)

If you wish to run backend and frontend servers bare-metal for debugging:

#### 1. Start External Dependency Containers
Spin up only the database, cache, and storage:
```bash
docker compose -f infra/docker/docker-compose.yml up db redis minio -d
```

#### 2. Start the API Gateway (Backend)
```bash
cd apps/api
# Install dependencies
poetry install
# Run Alembic DB migrations
poetry run alembic upgrade head
# Start local development server
poetry run uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

#### 3. Start the Web App (Frontend)
```bash
# From the project root workspace
npm install --legacy-peer-deps
npm run web:dev
```
Open `http://localhost:3000` to view the running app.

---

## 4. Verification and Linting Checks

Verify everything runs correctly using built-in scripts:

### Running Tests
- **Backend (FastAPI pytest):**
  ```bash
  cd apps/api
  poetry run pytest
  ```

### Code Quality & Standards Checking
- **Frontend Lints:**
  ```bash
  npm run lint
  ```
- **Backend Lints:**
  ```bash
  cd apps/api
  # Formatting check
  poetry run black --check src
  # Lint check
  poetry run flake8 src
  # Type check
  poetry run mypy src
  ```
