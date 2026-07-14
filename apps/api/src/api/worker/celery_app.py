"""
Celery Worker Application Config
================================
Configures Celery tasks with Redis broker.
Includes task hooks for agent executor, notification emails, and campaign schedules.
"""
import os
import uuid
from typing import Any, Dict, List
from celery import Celery
from api.core.config import settings

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


@celery_app.task(name="worker.tasks.agent_run_task")
def agent_run_task(session_id_str: str, user_input: str) -> Dict[str, Any]:
    """Background task to run an AI Agent session asynchronously."""
    from api.database.session import SessionLocal
    from api.models.agent import AgentSession
    from api.services.agent_executor import AgentExecutorService

    session_id = uuid.UUID(session_id_str)
    db = SessionLocal()
    try:
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
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="worker.tasks.notification_task")
def notification_task(
    user_id_str: str,
    org_id_str: str,
    title: str,
    body: str,
    channel_str: str,
    event_type: str = None,
) -> Dict[str, Any]:
    """Background task to dispatch email/in-app notifications."""
    from api.database.session import SessionLocal
    from api.models.integration import NotificationChannel
    from api.services.notification_service import NotificationService

    user_id = uuid.UUID(user_id_str)
    org_id = uuid.UUID(org_id_str)
    channel = NotificationChannel(channel_str)

    db = SessionLocal()
    try:
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
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="worker.tasks.campaign_broadcast_task")
def campaign_broadcast_task(campaign_id_str: str) -> Dict[str, Any]:
    """Background task to trigger campaign schedules and newsletter blasts."""
    from api.database.session import SessionLocal
    from api.models.campaign import Campaign, CampaignStatus

    campaign_id = uuid.UUID(campaign_id_str)
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        campaign.status = CampaignStatus.ACTIVE
        db.commit()

        # Simulate template delivery loop to contacts in target org
        from api.models.contact import Contact
        contacts = (
            db.query(Contact)
            .filter(
                Contact.organization_id == campaign.organization_id,
                Contact.deleted_at.is_(None),
            )
            .all()
        )

        for contact in contacts:
            # Broadcast notification dispatch task
            notification_task.delay(
                user_id_str=str(contact.id), # Fallback contacts represent targets
                org_id_str=str(campaign.organization_id),
                title=campaign.title,
                body=f"Hello {contact.full_name}, check out our newsletter details.",
                channel_str="EMAIL",
                event_type="campaign_broadcast",
            )

        campaign.status = CampaignStatus.COMPLETED
        db.commit()
        return {"success": True, "recipients_count": len(contacts)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()
