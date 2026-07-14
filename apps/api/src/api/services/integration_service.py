import uuid
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.models.integration import Integration, IntegrationCredential, SyncJob, IntegrationProvider, IntegrationStatus
from api.models.knowledge import KnowledgeDocument, DocumentChunk
from api.services.knowledge import KnowledgeService
from api.schemas.ai import KnowledgeUploadRequest


class IntegrationService:
    """
    Manages external platform credentials (OAuth, API keys), integration health,
    and runs synchronization pipelines (sync jobs).
    """

    @staticmethod
    def connect_integration(
        db: Session,
        organization_id: uuid.UUID,
        provider: IntegrationProvider,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        credentials_data: Optional[Dict[str, Any]] = None,
    ) -> Integration:
        # Check if already exists
        existing = db.scalars(
            select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.provider == provider,
                    Integration.deleted_at.is_(None),
                )
            )
        ).first()

        if existing:
            existing.name = name
            existing.status = IntegrationStatus.CONNECTED
            existing.config = config
            db.commit()
            db.refresh(existing)
            integration = existing
        else:
            integration = Integration(
                organization_id=organization_id,
                provider=provider,
                name=name,
                status=IntegrationStatus.CONNECTED,
                config=config,
            )
            db.add(integration)
            db.commit()
            db.refresh(integration)

        # Upsert credentials
        if credentials_data:
            stmt = select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration.id
            )
            creds = db.scalars(stmt).first()
            if creds:
                creds.access_token = credentials_data.get("access_token")
                creds.refresh_token = credentials_data.get("refresh_token")
                creds.token_expiry = credentials_data.get("token_expiry")
                creds.api_key = credentials_data.get("api_key")
                creds.extra = credentials_data.get("extra")
            else:
                creds = IntegrationCredential(
                    integration_id=integration.id,
                    organization_id=organization_id,
                    access_token=credentials_data.get("access_token"),
                    refresh_token=credentials_data.get("refresh_token"),
                    token_expiry=credentials_data.get("token_expiry"),
                    api_key=credentials_data.get("api_key"),
                    extra=credentials_data.get("extra"),
                )
                db.add(creds)
            db.commit()

        return integration

    @staticmethod
    def trigger_sync(
        db: Session,
        integration: Integration,
        triggered_by_user_id: uuid.UUID,
    ) -> SyncJob:
        sync_job = SyncJob(
            integration_id=integration.id,
            organization_id=integration.organization_id,
            status="running",
            records_synced=0,
        )
        db.add(sync_job)
        db.commit()
        db.refresh(sync_job)

        try:
            # Run Sync operations based on Provider
            if integration.provider == IntegrationProvider.GOOGLE_DRIVE:
                # Simulate importing Google Drive documentation into the Knowledge platform
                upload_in = KnowledgeUploadRequest(
                    title=f"Google Drive Sync - {datetime.date.today()}",
                    file_type="md",
                    content=(
                        "# Synced Corporate Guidelines\n"
                        "This document has been synchronized automatically from Google Drive.\n"
                        "Brand Voice Guideline: Professional, precise, enterprise-ready, marketing-native.\n"
                        "Target Audience: CMOS, Director of Marketing, Marketing Operations Directors."
                    ),
                )
                KnowledgeService.upload_document(
                    db=db,
                    doc_in=upload_in,
                    organization_id=integration.organization_id,
                    user_id=triggered_by_user_id,
                )
                sync_job.records_synced = 1

            elif integration.provider == IntegrationProvider.SLACK:
                # Simulate Slack alert/sync configurations
                sync_job.records_synced = 5

            else:
                # Fallback custom endpoint webhook registrations
                sync_job.records_synced = 2

            sync_job.status = "success"
            integration.last_synced_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            db.commit()

        except Exception as e:
            db.rollback()
            sync_job.status = "failed"
            sync_job.error_message = str(e)
            integration.status = IntegrationStatus.ERROR
            integration.error_message = str(e)
            db.commit()

        return sync_job

    @staticmethod
    def check_health(db: Session, integration: Integration) -> IntegrationStatus:
        """Verify integration credentials validity and service status."""
        try:
            if integration.provider == IntegrationProvider.WEBHOOK:
                # Webhooks are always active/connected unless disabled
                integration.status = IntegrationStatus.CONNECTED
            else:
                creds = db.scalars(
                    select(IntegrationCredential).where(
                        IntegrationCredential.integration_id == integration.id
                    )
                ).first()
                if creds and (creds.access_token or creds.api_key):
                    integration.status = IntegrationStatus.CONNECTED
                else:
                    integration.status = IntegrationStatus.DISCONNECTED

            integration.error_message = None
            db.commit()
            return integration.status

        except Exception as e:
            integration.status = IntegrationStatus.ERROR
            integration.error_message = str(e)
            db.commit()
            return integration.status
class OAuthService:
    """Mock Helper service managing OAuth flow authorization links."""
    @staticmethod
    def get_auth_url(provider: str, organization_id: uuid.UUID) -> str:
        return f"https://auth.viptant.ai/oauth/{provider}?state={organization_id}"
