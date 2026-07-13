# Step-by-Step Docker Running Guide for EAIMOS

This guide details how to configure, run, initialize, and verify the Enterprise AI Marketing Operating System (EAIMOS) stack using Docker and Docker Compose.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Docker Engine** (v20.10+ recommended)
- **Docker Compose** (v2.0+ recommended)

---

## 2. Step 1: Set Up Environment Variables

We have mapped the Docker container configurations to reference a root-level `.env` file. 

1. Copy the example environment template into a new `.env` file at the project root:
   ```bash
   cp .env.example .env
   ```
2. Configure the variables inside `.env` if desired:
   - **`SECRET_KEY`**: Signature key for JWT encryption.
   - **AI Provider Keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`)**: Optional keys. If left blank, the gateway will route requests to simulation engines for seamless local mock runs.

---

## 3. Step 2: Spin Up the Docker Ecosystem

Build and launch the complete stack containing PostgreSQL (with PgVector), Redis cache, MinIO Object storage, FastAPI backend API, and Next.js frontend web app:

```bash
# Launch the services in detached background mode
docker compose -f infra/docker/docker-compose.yml up --build -d
```

> [!TIP]
> Use `-f infra/docker/docker-compose.yml` to instruct Docker to use our unified infrastructure configurations context folder.

---

## 4. Step 3: Run Database Migrations Inside Docker

Once the postgres database container is up and healthy, we must run the Alembic database migrations inside the running API container to construct user schemas, organization logs, CRM profiles, and AI libraries.

Execute this single command to migrate the database:

```bash
docker exec -it eaimos-api alembic upgrade head
```

---

## 5. Step 4: Access the Stack

Verify services are up and open the following URLs in your browser:

- **Next.js Web Frontend:** [http://localhost:3000](http://localhost:3000)
- **FastAPI backend Swagger OpenAPI Specs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **MinIO Storage Console:** [http://localhost:9001](http://localhost:9001) (User: `minioadmin`, Pass: `minioadmin`)
- **PostgreSQL Database:** Connected locally at `localhost:5432` (User: `postgres`, Pass: `postgres`, DB: `eaimos`)

---

## 6. Step 5: Verification & Testing inside Containers

> [!NOTE]
> The automated test suite (`pytest`) requires development dependencies which are excluded from the main production container build. To run tests inside the container, you would need to adjust the Dockerfile to install the dev group dependencies, or you can run tests in your local environment.

