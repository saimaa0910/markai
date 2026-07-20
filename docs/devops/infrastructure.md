# Infrastructure & Docker Setup

## Overview

The containerized infrastructure of **MarkAI** is managed via **Docker Compose** (`docker-compose.yml`). The stack includes 11 microservice containers spanning data persistence, application runtimes, reverse proxying, telemetry collection, and metrics visualization.

---

## Infrastructure Container Topology

```mermaid
graph TD
    User([External Client Request]) --> Nginx[Nginx Reverse Proxy\nPort 80]
    
    Nginx -->|Proxy /api| API[FastAPI Gateway Engine\nPort 8000]
    Nginx -->|Proxy /| Web[Next.js 15 Web Application\nPort 3000]
    
    API --> DB[(PostgreSQL Database\nPort 5432)]
    API --> Redis[(Redis Broker / Cache\nPort 6379)]
    API --> MinIO[(MinIO Object Storage\nPorts 9000 / 9001)]
    API --> OtelCollector[OTEL Collector\nPorts 4317 / 4318]

    subgraph Async Processing
        Redis --> Worker[Celery Task Worker]
        Redis --> Scheduler[Celery Beat Scheduler]
        Worker --> DB
        Worker --> MinIO
    end

    subgraph Observability Stack
        API -->|Metrics Endpoint| Prometheus[Prometheus TSDB\nPort 9090]
        NodeExporter[Node Exporter\nPort 9100] --> Prometheus
        Prometheus --> Grafana[Grafana Dashboard\nPort 3001]
    end
```

---

## Docker Container Catalog

| Container Name | Base Image / Dockerfile | Exposed Ports | Primary Purpose | Health Check |
| :--- | :--- | :--- | :--- | :--- |
| `eaimos-postgres` | `./infra/docker/postgres/Dockerfile` | `5432` | Relational database (PostgreSQL) | `pg_isready -U postgres` |
| `eaimos-redis` | `redis:7-alpine` | `6379` | Cache manager & Celery broker | `redis-cli ping` |
| `eaimos-minio` | `minio/minio:RELEASE...` | `9000`, `9001` | S3-compatible file object storage | `curl http://localhost:9000/minio/health/live` |
| `eaimos-api` | `./infra/docker/api/Dockerfile` | `8000` | FastAPI ASGI backend gateway | `curl http://localhost:8000/live` |
| `eaimos-worker` | `./infra/docker/api/Dockerfile` | None | Distributed Celery task worker | Inherits container health |
| `eaimos-scheduler` | `./infra/docker/api/Dockerfile` | None | Celery Beat periodic job scheduler | Inherits container health |
| `eaimos-web` | `./infra/docker/web/Dockerfile` | `3000` | Next.js frontend web app | `wget http://localhost:3000/` |
| `eaimos-nginx` | `nginx:1.25-alpine` | `80` | Ingress reverse proxy & SSL wrapper | `wget http://localhost/` |
| `eaimos-prometheus` | `prom/prometheus:v2.52.0` | `9090` | Time-series metrics collection | Internal health check |
| `eaimos-grafana` | `grafana/grafana:11.0.0` | `3001` | System & latency metric dashboards | Internal health check |
| `eaimos-otel-collector`| `otel/opentelemetry-collector-contrib` | `4317`, `4318` | Tracing telemetry collector | Internal health check |
