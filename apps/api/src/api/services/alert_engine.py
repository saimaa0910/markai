import os
import time
import logging
import uuid
from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from api.core.config import settings
from api.models.observability import AIIncident, AIAlert
from api.core.metrics_registry import ai_failovers_total  # reuse failover counter

logger = logging.getLogger("api.services.alert_engine")

class AlertEngine:
    """
    Service responsible for incident tracking, threshold validation,
    and alert dispatching via Slack, Email, Webhooks, and Console logs.
    """

    @classmethod
    def report_incident(
        cls,
        db: Session,
        component: str,
        service: str,
        severity: str,
        root_cause: str,
        organization_id: Optional[uuid.UUID] = None
    ) -> AIIncident:
        """
        Record a system or provider failure incident in the database,
        then automatically trigger notifications.
        """
        try:
            # 1. Create DB Incident Record
            incident = AIIncident(
                organization_id=organization_id,
                component=component,
                service=service,
                severity=severity,
                root_cause=root_cause,
                status="active",
                start_time=datetime.utcnow(),
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)

            # 2. Trigger Alert for this Incident
            alert_type = f"{component.upper()}_{severity.upper()}"
            msg = f"Alert: Component '{component}' in service '{service}' is experiencing a {severity} incident. Reason: {root_cause}"
            cls.trigger_alert(
                db=db,
                alert_type=alert_type,
                message=msg,
                severity=severity,
                organization_id=organization_id,
                incident_id=incident.id
            )
            
            return incident
        except Exception as e:
            logger.error(f"Failed to report incident on {component}: {e}", exc_info=True)
            raise e

    @classmethod
    def resolve_incident(
        cls,
        db: Session,
        incident_id: uuid.UUID,
        resolution: str
    ) -> None:
        """
        Mark an active incident as resolved and record duration and resolution.
        """
        try:
            incident = db.query(AIIncident).filter(AIIncident.id == incident_id).first()
            if not incident:
                logger.warning(f"Incident {incident_id} not found to resolve.")
                return

            now = datetime.utcnow()
            incident.status = "resolved"
            incident.resolution = resolution
            incident.end_time = now
            
            # Calculate duration in seconds
            duration = (now - incident.start_time).total_seconds()
            incident.duration_sec = int(duration)
            db.commit()

            # Trigger resolution alert
            msg = f"RESOLVED: Component '{incident.component}' incident has been resolved. Duration: {incident.duration_sec}s. Resolution: {resolution}"
            cls.trigger_alert(
                db=db,
                alert_type=f"{incident.component.upper()}_RESOLVED",
                message=msg,
                severity="info",
                organization_id=incident.organization_id,
                incident_id=incident.id
            )
        except Exception as e:
            logger.error(f"Failed to resolve incident {incident_id}: {e}", exc_info=True)

    @classmethod
    def trigger_alert(
        cls,
        db: Session,
        alert_type: str,
        message: str,
        severity: str,
        organization_id: Optional[uuid.UUID] = None,
        incident_id: Optional[uuid.UUID] = None
    ) -> AIAlert:
        """
        Create an alert log and dispatch notifications to Slack, Email, and Webhooks.
        """
        # Determine active channels
        channels_list = ["console"]
        
        slack_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_url:
            channels_list.append("slack")
            
        smtp_host = settings.SMTP_HOST
        if smtp_host:
            channels_list.append("email")
            
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if webhook_url:
            channels_list.append("webhook")

        channels_str = ",".join(channels_list)

        # 1. Create DB Alert Record
        alert = AIAlert(
            organization_id=organization_id,
            incident_id=incident_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
            channels=channels_str,
            status="triggered"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # 2. Dispatch alerts
        success = True
        
        # Dispatch Slack
        if "slack" in channels_list:
            slack_ok = cls._dispatch_slack(slack_url, message, severity)
            success = success and slack_ok

        # Dispatch Email
        if "email" in channels_list:
            email_ok = cls._dispatch_email(message, alert_type)
            success = success and email_ok

        # Dispatch Webhook
        if "webhook" in channels_list:
            webhook_ok = cls._dispatch_webhook(webhook_url, alert_type, message, severity)
            success = success and webhook_ok

        # Dispatch Console
        cls._dispatch_console(message, severity)

        # 3. Update DB Alert Status
        alert.status = "sent" if success else "failed"
        db.commit()
        
        return alert

    @classmethod
    def _dispatch_console(cls, message: str, severity: str) -> None:
        """Log alert to standard python logs."""
        log_msg = f"[SYSTEM ALERT] Severity={severity} - {message}"
        if severity == "critical":
            logger.error(log_msg)
        elif severity == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    @classmethod
    def _dispatch_slack(cls, webhook_url: str, message: str, severity: str) -> bool:
        """Send message payload to Slack Incoming Webhook."""
        try:
            color = "#ff0000" if severity == "critical" else "#ffaa00" if severity == "warning" else "#00aa00"
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"EAIMOS Alert Manager - {severity.upper()}",
                        "text": message,
                        "fallback": message,
                        "ts": int(time.time())
                    }
                ]
            }
            # Perform synchronous post (with timeout)
            res = httpx.post(webhook_url, json=payload, timeout=5.0)
            return res.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to dispatch Slack alert: {e}")
            return False

    @classmethod
    def _dispatch_email(cls, message: str, alert_type: str) -> bool:
        """Send notification via unified SMTP transport."""
        try:
            from api.services.email_service import _send_email
            recipient = settings.ALERT_EMAIL_RECIPIENT
            subject = f"[EAIMOS Alert] {alert_type}"
            # Wrap plain text in minimal HTML for consistency
            html_body = f'<p style="color:#d1d5db;font-size:14px;line-height:1.6;">{message}</p>'
            return _send_email(recipient, subject, html_body)
        except Exception as e:
            logger.warning(f"Failed to dispatch Email alert: {e}")
            return False

    @classmethod
    def _dispatch_webhook(cls, webhook_url: str, alert_type: str, message: str, severity: str) -> bool:
        """Send POST request to user configured webhook URL."""
        try:
            payload = {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat()
            }
            res = httpx.post(webhook_url, json=payload, timeout=5.0)
            return res.status_code < 300
        except Exception as e:
            logger.warning(f"Failed to dispatch custom webhook alert: {e}")
            return False
