import logging
import time
from typing import Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from sqlalchemy.orm import Session
from sqlalchemy import select, func

logger = logging.getLogger("api.core.metrics_registry")

# Create a custom registry to avoid pollution of the default registry if needed,
# but using the standard default registry or sharing is common. Let's use the default registry.
# We will define our metrics globally.

# API Gateway & Request Metrics
ai_requests_total = Counter(
    "ai_requests_total",
    "Total number of AI requests processed by the platform",
    ["organization_id", "provider", "model", "status"]
)

ai_request_latency_seconds = Histogram(
    "ai_request_latency_seconds",
    "Latencies of requests through the AI platform in seconds",
    ["organization_id", "provider", "model", "layer"],  # layer: gateway, provider, streaming
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

ai_retries_total = Counter(
    "ai_retries_total",
    "Total number of request retry attempts",
    ["organization_id", "provider", "model"]
)

ai_failovers_total = Counter(
    "ai_failovers_total",
    "Total number of model/provider failover occurrences",
    ["organization_id", "failed_provider", "failed_model", "fallback_provider", "fallback_model"]
)

ai_errors_total = Counter(
    "ai_errors_total",
    "Total number of failed requests",
    ["organization_id", "provider", "model", "error_code", "layer"]  # layer: gateway, provider, streaming
)

# Token & Cost Metrics
ai_token_usage_total = Counter(
    "ai_token_usage_total",
    "Total tokens consumed",
    ["organization_id", "provider", "model", "type"]  # metric type: prompt, completion
)

ai_cost_usd_total = Counter(
    "ai_cost_usd_total",
    "Total estimated cost of AI request completions in USD",
    ["organization_id", "provider", "model"]
)

# Cache Metrics
ai_cache_operations_total = Counter(
    "ai_cache_operations_total",
    "Total number of cache hits or misses",
    ["namespace", "result"]  # result: hit, miss
)

# Feature Activity Metrics
ai_conversations_total = Counter(
    "ai_conversations_total",
    "Total number of conversation chat threads created",
    ["organization_id"]
)

ai_agent_runs_total = Counter(
    "ai_agent_runs_total",
    "Total number of AI agent run executions",
    ["organization_id", "agent_name", "status"]
)

ai_workflow_runs_total = Counter(
    "ai_workflow_runs_total",
    "Total number of workflow step run executions",
    ["organization_id", "workflow_name", "status"]
)

ai_knowledge_queries_total = Counter(
    "ai_knowledge_queries_total",
    "Total number of knowledge searches performed",
    ["organization_id"]
)

ai_prompt_executions_total = Counter(
    "ai_prompt_executions_total",
    "Total number of prompt template executions",
    ["organization_id", "prompt_name"]
)

# Infrastructure Gauges (Scraped dynamically)
ai_redis_memory_bytes = Gauge(
    "ai_redis_memory_bytes",
    "Current memory usage of the Redis server in bytes"
)

ai_redis_connections = Gauge(
    "ai_redis_connections",
    "Current active connections to Redis"
)

ai_queue_length = Gauge(
    "ai_queue_length",
    "Current number of pending tasks in Celery queue",
    ["queue_name"]
)

ai_worker_count = Gauge(
    "ai_worker_count",
    "Current active worker process count"
)

ai_scheduler_jobs = Gauge(
    "ai_scheduler_jobs",
    "Current count of scheduled beat tasks"
)

ai_active_conversations = Gauge(
    "ai_active_conversations",
    "Current count of open active conversations in database",
    ["organization_id"]
)


def update_scraped_system_metrics(db: Session) -> None:
    """
    Query Redis, Celery services, and DB, then update Prometheus gauge metrics.
    Called dynamically just prior to metrics collection scraper response.
    """
    # 1. Update Redis Metrics
    try:
        from api.core.redis_manager import RedisConnectionManager
        redis_mgr = RedisConnectionManager()
        client = redis_mgr.get_client()
        info = client.info()
        
        ai_redis_memory_bytes.set(float(info.get("used_memory", 0)))
        ai_redis_connections.set(float(info.get("connected_clients", 0)))
    except Exception as e:
        logger.warning(f"Failed to collect Redis scraper metrics: {e}")

    # 2. Update Queue & Worker Metrics
    try:
        from api.services.queue_service import QueueService
        queue_svc = QueueService()
        metrics = queue_svc.get_metrics()
        
        # Celery queue metrics
        queues = metrics.get("queues", {})
        for q_name, q_info in queues.items():
            ai_queue_length.labels(queue_name=q_name).set(float(q_info.get("size", 0)))
            
        ai_worker_count.set(float(metrics.get("active_workers_count", 1)))
    except Exception as e:
        logger.warning(f"Failed to collect Queue scraper metrics: {e}")

    # 3. Update Database Gauges (e.g. Active Conversations)
    try:
        from api.models.conversation import Conversation
        
        # Find count of active conversations grouped by organization
        results = db.execute(
            select(Conversation.organization_id, func.count(Conversation.id))
            .group_by(Conversation.organization_id)
        ).all()
        
        for org_id, count in results:
            org_str = str(org_id) if org_id else "system"
            ai_active_conversations.labels(organization_id=org_str).set(float(count))
    except Exception as e:
        logger.warning(f"Failed to collect DB scraper metrics: {e}")
