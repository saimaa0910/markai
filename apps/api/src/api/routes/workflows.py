import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.workflow import WorkflowDefinition, WorkflowExecution, WorkflowStep
from api.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowExecutionCreate,
    WorkflowExecutionResponse,
    WorkflowStepResponse,
)
from api.schemas.common import PaginatedResponse
from api.services.workflow_engine import WorkflowEngine
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

router = APIRouter(prefix="/workflows", tags=["workflows"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# --- DEFINITIONS ---

@router.post(
    "/definitions",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_definition(  # Sprint 8.3.1
    workflow_in: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    wf = WorkflowDefinition(
        name=workflow_in.name,
        description=workflow_in.description,
        status=workflow_in.status,
        trigger=workflow_in.trigger,
        steps_definition=workflow_in.steps_definition,
        cron_expression=workflow_in.cron_expression,
        webhook_config=workflow_in.webhook_config,
        max_retries=workflow_in.max_retries,
        timeout_seconds=workflow_in.timeout_seconds,
        organization_id=membership.organization_id,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


@router.get("/definitions", response_model=PaginatedResponse[WorkflowDefinitionResponse])
def list_workflow_definitions(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    skip = (page - 1) * page_size
    items = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/definitions/{wf_id}", response_model=WorkflowDefinitionResponse)
def get_workflow_definition(  # Sprint 8.3.1
    wf_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    wf = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.id == wf_id,
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .first()
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )
    return wf


@router.patch("/definitions/{wf_id}", response_model=WorkflowDefinitionResponse)
def update_workflow_definition(  # Sprint 8.3.1
    wf_id: uuid.UUID,
    workflow_in: WorkflowDefinitionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    wf = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.id == wf_id,
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .first()
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    update_data = workflow_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wf, field, value)

    db.commit()
    db.refresh(wf)
    return wf


@router.delete("/definitions/{wf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow_definition(  # Sprint 8.3.1
    wf_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> None:
    wf = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.id == wf_id,
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .first()
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    import datetime
    wf.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()


# --- EXECUTION ENDPOINTS ---

@router.post(
    "/definitions/{wf_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_workflow(  # Sprint 8.3.1
    wf_id: uuid.UUID,
    run_in: WorkflowExecutionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    wf = (
        db.query(WorkflowDefinition)
        .filter(
            WorkflowDefinition.id == wf_id,
            WorkflowDefinition.organization_id == membership.organization_id,
            WorkflowDefinition.deleted_at.is_(None),
        )
        .first()
    )
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow definition not found",
        )

    # 1. Create run execution
    execution = WorkflowExecution(
        workflow_id=wf_id,
        organization_id=membership.organization_id,
        triggered_by=membership.user_id,
        input_data=run_in.input_data,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 2. Run engine execution sync for MVP compliance
    result = WorkflowEngine.run_workflow(db=db, execution=execution)
    return result


@router.get("/executions", response_model=PaginatedResponse[WorkflowExecutionResponse])
def list_workflow_executions(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    workflow_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    skip = (page - 1) * page_size
    filters = [
        WorkflowExecution.organization_id == membership.organization_id,
        WorkflowExecution.deleted_at.is_(None),
    ]
    if workflow_id:
        filters.append(WorkflowExecution.workflow_id == workflow_id)

    items = (
        db.query(WorkflowExecution)
        .filter(and_(*filters))
        .order_by(WorkflowExecution.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(WorkflowExecution)
        .filter(and_(*filters))
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/executions/{exec_id}/steps", response_model=List[WorkflowStepResponse])
def list_execution_steps(  # Sprint 8.3.1
    exec_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    # Verify execution access
    execution = (
        db.query(WorkflowExecution)
        .filter(
            WorkflowExecution.id == exec_id,
            WorkflowExecution.organization_id == membership.organization_id,
            WorkflowExecution.deleted_at.is_(None),
        )
        .first()
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution record not found",
        )

    return (
        db.query(WorkflowStep)
        .filter(WorkflowStep.execution_id == exec_id)
        .order_by(WorkflowStep.created_at.asc())
        .all()
    )
