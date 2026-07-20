# Enterprise AI Platform: Observability Implementation Details

This document outlines the detailed software and infrastructure components built during the Phase 1D (Enterprise Observability) implementation.

## Backend Observability Architecture

### 1. Telemetry Core Helper (`api/core/telemetry.py`)
- Initializes OpenTelemetry `TracerProvider` with dynamic standard service name configuration.
- Configures OpenTelemetry `OTLPCollector` exporters to publish traces over gRPC/HTTP endpoints.
- Auto-instruments SQLAlchemy database operations and Redis client commands.
- Implements `start_span` context manager for custom spans.
- Exposes a `get_current_trace_and_span_ids` helper that resolves trace IDs using active contexts, with a `ContextVar`-based pseudo-trace fallback for self-contained database audits (enabling logging even when the external OTel collector is offline).

### 2. Prometheus Registry (`api/core/metrics_registry.py`)
- Sets up custom multi-dimensional gauges, counters, and histograms for:
  - Gateway Traffic (`ai_requests_total`, `ai_request_latency_seconds`)
  - Operational Costs (`ai_cost_usd_total`)
  - Token Consumption (`ai_token_usage_total`)
  - Gateway Errors (`ai_errors_total` at router, provider, and security layers)
  - Failovers & Retries (`ai_failovers_total`, `ai_retries_total`)
  - Cache Operations (`ai_cache_hits_total`, `ai_cache_misses_total`)
  - Background Queues (`celery_queue_length`, `celery_active_workers`)
- Exposes a background scraper to gather system and database statistics dynamically.

### 3. Structured Logging Config (`api/core/logging.py`)
- Configures `structlog` to output structured JSON format logs.
- Automatically scrubs sensitive credentials, authorization tokens, and API keys.
- Injects `trace_id` and `span_id` context headers into all console logging entries.

### 4. Observability Middlewares
- **LoggingMiddleware (`api/middleware/logging.py`)**:
  - Resolves standard `x-correlation-id` and `x-request-id` from incoming request headers (generating new ones if absent).
  - Injects correlation and trace headers back to the caller in HTTP response headers.
  - Automatically writes access log summaries to the database `ai_logs` table (excluding telemetry endpoints to prevent database bloat).
- **TelemetryMiddleware (`api/middleware/telemetry_middleware.py`)**:
  - Hooks FastAPI endpoints to report latency histograms and HTTP error counts directly to the Prometheus metrics registry.

### 5. Alert & Incident Engine (`api/services/alert_engine.py`)
- **Incident Manager**:
  - Registers active outages in the database `ai_incidents` table.
  - Dedupes recurring alerts and tracks resolution states automatically.
- **Alert Dispatcher**:
  - Dispatches incident notifications across multiple integrations: console logs, mock SMTP server emails, Slack incoming webhooks, and custom JSON webhook targets.

### 6. Background Task Telemetry (`api/worker/celery_app.py`)
- Hooks Celery task signals to trace background job executions inside OpenTelemetry spans.
- Automatically records task failures and dispatches warnings to the Alert Engine.

### 7. Observability API Router (`api/routes/observability.py`)
- `/api/v1/observability/health`: Detailed health checks of Database, Redis, Celery, and Telemetry.
- `/api/v1/observability/metrics`: Raw Prometheus scraper endpoint.
- `/api/v1/observability/traces`: Fetches execution traces.
- `/api/v1/observability/logs`: Searchable JSON structured logs.
- `/api/v1/observability/incidents` & `/alerts`: Manage alerts and resolutions.
- `/api/v1/observability/performance`: Computes latency percentiles (P50, P90, P95, P99) and costs.
- `/api/v1/observability/live`: Real-time system snapshot (traffic, workers, cache ratio).
- `/api/v1/observability/alerts/test`: Simulated incident dispatch test.

---

## Infrastructure Monitoring Configuration

### 1. Prometheus Scraping Configuration (`infra/docker/prometheus/prometheus.yml`)
- Configures a 15-second scraping interval target directed at the FastAPI observability metrics route.
- Includes target definitions for `node-exporter` to aggregate VM-level CPU/memory stats.

### 2. OTel Collector pipeline (`infra/docker/otel-collector/otel-collector-config.yaml`)
- Declares standard OTLP receivers on gRPC (4317) and HTTP (4318) ports.
- Employs batch processors and routes traces to console logging for validation.

### 3. Docker Compose Services
- Integrated Prometheus, Grafana, OTel Collector, and Node Exporter services into the root `docker-compose.yml`.
