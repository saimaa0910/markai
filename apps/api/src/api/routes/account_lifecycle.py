"""
EAIMOS Account Lifecycle API Routes (Sprint 8.3.1 Phase 3)
===========================================================
Advanced account management endpoints for data export, deactivation,
lockout management, and audit history.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field

from api.dependencies.auth import get_current_user, get_service_context
from api.models.iam import User
from api.services.account_lifecycle_service import (
    AccountLifecycleService,
    ExportFormat,
)
from api.services.base import ServiceContext

logger = logging.getLogger("eaimos.api.account_lifecycle")

router = APIRouter(prefix="/account/lifecycle", tags=["Account Lifecycle"])


# ─── Request/Response Models ──────────────────────────────────────────────────


class ExportAccountRequest(BaseModel):
    """Request body for account data export."""
    export_format: ExportFormat = Field(
        default=ExportFormat.JSON,
        description="Export format: json or csv"
    )


class DeactivateAccountRequest(BaseModel):
    """Request body for account deactivation."""
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for deactivation"
    )


class AccountExportResponse(BaseModel):
    """Response for account data export."""
    export_data: dict
    format: str
    total_sessions: int


class AccountStatusResponse(BaseModel):
    """Response for account status check."""
    user_id: str
    email: str
    overall_status: str
    account_info: dict
    security_status: dict
    session_info: dict
    lifecycle_info: dict


class AccountHistoryResponse(BaseModel):
    """Response for account history."""
    user_id: str
    timeline: list
    total_events: int


class LifecycleActionResponse(BaseModel):
    """Generic response for lifecycle actions."""
    user_id: str
    message: str


# ─── Data Export ──────────────────────────────────────────────────────────────


@router.post(
    "/export",
    response_model=AccountExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export Account Data",
    description="""
    Export all user account data in JSON or CSV format (GDPR compliance).
    
    Returns:
    - User profile data
    - Session history
    - Login history
    - Security settings
    - All personal information
    
    Users can export their own data. Admins can export any user's data.
    """,
)
async def export_account_data(
    request: ExportAccountRequest,
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountExportResponse:
    """
    Export user account data for GDPR compliance.
    """
    service = AccountLifecycleService()
    result = await service.export_account_data(
        ctx=ctx,
        user_id=current_user.id,
        export_format=request.export_format,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountExportResponse(**result.data)


@router.get(
    "/{user_id}/export",
    response_model=AccountExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export User Data (Admin)",
    description="Export any user's account data. Admin only.",
)
async def export_user_data_admin(
    user_id: UUID,
    export_format: ExportFormat = Query(ExportFormat.JSON),
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountExportResponse:
    """
    Admin endpoint to export any user's data.
    """
    service = AccountLifecycleService()
    result = await service.export_account_data(
        ctx=ctx,
        user_id=user_id,
        export_format=export_format,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountExportResponse(**result.data)


# ─── Account Deactivation ─────────────────────────────────────────────────────


@router.post(
    "/deactivate",
    response_model=LifecycleActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Account",
    description="""
    Temporarily deactivate your account.
    
    Effects:
    - Account cannot log in
    - All active sessions are revoked
    - Data is retained
    - Can be reactivated at any time
    
    This is different from deletion:
    - Deactivation: Temporary, reversible, data retained
    - Deletion: Permanent (after grace period), data removed
    """,
)
async def deactivate_account(
    request: DeactivateAccountRequest,
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> LifecycleActionResponse:
    """
    Deactivate the current user's account.
    """
    service = AccountLifecycleService()
    result = await service.deactivate_account(
        ctx=ctx,
        user_id=current_user.id,
        reason=request.reason,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return LifecycleActionResponse(
        user_id=result.data["user_id"],
        message=result.data["message"],
    )


@router.post(
    "/reactivate",
    response_model=LifecycleActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate Account",
    description="""
    Reactivate a temporarily deactivated account.
    
    After reactivation:
    - Account can log in again
    - Must authenticate with credentials
    - Previous sessions remain revoked
    """,
)
async def reactivate_account(
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> LifecycleActionResponse:
    """
    Reactivate a deactivated account.
    """
    service = AccountLifecycleService()
    result = await service.reactivate_account(
        ctx=ctx,
        user_id=current_user.id,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return LifecycleActionResponse(
        user_id=result.data["user_id"],
        message=result.data["message"],
    )


# ─── Lockout Management ───────────────────────────────────────────────────────


@router.post(
    "/unlock",
    response_model=LifecycleActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlock Account",
    description="""
    Manually unlock a locked account.
    
    Effects:
    - Removes account lock
    - Resets failed login counter
    - Clears locked_until timestamp
    - Audit-logged for security
    
    Users can unlock their own accounts if they have access (e.g., via email link).
    Admins can unlock any account.
    """,
)
async def unlock_account(
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> LifecycleActionResponse:
    """
    Unlock the current user's locked account.
    """
    service = AccountLifecycleService()
    result = await service.unlock_account(
        ctx=ctx,
        user_id=current_user.id,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return LifecycleActionResponse(
        user_id=result.data["user_id"],
        message=result.data["message"],
    )


@router.post(
    "/{user_id}/unlock",
    response_model=LifecycleActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlock User Account (Admin)",
    description="Admin endpoint to unlock any user's account.",
)
async def unlock_user_account_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> LifecycleActionResponse:
    """
    Admin endpoint to unlock any user's account.
    """
    service = AccountLifecycleService()
    result = await service.unlock_account(
        ctx=ctx,
        user_id=user_id,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return LifecycleActionResponse(
        user_id=result.data["user_id"],
        message=result.data["message"],
    )


# ─── Account Status & History ─────────────────────────────────────────────────


@router.get(
    "/status",
    response_model=AccountStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Account Status",
    description="""
    Get comprehensive account status information.
    
    Returns:
    - Basic account info
    - Security status (locked, deactivated, etc.)
    - Activity metrics
    - Lifecycle information
    - Session counts
    """,
)
async def get_account_status(
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountStatusResponse:
    """
    Get the current user's account status.
    """
    service = AccountLifecycleService()
    result = await service.get_account_status(
        ctx=ctx,
        user_id=current_user.id,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountStatusResponse(**result.data)


@router.get(
    "/history",
    response_model=AccountHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Account History",
    description="""
    Get account lifecycle event history.
    
    Returns timeline of:
    - Account creation
    - Email verification
    - Password changes
    - Login history
    - Status changes (locked, deactivated, deleted)
    - Session revocations
    """,
)
async def get_account_history(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events to return"),
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountHistoryResponse:
    """
    Get the current user's account history.
    """
    service = AccountLifecycleService()
    result = await service.get_account_history(
        ctx=ctx,
        user_id=current_user.id,
        limit=limit,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountHistoryResponse(**result.data)


@router.get(
    "/{user_id}/status",
    response_model=AccountStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Status (Admin)",
    description="Admin endpoint to view any user's account status.",
)
async def get_user_status_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountStatusResponse:
    """
    Admin endpoint to get any user's account status.
    """
    service = AccountLifecycleService()
    result = await service.get_account_status(
        ctx=ctx,
        user_id=user_id,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountStatusResponse(**result.data)


@router.get(
    "/{user_id}/history",
    response_model=AccountHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User History (Admin)",
    description="Admin endpoint to view any user's account history.",
)
async def get_user_history_admin(
    user_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    ctx: ServiceContext = Depends(get_service_context),
) -> AccountHistoryResponse:
    """
    Admin endpoint to get any user's account history.
    """
    service = AccountLifecycleService()
    result = await service.get_account_history(
        ctx=ctx,
        user_id=user_id,
        limit=limit,
    )
    
    if not result.success:
        raise result.to_exception()
    
    return AccountHistoryResponse(**result.data)
