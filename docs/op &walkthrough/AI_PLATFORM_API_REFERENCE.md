# Enterprise AI Platform: Observability API Reference

This document provides a reference of the REST APIs exposed under `/api/v1/observability`.

---

## 1. System Health Status

Fetches the live status checks for the database, cache, workers, and tracer pipelines.

- **URL**: `/api/v1/observability/health`
- **Method**: `GET`
- **Auth Required**: No (Public)
- **Response Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "success": true,
    "status": "healthy",
    "timestamp": "2026-07-16T12:00:00.000000",
    "components": {
      "database": "healthy",
      "redis": "healthy",
      "workers": "healthy",
      "telemetry": "healthy"
    },
    "details": {
      "database": {
        "status": "healthy",
        "engine": "sqlite"
      },
      "redis": {
        "status": "healthy",
        "connected_clients": 5
      },
      "workers": {
        "status": "healthy",
        "active_queues": ["celery"]
      },
      "telemetry": {
        "status": "healthy",
        "exporter": "otlp"
      }
    }
  }
  ```

---

## 2. Prometheus Metrics

Exposes internal performance registry gauges, cost trackers, and token counters.

- **URL**: `/api/v1/observability/metrics`
- **Method**: `GET`
- **Auth Required**: No (Public)
- **Response Code**: `200 OK`
- **Content-Type**: `text/plain; version=0.0.4`
- **Response Body**:
  ```text
  # HELP ai_requests_total Total number of AI Requests processed.
  # TYPE ai_requests_total counter
  ai_requests_total{model="llama3-8b-8192",organization_id="ad43d317-f490-426d-b19c-eb9cfe1e2653",provider="groq",status="success"} 12.0
  # HELP ai_request_latency_seconds Latency of AI Requests in seconds.
  # TYPE ai_request_latency_seconds histogram
  ai_request_latency_seconds_bucket{le="0.005",model="llama3-8b-8192",organization_id="ad43d317-f490-426d-b19c-eb9cfe1e2653",provider="groq"} 0.0
  ...
  ```

---

## 3. Query Traces List

Queries the execution trace database table with active user filtering.

- **URL**: `/api/v1/observability/traces`
- **Method**: `GET`
- **Auth Required**: Yes (Active Organization Member)
- **Parameters**:
  - `trace_id` (string, optional): Hexadecimal trace filter
  - `name` (string, optional): Operation name pattern match
  - `status` (string, optional): `success` or `error`
  - `limit` (int, default=50)
  - `offset` (int, default=0)
- **Response Body**:
  ```json
  [
    {
      "id": "7c582131-7671-49ef-9473-21fb2f0f49a7",
      "trace_id": "c021a8677463416ba10adac427c4c6a1",
      "span_id": "dac427c4c6a1b1a0",
      "parent_span_id": null,
      "name": "gateway.groq.llama3-8b-8192",
      "start_time": "2026-07-16T11:43:18.000000",
      "end_time": "2026-07-16T11:43:18.175000",
      "duration_ms": 175,
      "status": "success",
      "error_message": null,
      "attributes": {
        "provider": "groq",
        "model": "llama3-8b-8192",
        "prompt_tokens": 12,
        "completion_tokens": 18,
        "cost_usd": 0.0000024
      }
    }
  ]
  ```

---

## 4. Query Structured Logs

Queries structured log records.

- **URL**: `/api/v1/observability/logs`
- **Method**: `GET`
- **Auth Required**: Yes (Active Organization Member)
- **Parameters**:
  - `search` (string, optional): Match logger message terms
  - `level` (string, optional): `INFO`, `WARNING`, `ERROR`
  - `trace_id` (string, optional): Filter by trace UUID
- **Response Body**:
  ```json
  [
    {
      "id": "ad43d317-f490-426d-b19c-eb9cfe1e2653",
      "trace_id": "c021a8677463416ba10adac427c4c6a1",
      "span_id": "dac427c4c6a1b1a0",
      "correlation_id": "test-correlation-1234",
      "request_id": "46f8f36f-badc-454f-9bfb-bde0dce0dcc8",
      "timestamp": "2026-07-16T11:43:18.000000",
      "level": "INFO",
      "logger": "api.ai.gateway.coordinator",
      "message": "AI Request to groq/llama3-8b-8192 resolved with status success",
      "payload": {
        "provider": "groq",
        "model": "llama3-8b-8192",
        "prompt_tokens": 12,
        "completion_tokens": 18,
        "cost_usd": 0.0000024,
        "latency_ms": 175
      }
    }
  ]
  ```

---

## 5. Live Dashboard Snapshot

Fetches real-time request loads, Celery queue depth, and background worker state.

- **URL**: `/api/v1/observability/live`
- **Method**: `GET`
- **Auth Required**: Yes
- **Response Body**:
  ```json
  {
    "timestamp": "2026-07-16T12:00:00.000000",
    "traffic_5m": {
      "requests_count": 12,
      "errors_count": 0,
      "avg_latency_ms": 150.5,
      "throughput_rpm": 2.4
    },
    "redis": {
      "status": "healthy",
      "used_memory": "1.24 MB",
      "connections": 4
    },
    "workers": {
      "active_workers_count": 1,
      "jobs_total": 0,
      "jobs_running": 0
    },
    "queues": {
      "celery": {
        "size": 0
      }
    },
    "active_incidents": []
  }
  ```

---

## 6. Simulated Test Alert Trigger

Simulates an outage incident to verify channels (Slack webhooks, SMTP, console) are correctly routing alarms.

- **URL**: `/api/v1/observability/alerts/test`
- **Method**: `POST`
- **Parameters**:
  - `severity` (string, default="warning"): `warning` or `critical`
- **Response Body**:
  ```json
  {
    "success": true,
    "status": "sent",
    "incident_id": "7c582131-7671-49ef-9473-21fb2f0f49a7",
    "channels": "console,slack,smtp",
    "message": "Test alert notification dispatched successfully."
  }
  ```
