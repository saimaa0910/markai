"""Audit Log Routes — Sprint 8.3.1 Phase 4

API endpoints for audit log querying and export.
"""
import uuid
import logging
import json
import csv
import io
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user, get_current_admin_user
from api.models.user import User
from api.models.auth import AuditLog


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/security/audit", tags=["audit-logs"])


def _map_log(log) -> dict:
    """Map an AuditLog ORM row to the response schema fields."""
    try:
        details = json.loads(log.description) if log.description else None
    except (TypeError, ValueError, json.JSONDecodeError):
        details = None
    return {
        "id": str(log.id),
        "user_id": str(log.actor_id) if log.actor_id else "",
        "event_type": log.action or "",
        "ip_address": log.actor_ip,
        "user_agent": log.actor_user_agent,
        "details": details,
        "created_at": log.created_at.isoformat(),
    }


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


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO 8601 format.",
        )


def _build_query(db: Session, user_id: uuid.UUID, event_type, from_date, to_date):
    query = db.query(AuditLog).filter(AuditLog.actor_id == user_id)
    if event_type:
        query = query.filter(AuditLog.action == event_type)
    if from_date:
        query = query.filter(AuditLog.created_at >= from_date)
    if to_date:
        query = query.filter(AuditLog.created_at <= to_date)
    return query


# Endpoints

@router.get("/logs", response_model=AuditLogsListResponse)
async def get_user_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get audit logs for the current user."""
    from_datetime = _parse_date(from_date)
    to_datetime = _parse_date(to_date)

    query = _build_query(db, current_user.id, event_type, from_datetime, to_datetime)
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return AuditLogsListResponse(
        logs=[AuditLogEntryResponse(**_map_log(log)) for log in logs],
        total=total,
        page=offset // limit + 1,
        page_size=limit,
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
    db: Session = Depends(get_db),
):
    """Get audit logs for any user (admin only)."""
    from_datetime = _parse_date(from_date)
    to_datetime = _parse_date(to_date)

    query = _build_query(db, user_id, event_type, from_datetime, to_datetime)
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return AuditLogsListResponse(
        logs=[AuditLogEntryResponse(**_map_log(log)) for log in logs],
        total=total,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.get("/logs/export")
async def export_audit_logs(
    format: str = Query(..., description="Export format: json or csv"),
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export audit logs in JSON or CSV format."""
    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'json' or 'csv'",
        )

    from_datetime = _parse_date(from_date)
    to_datetime = _parse_date(to_date)

    logs = _build_query(db, current_user.id, event_type, from_datetime, to_datetime).order_by(
        AuditLog.created_at.desc()
    ).all()

    if format == "json":
        data = [_map_log(log) for log in logs]
        content = json.dumps(data, indent=2)
        media_type = "application/json"
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user_id", "event_type", "ip_address", "user_agent", "details", "created_at"])
        for log in logs:
            mapped = _map_log(log)
            writer.writerow([
                mapped["id"],
                mapped["user_id"],
                mapped["event_type"],
                mapped["ip_address"] or "",
                mapped["user_agent"] or "",
                json.dumps(mapped["details"]) if mapped["details"] else "",
                mapped["created_at"],
            ])
        content = output.getvalue()
        media_type = "text/csv"

    logger.info(f"User {current_user.id} exported {len(logs)} audit logs as {format}")
    return Response(content=content, media_type=media_type)
