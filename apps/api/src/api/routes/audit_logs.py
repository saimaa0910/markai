"""Audit Log Routes — Sprint 8.3.1 Phase 4

API endpoints for audit log querying and export.
"""
import uuid
import logging
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import json
import csv
import io

from api.core.database import get_db
from api.core.security import get_current_user, get_current_admin_user
from api.models.user import User
from api.services.audit_log_service import AuditLogService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/audit", tags=["audit-logs"])


# Request/Response Models

class AuditLogEntryResponse(BaseModel):
    """Single audit log entry."""
    id: str
    user_id: str
    event_type: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[dict]
    created_at: str


class AuditLogsListResponse(BaseModel):
    """List of audit log entries."""
    logs: List[AuditLogEntryResponse]
    total: int
    page: int
    page_size: int


class ExportAuditLogsRequest(BaseModel):
    """Request to export audit logs."""
    format: str = Field(..., description="Export format: json or csv")
    from_date: Optional[str] = Field(None, description="Start date (ISO format)")
    to_date: Optional[str] = Field(None, description="End date (ISO format)")
    event_type: Optional[str] = Field(None, description="Filter by event type")


# Endpoints

@router.get("/logs", response_model=AuditLogsListResponse)
async def get_user_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit logs for the current user.
    """
    try:
        # Parse date filters
        from_datetime = None
        to_datetime = None
        
        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid from_date format. Use ISO 8601 format.",
                )
        
        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid to_date format. Use ISO 8601 format.",
                )
        
        # Get logs
        logs = await AuditLogService.get_user_logs(
            db=db,
            user_id=current_user.id,
            event_type=event_type,
            from_date=from_datetime,
            to_date=to_datetime,
            limit=limit,
            offset=offset,
        )
        
        # Get total count
        total = await AuditLogService.count_user_logs(
            db=db,
            user_id=current_user.id,
            event_type=event_type,
            from_date=from_datetime,
            to_date=to_datetime,
        )
        
        return AuditLogsListResponse(
            logs=[
                AuditLogEntryResponse(
                    id=str(log.id),
                    user_id=str(log.user_id),
                    event_type=log.event_type,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    details=log.details,
                    created_at=log.created_at.isoformat(),
                )
                for log in logs
            ],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.get("/{user_id}/logs", response_model=AuditLogsListResponse)
async def get_any_user_audit_logs(
    user_id: uuid.UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit logs for any user (admin only).
    """
    try:
        # Parse date filters
        from_datetime = None
        to_datetime = None
        
        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid from_date format. Use ISO 8601 format.",
                )
        
        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid to_date format. Use ISO 8601 format.",
                )
        
        # Get logs
        logs = await AuditLogService.get_user_logs(
            db=db,
            user_id=user_id,
            event_type=event_type,
            from_date=from_datetime,
            to_date=to_datetime,
            limit=limit,
            offset=offset,
        )
        
        # Get total count
        total = await AuditLogService.count_user_logs(
            db=db,
            user_id=user_id,
            event_type=event_type,
            from_date=from_datetime,
            to_date=to_datetime,
        )
        
        return AuditLogsListResponse(
            logs=[
                AuditLogEntryResponse(
                    id=str(log.id),
                    user_id=str(log.user_id),
                    event_type=log.event_type,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    details=log.details,
                    created_at=log.created_at.isoformat(),
                )
                for log in logs
            ],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.post("/export")
async def export_audit_logs(
    body: ExportAuditLogsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export audit logs in JSON or CSV format.
    """
    try:
        # Validate format
        if body.format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'json' or 'csv'",
            )
        
        # Parse date filters
        from_datetime = None
        to_datetime = None
        
        if body.from_date:
            try:
                from_datetime = datetime.fromisoformat(body.from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid from_date format. Use ISO 8601 format.",
                )
        
        if body.to_date:
            try:
                to_datetime = datetime.fromisoformat(body.to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid to_date format. Use ISO 8601 format.",
                )
        
        # Get logs (no limit for export)
        logs = await AuditLogService.get_user_logs(
            db=db,
            user_id=current_user.id,
            event_type=body.event_type,
            from_date=from_datetime,
            to_date=to_datetime,
            limit=10000,  # Maximum for export
            offset=0,
        )
        
        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{timestamp}.{body.format}"
        
        if body.format == "json":
            # Export as JSON
            data = [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id),
                    "event_type": log.event_type,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "details": log.details,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
            
            content = json.dumps(data, indent=2)
            media_type = "application/json"
            
        else:  # csv
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["id", "user_id", "event_type", "ip_address", "user_agent", "details", "created_at"])
            
            # Write rows
            for log in logs:
                writer.writerow([
                    str(log.id),
                    str(log.user_id),
                    log.event_type,
                    log.ip_address or "",
                    log.user_agent or "",
                    json.dumps(log.details) if log.details else "",
                    log.created_at.isoformat(),
                ])
            
            content = output.getvalue()
            media_type = "text/csv"
        
        # Log the export
        await AuditLogService.log_event(
            db=db,
            user_id=current_user.id,
            event_type="audit_log_exported",
            ip_address=None,
            user_agent=None,
            details={
                "format": body.format,
                "record_count": len(logs),
                "from_date": body.from_date,
                "to_date": body.to_date,
            },
        )
        
        logger.info(f"User {current_user.id} exported {len(logs)} audit logs as {body.format}")
        
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs",
        )
