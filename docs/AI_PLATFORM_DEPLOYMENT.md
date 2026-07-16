# Enterprise AI Platform: Observability Deployment Guide

This guide details steps to deploy and manage Viptant's monitoring, tracing, and metric stacks in staging and production.

## 1. Local and Development Deployment

Monitoring is pre-packaged inside the docker-compose stack.

### 1. Enable variables in `.env`
Ensure standard OpenTelemetry exporter and SMTP email variables are active:
```env
OTEL_SERVICE_NAME=viptant-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ALERT_EMAIL_RECIPIENT=alerts@viptant.ai
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_SMTP_HOST=localhost
EMAIL_SMTP_PORT=1025
```

### 2. Boot Docker containers
From the root directory:
```bash
docker compose up -d prometheus grafana otel-collector node-exporter
```
Verify the monitors are active:
- **Prometheus UI**: `http://localhost:9090`
- **Grafana UI**: `http://localhost:3001` (Default credential: admin / admin)

---

## 2. Production Deployment Best Practices

### 1. Prometheus Scrape Configuration
Ensure network firewall rules allow the Prometheus server container to reach your FastAPI application instances on `/api/v1/observability/metrics`. 
Enable Prometheus authentication using Nginx or an API gateway if the `/metrics` endpoint is exposed publicly.

### 2. OpenTelemetry Collector Scaling
- For production, configure the OpenTelemetry Collector using the *Agent-Collector* deployment model:
  - Run the OTel Collector as a sidecar container in your ECS tasks or Kubernetes pods to collect traces locally with minimal network overhead.
  - Configure the collector to export metrics/traces to a central Grafana Tempo, Jaeger, or Datadog backend using standard OTLP protocols.

### 3. Database Log Retention & Bloat Management
Since access logs and execution traces are stored in the Postgres database, execute a scheduled cron cleanup job to delete or archive database records older than 14 days to prevent table bloat:
```sql
DELETE FROM ai_logs WHERE timestamp < NOW() - INTERVAL '14 days';
DELETE FROM ai_traces WHERE start_time < NOW() - INTERVAL '14 days';
```
This is easily scheduled using a Postgres pg_cron task or a Celery background periodic task.
