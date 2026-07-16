import logging
from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa
from pydantic import BaseModel

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])
from api.core.redis_manager import RedisConnectionManager
from api.services.cache_service import CacheService
from api.services.queue_service import QueueService
from api.models.infrastructure import AIBackgroundJob, AIWorkerMetric

logger = logging.getLogger("api.routes.infrastructure")
router = APIRouter(prefix="/ai/infrastructure", tags=["ai-infrastructure"])

class CacheClearRequest(BaseModel):
    namespace: Optional[str] = None
    org_id: Optional[str] = None

class JobRunRequest(BaseModel):
    task_name: str
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None

@router.get("/health")
def get_infra_health(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    redis_mgr = RedisConnectionManager()
    redis_metrics = redis_mgr.get_metrics()
    
    db_ok = False
    try:
        db.execute(sa.text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
        
    return {
        "database": "healthy" if db_ok else "unhealthy",
        "redis": redis_metrics.get("status", "disconnected"),
        "latency_ms": redis_metrics.get("latency_ms", 0.0),
        "status": "healthy" if (db_ok and redis_metrics.get("status") == "connected") else "degraded",
    }

@router.get("/redis")
def get_redis_metrics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    redis_mgr = RedisConnectionManager()
    return redis_mgr.get_metrics()

@router.post("/redis/reconnect")
def reconnect_redis(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    redis_mgr = RedisConnectionManager()
    redis_mgr.disconnect()
    redis_mgr.connect()
    return {"success": True, "message": "Successfully reinitialized Redis connection pool."}

@router.get("/cache")
def get_cache_metrics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    cache_svc = CacheService()
    return cache_svc.get_metrics()

@router.post("/cache/clear")
def clear_cache_route(
    req: CacheClearRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    cache_svc = CacheService()
    
    if req.namespace:
        cleared_count = cache_svc.clear_namespace(req.namespace, req.org_id)
        msg = f"Cleared namespace '{req.namespace}'"
    elif req.org_id:
        cleared_count = cache_svc.clear_org(req.org_id)
        msg = f"Cleared org '{req.org_id}'"
    else:
        cleared_count = cache_svc.clear_all()
        msg = "Cleared entire AI Cache"
        
    return {"success": True, "message": msg, "cleared_count": cleared_count}

@router.get("/workers")
def get_workers_status(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    jobs_count = db.query(AIBackgroundJob).count()
    active_jobs = db.query(AIBackgroundJob).filter_by(status="STARTED").count()
    failed_jobs = db.query(AIBackgroundJob).filter_by(status="FAILURE").count()
    completed_jobs = db.query(AIBackgroundJob).filter_by(status="SUCCESS").count()
    
    recent_metrics = db.query(AIWorkerMetric).order_by(AIWorkerMetric.timestamp.desc()).limit(10).all()
    
    return {
        "jobs": {
            "total": jobs_count,
            "running": active_jobs,
            "failed": failed_jobs,
            "completed": completed_jobs,
        },
        "worker_metrics": recent_metrics,
        "active_nodes_count": 1,
    }

@router.get("/jobs")
def get_jobs_list(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    jobs = db.query(AIBackgroundJob).order_by(AIBackgroundJob.created_at.desc()).limit(50).all()
    return jobs

@router.post("/jobs/run")
def trigger_job(
    req: JobRunRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    from api.worker.celery_app import celery_app
    
    args = req.args or []
    kwargs = req.kwargs or {}
    
    try:
        res = celery_app.send_task(req.task_name, args=args, kwargs=kwargs)
        
        job = AIBackgroundJob(
            task_id=res.id,
            name=req.task_name,
            status="PENDING",
            args=str(args),
            kwargs=str(kwargs)
        )
        db.add(job)
        db.commit()
        
        return {"success": True, "task_id": res.id, "status": "PENDING"}
    except Exception as e:
        logger.error(f"Failed to manually run task {req.task_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Task trigger failed: {str(e)}")

@router.get("/queues")
def get_queues_metrics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    queue_svc = QueueService()
    return queue_svc.get_metrics()
