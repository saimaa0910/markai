# Background Task Processing & Celery Architecture

## Overview

**MarkAI** uses **Celery 5.x** backed by **Redis 7.x** as its distributed task queue and result backend ([celery_app.py](file:///d:/markai/apps/api/src/api/worker/celery_app.py)). All asynchronous task executions are logged to database audit tables (`AIBackgroundJob` and `AIJobHistory`) and traced via OpenTelemetry spans.

---

## Celery Worker Topology

```mermaid
graph TD
    API[FastAPI Gateway / API Endpoints] -->|Enqueue Task .delay()| Redis Broker[(Redis Queue Broker)]
    
    subgraph Celery Distributed Cluster
        Redis Broker --> Worker1[Celery Worker - Agent Tasks]
        Redis Broker --> Worker2[Celery Worker - RAG Ingestion]
        Redis Broker --> Worker3[Celery Worker - Notifications]
        
        Beat[Celery Beat Scheduler] -->|Cron Schedules| Redis Broker
    end

    Worker1 -->|Track Execution| DB[(PostgreSQL Database)]
    Worker2 -->|Write Chunks / Embeddings| DB
    Worker3 -->|Send Emails / In-App Alerts| Smtp[SMTP / Email Gateway]

    Worker1 -->|Record Incident on Failure| AlertEngine[Alert Engine\nservices/alert_engine.py]
```

---

## Task Execution & Telemetry Tracking

Every background task uses the `track_task_execution` context manager helper ([celery_app.py#L35-L114](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L35-L114)):

1. **Database Audit Logging**: Creates or updates an `AIBackgroundJob` record with `task_id`, `status` (`STARTED`, `SUCCESS`, `FAILURE`), `started_at`, `completed_at`, `runtime`, and `error` text.
2. **OpenTelemetry Integration**: Starts a child span `celery.task.<task_name>` tagged with `celery.task_id`, tracking precise background execution duration and status.
3. **Incident Reporting**: Automatically triggers `AlertEngine.report_incident()` with `critical` severity if core tasks fail (e.g. `agent_run_task` or `notification_task`).

---

## Celery Task Catalog

### 1. Application Background Tasks

- **`worker.tasks.agent_run_task`**: Executes an autonomous AI Agent session asynchronously.
  - Inputs: `session_id_str`, `user_input`
  - Internal Service: `AgentExecutorService.run_agent_session()`
- **`worker.tasks.process_document_pipeline_task`**: Executes asynchronous document parsing, chunking, vector embedding, and index storage into the Knowledge Base.
  - Inputs: `document_id_str`, `file_path`, `organization_id_str`, `user_id_str`, `chunk_size`, `strategy`, `embedding_model`
  - Internal Service: `DocumentProcessingService.run_ingestion_pipeline()`
- **`worker.tasks.notification_task`**: Dispatches email and in-app notifications.
  - Inputs: `user_id_str`, `org_id_str`, `title`, `body`, `channel_str`, `event_type`
  - Internal Service: `NotificationService.send_notification()`
- **`worker.tasks.campaign_broadcast_task`**: Triggers marketing email campaign blasts across organization contact lists.
  - Inputs: `campaign_id_str`

### 2. Scheduled Cron Jobs (Celery Beat)

| Schedule | Task Name | Purpose | Source File |
| :--- | :--- | :--- | :--- |
| **Every Minute** | `worker.tasks.health_worker_task` | Health checks & latency pings to AI Providers | [celery_app.py#L361](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L361) |
| **Daily (Midnight)** | `worker.tasks.model_sync_worker_task` | Sync active providers & model registry entries | [celery_app.py#L365](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L365) |
| **Daily (Midnight)** | `worker.tasks.quota_reset_worker_task` | Reset daily organization token/spend usage counters | [celery_app.py#L381](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L381) |
| **Hourly** | `worker.tasks.cleanup_worker_task` | Purge expired Redis playground cache entries | [celery_app.py#L369](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L369) |
| **Hourly** | `worker.tasks.usage_worker_task` | Aggregate token usage & cost stats | [celery_app.py#L373](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L373) |
| **Daily (1:00 AM)** | `worker.tasks.cost_worker_task` | Verify organization billing credit limits | [celery_app.py#L377](file:///d:/markai/apps/api/src/api/worker/celery_app.py#L377) |
