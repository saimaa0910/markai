# Enterprise AI Platform: Telemetry, Logging & Alerting Reference Guide

This guide details the schemas, formats, and channels used by Viptant's Enterprise Observability system.

## 1. Trace and Span Database Schema (`AITrace`)

Self-contained spans are recorded directly in the database (`ai_traces` table) to display timelines directly in the admin dashboard:

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique primary key |
| `trace_id` | String(32) | Hexadecimal correlation trace identifier |
| `span_id` | String(16) | Hexadecimal span identifier |
| `parent_span_id` | String(16) | Hexadecimal parent span identifier (nullable) |
| `name` | String(256) | Span operation name (e.g. `gateway.openai.gpt-4o`) |
| `organization_id` | UUID | Associated Organization (nullable) |
| `user_id` | UUID | Associated User (nullable) |
| `start_time` | DateTime | Timestamp when the operation began |
| `end_time` | DateTime | Timestamp when the operation finished |
| `duration_ms` | Integer | Computation time in milliseconds |
| `status` | String(50) | Status code: `success` or `error` |
| `error_message` | Text | Description of failures (nullable) |
| `attributes` | JSONB / Text | Key-value pairs containing provider, model, tokens, costs |

---

## 2. Structured JSON Log Schema (`AILog`)

Logs are stored in the `ai_logs` table for central searchability and access audits:

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Log record ID |
| `trace_id` | String(32) | Trace ID context (nullable) |
| `span_id` | String(16) | Span ID context (nullable) |
| `correlation_id` | String(100) | Correlation ID header value (nullable) |
| `request_id` | String(100) | Unique request tracking ID (nullable) |
| `timestamp` | DateTime | Log generation timestamp |
| `level` | String(20) | Log severity level: `INFO`, `WARNING`, `ERROR` |
| `logger` | String(100) | Logger source module name |
| `message` | Text | Log summary message |
| `payload` | JSONB / Text | Additional metadata parameters (latency, status codes, endpoints) |

---

## 3. Prometheus Metrics Reference

Metrics are exposed on `/api/v1/observability/metrics` in the standard Prometheus exposition format:

### Gateway Metrics
- `ai_requests_total`: Counter tracking execution loads.
  - *Labels*: `organization_id`, `provider`, `model`, `status`.
- `ai_request_latency_seconds`: Histogram measuring execution duration.
  - *Labels*: `organization_id`, `provider`, `model`, `layer` (e.g. `gateway`, `provider`, `security`).
- `ai_errors_total`: Counter tracking failures.
  - *Labels*: `organization_id`, `provider`, `model`, `error_code`, `layer`.

### Cost and Consumption Metrics
- `ai_cost_usd_total`: Counter summing monetary consumption.
  - *Labels*: `organization_id`, `provider`, `model`.
- `ai_token_usage_total`: Counter summing token usages.
  - *Labels*: `organization_id`, `provider`, `model`, `type` (`prompt` or `completion`).

### Resiliency Metrics
- `ai_failovers_total`: Counter tracking automated model reroutings.
  - *Labels*: `organization_id`, `failed_provider`, `failed_model`, `fallback_provider`, `fallback_model`.
- `ai_retries_total`: Counter tracking endpoint connection retries.
  - *Labels*: `organization_id`, `provider`, `model`.

### Infrastructure and Cache Metrics
- `ai_cache_hits_total` / `ai_cache_misses_total`: Counters tracking semantic cache efficiency.
  - *Labels*: `organization_id`.
- `celery_queue_length`: Gauge tracking message backlog.
  - *Labels*: `queue_name`.
- `celery_active_workers`: Gauge tracking active worker pools.

---

## 4. Multi-Channel Alert Configurations

Alarms dispatched by `AlertEngine` are customized through these integrations:

### 1. Slack Hook
- Dispatches formatted payloads to `SLACK_WEBHOOK_URL` containing the alert type, severity emoji (`⚠️` or `🚨`), error message, and associated organization identifier.

### 2. SMTP Emails
- Connects to `EMAIL_SMTP_HOST` on `EMAIL_SMTP_PORT` to dispatch alerts to `ALERT_EMAIL_RECIPIENT`.
- Sends detailed technical debug details inside structured text bodies.

### 3. Custom HTTP Webhooks
- Can be hooked to trigger automated webhook URLs registered inside organizations to execute auto-mitigation workflows.
