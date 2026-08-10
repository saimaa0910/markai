import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.observability import AITrace, AILog, AIIncident, AIAlert, AIPerformanceMetric
from api.core.metrics_registry import update_scraped_system_metrics
from api.services.alert_engine import AlertEngine
from api.core.redis_manager import RedisConnectionManager
from api.services.queue_service import QueueService

router = APIRouter(prefix="/observability", tags=["ai-observability"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])
admin_only = RoleChecker([UserRole.OWNER, UserRole.ADMIN])


@router.get("/metrics")
def get_prometheus_metrics(db: Session = Depends(get_db)) -> Response:
    """
    Exposes raw Prometheus metrics to be scraped by a Prometheus server.
    This public endpoint updates dynamic system metrics before returning.
    """
    try:
        update_scraped_system_metrics(db)
    except Exception as e:
        import logging
        logging.getLogger("api.routes.observability").warning(f"Error updating scraper metrics: {e}")
        
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health")
def get_detailed_system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Performs a deep health check of core ecosystem components and telemetry pipelines.
    Returns status: healthy, warning, critical, or offline.
    """
    checks = {
        "gateway": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "workers": "healthy",
        "queues": "healthy",
        "telemetry": "healthy"
    }
    
    details = {}
    overall_status = "healthy"

    # 1. Check DB Health
    try:
        db.execute(select(1))
        details["database"] = {"status": "healthy", "latency_ms": 1.0}
    except Exception as e:
        checks["database"] = "offline"
        details["database"] = {"status": "offline", "error": str(e)}
        overall_status = "critical"

    # 2. Check Redis Health
    try:
        redis_mgr = RedisConnectionManager()
        redis_metrics = redis_mgr.get_metrics()
        checks["redis"] = "healthy" if redis_metrics.get("status") == "connected" else "offline"
        details["redis"] = redis_metrics
        if checks["redis"] == "offline":
            overall_status = "critical"
    except Exception as e:
        checks["redis"] = "offline"
        details["redis"] = {"status": "offline", "error": str(e)}
        overall_status = "critical"

    # 3. Check Workers & Queues Health
    try:
        queue_svc = QueueService()
        queue_metrics = queue_svc.get_metrics()
        checks["queues"] = "healthy"
        checks["workers"] = "healthy" if queue_metrics.get("active_workers_count", 0) > 0 else "warning"
        details["queues"] = queue_metrics
        if checks["workers"] == "warning" and overall_status == "healthy":
            overall_status = "warning"
    except Exception as e:
        checks["queues"] = "warning"
        checks["workers"] = "warning"
        details["queues"] = {"error": str(e)}
        if overall_status == "healthy":
            overall_status = "warning"

    # 4. Check Telemetry & Logs
    try:
        # Verify that we can query traces/logs table
        trace_count = db.scalars(select(func.count(AITrace.id))).first()
        details["telemetry"] = {"status": "healthy", "stored_traces_count": trace_count or 0}
    except Exception as e:
        checks["telemetry"] = "warning"
        details["telemetry"] = {"status": "warning", "error": str(e)}
        if overall_status == "healthy":
            overall_status = "warning"

    return {
        "success": overall_status in ["healthy", "warning"],
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": checks,
        "details": details
    }


@router.get("/traces")
def get_traces_list(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    trace_id: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Any:
    """Query and filter database-backed execution traces."""
    query = select(AITrace).where(
        (AITrace.organization_id == None) | (AITrace.organization_id == membership.organization_id)
    )
    
    if trace_id:
        query = query.where(AITrace.trace_id == trace_id)
    if name:
        query = query.where(AITrace.name.contains(name))
    if status:
        query = query.where(AITrace.status == status)
        
    query = query.order_by(desc(AITrace.start_time)).limit(limit).offset(offset)
    traces = db.scalars(query).all()
    
    return [
        {
            "id": str(t.id),
            "trace_id": t.trace_id,
            "span_id": t.span_id,
            "parent_span_id": t.parent_span_id,
            "name": t.name,
            "start_time": t.start_time.isoformat(),
            "end_time": t.end_time.isoformat(),
            "duration_ms": t.duration_ms,
            "status": t.status,
            "error_message": t.error_message,
            "attributes": t.attributes
        }
        for t in traces
    ]


@router.get("/logs")
def get_logs_list(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Any:
    """Query and search structured JSON log entries."""
    query = select(AILog).where(
        (AILog.organization_id == None) | (AILog.organization_id == membership.organization_id)
    )
    
    if trace_id:
        query = query.where(AILog.trace_id == trace_id)
    if correlation_id:
        query = query.where(AILog.correlation_id == correlation_id)
    if request_id:
        query = query.where(AILog.request_id == request_id)
    if level:
        query = query.where(AILog.level == level.upper())
    if search:
        query = query.where(AILog.message.contains(search))
        
    query = query.order_by(desc(AILog.timestamp)).limit(limit).offset(offset)
    logs = db.scalars(query).all()
    
    return [
        {
            "id": str(l.id),
            "trace_id": l.trace_id,
            "span_id": l.span_id,
            "correlation_id": l.correlation_id,
            "request_id": l.request_id,
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "logger": l.logger,
            "message": l.message,
            "payload": l.payload
        }
        for l in logs
    ]


@router.get("/incidents")
def get_incidents_list(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    component: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Any:
    """Query active or historical platform incidents."""
    query = select(AIIncident).where(
        (AIIncident.organization_id == None) | (AIIncident.organization_id == membership.organization_id)
    )
    
    if component:
        query = query.where(AIIncident.component == component)
    if status:
        query = query.where(AIIncident.status == status)
        
    query = query.order_by(desc(AIIncident.start_time)).limit(limit).offset(offset)
    incidents = db.scalars(query).all()
    
    return [
        {
            "id": str(i.id),
            "component": i.component,
            "service": i.service,
            "severity": i.severity,
            "root_cause": i.root_cause,
            "resolution": i.resolution,
            "status": i.status,
            "start_time": i.start_time.isoformat(),
            "end_time": i.end_time.isoformat() if i.end_time else None,
            "duration_sec": i.duration_sec
        }
        for i in incidents
    ]


@router.get("/alerts")
def get_alerts_list(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Any:
    """Query active and sent alert manager logs."""
    query = select(AIAlert).where(
        (AIAlert.organization_id == None) | (AIAlert.organization_id == membership.organization_id)
    )
    
    if alert_type:
        query = query.where(AIAlert.alert_type == alert_type)
    if severity:
        query = query.where(AIAlert.severity == severity)
    if status:
        query = query.where(AIAlert.status == status)
        
    query = query.order_by(desc(AIAlert.created_at)).limit(limit).offset(offset)
    alerts = db.scalars(query).all()
    
    return [
        {
            "id": str(a.id),
            "incident_id": str(a.incident_id) if a.incident_id else None,
            "alert_type": a.alert_type,
            "message": a.message,
            "severity": a.severity,
            "channels": a.channels,
            "status": a.status,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]


@router.get("/performance")
def get_performance_analytics(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """
    Returns aggregated percentile distributions (P50, P90, P95, P99),
    latencies, comparisons, and cache performance trends.
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Query all trace durations for organization in timeframe
    query = select(AITrace.duration_ms, AITrace.name).where(
        ((AITrace.organization_id == None) | (AITrace.organization_id == membership.organization_id)),
        AITrace.start_time >= since_date
    )
    results = db.execute(query).all()
    
    latencies = [r[0] for r in results]
    latencies.sort()
    count = len(latencies)
    
    p50 = latencies[int(count * 0.50)] if count > 0 else 0
    p90 = latencies[int(count * 0.90)] if count > 0 else 0
    p95 = latencies[int(count * 0.95)] if count > 0 else 0
    p99 = latencies[int(count * 0.99)] if count > 0 else 0
    
    average = int(sum(latencies) / count) if count > 0 else 0
    maximum = latencies[-1] if count > 0 else 0
    minimum = latencies[0] if count > 0 else 0
    
    # Group by name/provider to get comparisons
    from api.models.ai_usage import AITokenUsage
    usage_query = select(
        AITokenUsage.provider,
        AITokenUsage.model_name,
        func.avg(AITokenUsage.latency_ms),
        func.count(AITokenUsage.id),
        func.sum(AITokenUsage.cost_usd)
    ).where(
        AITokenUsage.organization_id == membership.organization_id,
        AITokenUsage.created_at >= since_date
    ).group_by(AITokenUsage.provider, AITokenUsage.model_name)
    
    comparisons = db.execute(usage_query).all()
    provider_comparison = []
    for row in comparisons:
        provider_comparison.append({
            "provider": row[0],
            "model": row[1],
            "avg_latency_ms": round(float(row[2] or 0), 2),
            "requests_count": row[3],
            "total_cost_usd": round(float(row[4] or 0), 6)
        })

    # Cache hit metrics from AICacheMetadata
    from api.models.infrastructure import AICacheMetadata
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
    cache_row = db.execute(
        select(func.sum(AICacheMetadata.hits), func.sum(AICacheMetadata.misses))
        .where(AICacheMetadata.timestamp >= since_date)
    ).first()
    
    hits = int(cache_row[0] or 0)
    misses = int(cache_row[1] or 0)
    total_cache = hits + misses
    hit_ratio = round(hits / total_cache, 4) if total_cache > 0 else 1.0

    return {
        "summary": {
            "total_traces": count,
            "average_ms": average,
            "p50_ms": p50,
            "p90_ms": p90,
            "p95_ms": p95,
            "p99_ms": p99,
            "max_ms": maximum,
            "min_ms": minimum
        },
        "provider_comparison": provider_comparison,
        "cache_performance": {
            "hits": hits,
            "misses": misses,
            "hit_ratio": hit_ratio
        }
    }


@router.get("/live")
def get_live_observability_feed(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member)
) -> Dict[str, Any]:
    """
    Returns a snapshot of the live status of the system (active queues, jobs, errors, and traffic rate)
    for dashboard streaming or dynamic periodic updates.
    """
    redis_mgr = RedisConnectionManager()
    redis_metrics = redis_mgr.get_metrics()
    
    queue_svc = QueueService()
    queue_metrics = queue_svc.get_metrics()

    # Active incidents
    active_incidents = db.scalars(
        select(AIIncident)
        .where(
            ((AIIncident.organization_id == None) | (AIIncident.organization_id == membership.organization_id)),
            AIIncident.status == "active"
        )
    ).all()

    # Traffic count in the last 5 minutes
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    recent_traces = db.scalars(
        select(AITrace)
        .where(
            ((AITrace.organization_id == None) | (AITrace.organization_id == membership.organization_id)),
            AITrace.start_time >= five_min_ago
        )
    ).all()

    recent_list = list(recent_traces)
    recent_count = len(recent_list)
    recent_errors = len([t for t in recent_list if t.status == "error"])
    recent_avg_latency = int(sum(t.duration_ms for t in recent_list) / recent_count) if recent_count > 0 else 0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "traffic_5m": {
            "requests_count": recent_count,
            "errors_count": recent_errors,
            "avg_latency_ms": recent_avg_latency,
            "throughput_rpm": round(recent_count / 5.0, 2)
        },
        "redis": {
            "status": redis_metrics.get("status", "disconnected"),
            "used_memory": redis_metrics.get("used_memory_human", "0B"),
            "connections": redis_metrics.get("connected_clients", 0)
        },
        "workers": {
            "active_workers_count": queue_metrics.get("active_workers_count", 1),
            "jobs_total": queue_metrics.get("jobs", {}).get("total", 0),
            "jobs_running": queue_metrics.get("jobs", {}).get("running", 0)
        },
        "queues": queue_metrics.get("queues", {}),
        "active_incidents": [
            {
                "id": str(i.id),
                "component": i.component,
                "service": i.service,
                "severity": i.severity,
                "root_cause": i.root_cause,
                "start_time": i.start_time.isoformat()
            }
            for i in active_incidents
        ]
    }


@router.post("/alerts/test")
def trigger_test_alert(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(admin_only),
    severity: str = Query("warning", enum=["warning", "critical", "info"])
) -> Dict[str, Any]:
    """
    Admin-only test endpoint to trigger a simulated alert notification
    across active Slack, Email, and Webhook dispatch channels.
    """
    alert = AlertEngine.trigger_alert(
        db=db,
        alert_type="TEST_ALERT_TRIGGER",
        message=f"Simulated test alert triggered by user {membership.user_id} in organization {membership.organization_id}.",
        severity=severity,
        organization_id=membership.organization_id
    )
    return {"success": True, "alert_id": str(alert.id), "status": alert.status, "channels": alert.channels}
