import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.memory import OrganizationMemory, AgentMemory, MemoryType
from api.schemas.memory import (
    OrganizationMemoryCreate,
    OrganizationMemoryUpdate,
    OrganizationMemoryResponse,
    AgentMemoryResponse,
)
from api.schemas.common import PaginatedResponse
from api.services.memory_manager import MemoryManager

router = APIRouter(prefix="/memory", tags=["memory"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@router.post(
    "/organization",
    response_model=OrganizationMemoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_memory(
    entry_in: OrganizationMemoryCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return MemoryManager.write_org_memory(
        db=db,
        organization_id=membership.organization_id,
        category=entry_in.category,
        key=entry_in.key,
        value=entry_in.value,
        metadata=entry_in.metadata,
    )


@router.get("/organization", response_model=PaginatedResponse[OrganizationMemoryResponse])
def list_organization_memories(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    skip = (page - 1) * page_size
    filters = [
        OrganizationMemory.organization_id == membership.organization_id,
        OrganizationMemory.deleted_at.is_(None),
    ]
    if category:
        filters.append(OrganizationMemory.category == category)

    items = (
        db.query(OrganizationMemory)
        .filter(and_(*filters))
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(OrganizationMemory)
        .filter(and_(*filters))
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.patch("/organization/{entry_id}", response_model=OrganizationMemoryResponse)
def update_organization_memory(
    entry_id: uuid.UUID,
    entry_in: OrganizationMemoryUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    entry = (
        db.query(OrganizationMemory)
        .filter(
            OrganizationMemory.id == entry_id,
            OrganizationMemory.organization_id == membership.organization_id,
            OrganizationMemory.deleted_at.is_(None),
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization memory entry not found",
        )

    update_data = entry_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/organization/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_memory(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    entry = (
        db.query(OrganizationMemory)
        .filter(
            OrganizationMemory.id == entry_id,
            OrganizationMemory.organization_id == membership.organization_id,
            OrganizationMemory.deleted_at.is_(None),
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization memory entry not found",
        )

    import datetime
    entry.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()


@router.delete("/sessions/{session_id}/clear", status_code=status.HTTP_200_OK)
def clear_session_memory(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    cleared_count = MemoryManager.clear_session_memory(
        db=db, session_id=session_id, organization_id=membership.organization_id
    )
    return {"success": True, "cleared_items": cleared_count}
