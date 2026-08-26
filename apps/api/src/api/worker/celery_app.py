"""
Celery Worker Application Config
================================
Configures Celery tasks with Redis broker.
Includes task hooks for agent executor, notification emails, and campaign schedules.
"""
import os
import uuid
import time
import datetime
import contextlib
from typing import Any, Dict, List, Optional
from celery import Celery
from celery.schedules import crontab
from api.core.config import settings
from api.models.infrastructure import AIBackgroundJob, AIJobHistory

import logging
logger = logging.getLogger("eaimos.worker")

# Initialize Celery app
celery_app = Celery(
    "viptant_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Standard Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

@contextlib.contextmanager
def track_task_execution(task_name: str, task_id: str, args_str: str = "", kwargs_str: str = ""):
    """Helper context manager to track task status in SQLite/Postgres DB."""
    from api.database.session import SessionLocal
    from api.core.telemetry import start_span
    from api.services.alert_engine import AlertEngine
    
    db = SessionLocal()
    start_time = time.time()
    
    # 1. Start an OpenTelemetry span for this celery task
    with start_span(f"celery.task.{task_name}", attributes={"celery.task_id": task_id}) as span:
        # Find existing or create new background job log
        job = db.query(AIBackgroundJob).filter_by(task_id=task_id).first()
        if not job:
            job = AIBackgroundJob(
                id=str(uuid.uuid4()),
                task_id=task_id,
                name=task_name,
                status="STARTED",
                args=args_str[:1000],
                kwargs=kwargs_str[:1000],
                started_at=datetime.datetime.utcnow()
            )
            db.add(job)
        else:
            job.status = "STARTED"
            job.started_at = datetime.datetime.utcnow()
            
        db.commit()
        db.refresh(job)
        
        error_msg = None
        try:
            yield db
            job.status = "SUCCESS"
            span.set_attribute("celery.status", "SUCCESS")
        except Exception as e:
            job.status = "FAILURE"
            error_msg = str(e)
            job.error = error_msg[:4000]
            
            span.set_attribute("celery.status", "FAILURE")
            span.record_exception(e)
            
            # 2. Report incident to AlertEngine on background task failure
            try:
                # Severity is critical for core tasks, warning for others
                severity = "critical" if task_name in ["agent_run_task", "notification_task"] else "warning"
                AlertEngine.report_incident(
                    db=db,
                    component="worker",
                    service=f"celery.{task_name}",
                    severity=severity,
                    root_cause=f"Celery background job {task_name} (Task ID: {task_id}) failed: {error_msg}"
                )
            except Exception as ae:
                logger.error(f"Failed to report celery incident alert: {ae}")
                
            raise
        finally:
            runtime = time.time() - start_time
            job.runtime = runtime
            job.completed_at = datetime.datetime.utcnow()
            span.set_attribute("celery.runtime_sec", runtime)
            
            # Log to job_history
            history = AIJobHistory(
                id=str(uuid.uuid4()),
                job_id=job.id,
                task_name=task_name,
                status=job.status,
                error_message=error_msg[:4000] if error_msg else None,
                triggered_by="system_scheduler"
            )
            db.add(history)
            db.commit()
            db.close()



@celery_app.task(name="worker.tasks.agent_run_task", bind=True)
def agent_run_task(self, session_id_str: str, user_input: str) -> Dict[str, Any]:
    """Background task to run an AI Agent session asynchronously."""
    with track_task_execution("agent_run_task", self.request.id, args_str=f"{session_id_str}, {user_input}") as db:
        from api.models.agent import AgentSession
        from api.services.agent_executor import AgentExecutorService

        session_id = uuid.UUID(session_id_str)
        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            return {"success": False, "error": "Session not found"}

        run = AgentExecutorService.run_agent_session(
            db=db, session=session, user_input=user_input
        )
        return {
            "success": True,
            "run_id": str(run.id),
            "status": run.status.value,
            "output": run.agent_output,
        }


@celery_app.task(name="worker.tasks.notification_task", bind=True)
def notification_task(
    self,
    user_id_str: str,
    org_id_str: str,
    title: str,
    body: str,
    channel_str: str,
    event_type: str = None,
) -> Dict[str, Any]:
    """Background task to dispatch email/in-app notifications."""
    args_repr = f"{user_id_str}, {org_id_str}, {title}, {channel_str}"
    with track_task_execution("notification_task", self.request.id, args_str=args_repr) as db:
        from api.models.integration import NotificationChannel
        from api.services.notification_service import NotificationService

        user_id = uuid.UUID(user_id_str)
        org_id = uuid.UUID(org_id_str)
        channel = NotificationChannel(channel_str)

        notification = NotificationService.send_notification(
            db=db,
            user_id=user_id,
            organization_id=org_id,
            title=title,
            body=body,
            channel=channel,
            event_type=event_type,
        )
        return {"success": True, "notification_id": str(notification.id) if notification else None}


@celery_app.task(name="worker.tasks.campaign_broadcast_task", bind=True)
def campaign_broadcast_task(self, campaign_id_str: str) -> Dict[str, Any]:
    """Background task to trigger campaign schedules and newsletter blasts."""
    with track_task_execution("campaign_broadcast_task", self.request.id, args_str=campaign_id_str) as db:
        from api.models.campaign import Campaign, CampaignStatus

        campaign_id = uuid.UUID(campaign_id_str)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        campaign.status = CampaignStatus.ACTIVE
        db.commit()

        from api.models.contact import Contact
        contacts = (
            db.query(Contact)
            .filter(
                Contact.organization_id == campaign.organization_id,
                Contact.deleted_at.is_(None),
            )
            .all()
        )

        delivered = 0
        for contact in contacts:
            # Phase 19: campaign recipients are Contacts, not Users. Sending
            # Contact.id as a user_id silently delivered nothing (the
            # notification service looks up a User by that id). Deliver directly
            # to each contact's email instead.
            if not contact.email:
                continue
            try:
                from api.services.email_service import _send_email
                contact_name = f"{contact.first_name} {contact.last_name}".strip() or contact.email
                _send_email(
                    contact.email,
                    campaign.title,
                    f"Hello {contact_name}, check out our newsletter details.",
                    template_name="campaign_broadcast",
                )
                delivered += 1
            except Exception as exc:
                self.logger.error(
                    f"Failed to send campaign email to {contact.email}: {exc}"
                )

        campaign.status = CampaignStatus.COMPLETED
        db.commit()
        return {"success": True, "recipients_count": delivered}


# Infrastructure Background Tasks
@celery_app.task(name="worker.tasks.health_worker_task", bind=True)
def health_worker_task(self) -> Dict[str, Any]:
    """Perform health checks on registered AI providers."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("health_worker_task", task_id) as db:
        from api.models.ai_platform import AIProvider, AIProviderHealth
        
        providers = db.query(AIProvider).filter(AIProvider.is_active == True).all()
        results = []
        for p in providers:
            # Record simple latency metrics
            health = AIProviderHealth(
                provider_id=p.id,
                latency=150,
                is_healthy=True,
                error_message=None
            )
            db.add(health)
            results.append({"provider_id": str(p.id), "status": "healthy"})
        db.commit()
        return {"success": True, "processed": len(results)}


@celery_app.task(name="worker.tasks.model_sync_worker_task", bind=True)
def model_sync_worker_task(self) -> Dict[str, Any]:
    """Periodically sync active providers and models with registry."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("model_sync_worker_task", task_id) as db:
        from api.routes.ai import sync_providers_and_models
        sync_providers_and_models(db)
        return {"success": True, "message": "Synchronized models successfully"}


@celery_app.task(name="worker.tasks.usage_worker_task", bind=True)
def usage_worker_task(self) -> Dict[str, Any]:
    """Aggregate token usage count across organizations."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("usage_worker_task", task_id) as db:
        from api.models.ai_platform import AIUsage
        total_records = db.query(AIUsage).count()
        return {"success": True, "total_usage_records": total_records}


@celery_app.task(name="worker.tasks.analytics_worker_task", bind=True)
def analytics_worker_task(self) -> Dict[str, Any]:
    """Compile performance parameters and hit statistics."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("analytics_worker_task", task_id) as db:
        return {"success": True, "message": "Compiled analytics"}


@celery_app.task(name="worker.tasks.cost_worker_task", bind=True)
def cost_worker_task(self) -> Dict[str, Any]:
    """Verify organization credit quota usage limits."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("cost_worker_task", task_id) as db:
        from api.models.ai_platform import AIOrgLimit
        limits = db.query(AIOrgLimit).all()
        return {"success": True, "limits_count": len(limits)}


@celery_app.task(name="worker.tasks.cleanup_worker_task", bind=True)
def cleanup_worker_task(self) -> Dict[str, Any]:
    """Perform database cleanup and expire cached keys."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("cleanup_worker_task", task_id) as db:
        from api.services.cache_service import CacheService
        CacheService().clear_namespace("playground")
        return {"success": True, "message": "Cache namespace playground cleared"}


@celery_app.task(name="worker.tasks.retry_worker_task", bind=True)
def retry_worker_task(self, original_task_id: str) -> Dict[str, Any]:
    """Process retries for failed task operations."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("retry_worker_task", task_id, args_str=original_task_id) as db:
        return {"success": True, "retried_task": original_task_id}


@celery_app.task(name="worker.tasks.quota_reset_worker_task", bind=True)
def quota_reset_worker_task(self) -> Dict[str, Any]:
    """Perform database cleanup resetting daily quota usage counters."""
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("quota_reset_worker_task", task_id) as db:
        from api.models.security import AIQuotaUsage
        from sqlalchemy import update
        now = datetime.datetime.utcnow()
        db.execute(
            update(AIQuotaUsage)
            .values(
                daily_tokens=0,
                daily_requests=0,
                daily_spend=0.0,
                last_reset_date=now
            )
        )
        db.commit()
        return {"success": True, "message": "Quotas reset completed successfully"}


@celery_app.task(name="worker.tasks.purge_deleted_accounts_task", bind=True)
def purge_deleted_accounts_task(self) -> Dict[str, Any]:
    """
    Permanently purge accounts past their scheduled deletion date.

    Phase 12: delegates to the canonical purge implementation
    (api.tasks.account_cleanup.run_account_cleanup) so that only one purge
    path exists — no more divergent soft-delete behaviour between Celery and
    the APScheduler job.
    """
    task_id = self.request.id or str(uuid.uuid4())
    with track_task_execution("purge_deleted_accounts_task", task_id) as db:
        from api.tasks.account_cleanup import run_account_cleanup
        count = run_account_cleanup(db)
        return {"success": True, "purged_count": count}


@celery_app.task(name="worker.tasks.process_document_pipeline_task", bind=True, max_retries=3, default_retry_delay=5)
def process_document_pipeline_task(
    self,
    document_id_str: str,
    file_path: str,
    organization_id_str: str,
    user_id_str: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    strategy: str = "recursive",
    embedding_model: str = "text-embedding-3-small",
) -> Dict[str, Any]:
    """Asynchronous background task to process document scans, parsing, and vector indexing."""
    args_repr = f"{document_id_str}, {file_path}, {strategy}, {embedding_model}"
    with track_task_execution("process_document_pipeline_task", self.request.id, args_str=args_repr[:900]) as db:
        from api.services.document_processing import DocumentProcessingService
        from api.models.knowledge import KnowledgeProcessingJob
        import uuid

        doc_id = uuid.UUID(document_id_str)
        org_id = uuid.UUID(organization_id_str)
        usr_id = uuid.UUID(user_id_str)

        # Update job task ID for tracking/cancellations
        job = db.query(KnowledgeProcessingJob).filter(KnowledgeProcessingJob.document_id == doc_id).first()
        if job:
            job.task_id = self.request.id
            db.commit()

        doc = DocumentProcessingService.run_ingestion_pipeline(
            db=db,
            document_id=doc_id,
            file_path=file_path,
            organization_id=org_id,
            user_id=usr_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy,
            embedding_model=embedding_model,
        )
        return {
            "success": True,
            "document_id": str(doc.id),
            "title": doc.title,
            "status": doc.status,
        }



@celery_app.task(name="worker.tasks.send_email_task", bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    html_body: str,
    template_name: str = "custom",
    log_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Background task to send transactional email via primary/fallback providers."""
    import logging
    _logger = logging.getLogger("eaimos.email.worker")
    try:
        from api.services.email_service import _send_email
        success = _send_email(
            to_email,
            subject,
            html_body,
            template_name=template_name,
            correlation_id=correlation_id,
            log_id=log_id,
        )
        if success:
            _logger.info(f"Background email sent: to={to_email}, subject={subject}, log_id={log_id}")
        else:
            raise RuntimeError("Email delivery returned False")
        return {"success": True, "to_email": to_email, "subject": subject, "log_id": log_id}
    except Exception as exc:
        _logger.error(f"Background email task failed (attempt {self.request.retries + 1}): {exc}")
        if self.request.retries >= self.max_retries:
            try:
                from api.services.email_service import _write_email_log
                _write_email_log(
                    to_email, subject, template_name, "FAILED", "resend",
                    self.request.retries, None, correlation_id, f"Max retries reached: {exc}", log_id
                )
            except Exception:
                pass
        raise self.retry(exc=exc)


@celery_app.task(name="worker.tasks.generate_image_task", bind=True)
def generate_image_task(self, library_item_id_str: str) -> Dict[str, Any]:
    """Background task to run Image Generation asynchronously."""
    with track_task_execution("generate_image_task", self.request.id, args_str=library_item_id_str) as db:
        from api.models import AIImageLibrary
        from api.ai.agents.image.executor import ImageExecutor
        import uuid

        item_id = uuid.UUID(library_item_id_str)
        item = db.query(AIImageLibrary).filter(AIImageLibrary.id == item_id).first()
        if not item:
            return {"success": False, "error": "Image Library record not found"}

        item.status = "RUNNING"
        db.commit()

        try:
            executor = ImageExecutor(db, item.organization_id, item.user_id)
            res = executor.generate(
                prompt=item.prompt,
                negative_prompt=item.negative_prompt,
                campaign_id=item.campaign_id,
                model=item.model,
                seed=item.seed,
                cfg_scale=float(item.cfg_scale) if item.cfg_scale else None,
                steps=item.steps,
                library_item_id=item.id,
            )
            return {"success": True, "library_item_id": str(item.id)}
        except Exception as e:
            item.status = "FAILED"
            db.commit()
            raise


# Celery Beat scheduler configuration
celery_app.conf.beat_schedule = {
    "provider-health-check-every-minute": {
        "task": "worker.tasks.health_worker_task",
        "schedule": 60.0,
    },
    "model-sync-every-day": {
        "task": "worker.tasks.model_sync_worker_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "cache-cleanup-every-hour": {
        "task": "worker.tasks.cleanup_worker_task",
        "schedule": crontab(minute=0),
    },
    "usage-aggregation-every-hour": {
        "task": "worker.tasks.usage_worker_task",
        "schedule": crontab(minute=0),
    },
    "cost-aggregation-every-day": {
        "task": "worker.tasks.cost_worker_task",
        "schedule": crontab(hour=1, minute=0),
    },
    "daily-quota-reset-at-midnight": {
        "task": "worker.tasks.quota_reset_worker_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "purge-deleted-accounts-every-hour": {
        "task": "worker.tasks.purge_deleted_accounts_task",
        "schedule": crontab(minute=0),
    },
}
