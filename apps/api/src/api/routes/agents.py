import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog
from api.repositories.agent import (
    agent_definition_repo,
    agent_session_repo,
    agent_run_repo,
    agent_log_repo,
)
from api.schemas.agent import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    AgentDefinitionResponse,
    AgentSessionCreate,
    AgentSessionUpdate,
    AgentSessionResponse,
    AgentRunCreate,
    AgentRunResponse,
    AgentLogResponse,
)
from api.schemas.common import PaginatedResponse
from api.services.agent_executor import AgentExecutorService

router = APIRouter(prefix="/agents", tags=["agents"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# --- AGENT DEFINITION ENDPOINTS ---

@router.post(
    "/definitions",
    response_model=AgentDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_definition(
    agent_in: AgentDefinitionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    obj_data = agent_in.model_dump()
    return agent_definition_repo.create(
        db=db,
        obj_in=obj_data,
        organization_id=membership.organization_id,
        created_by=str(membership.user_id),
    )


@router.get("/definitions", response_model=PaginatedResponse[AgentDefinitionResponse])
def list_agent_definitions(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    skip = (page - 1) * page_size
    items = agent_definition_repo.list_by_org(
        db=db, organization_id=membership.organization_id, skip=skip, limit=page_size
    )
    total = agent_definition_repo.count_by_org(
        db=db, organization_id=membership.organization_id
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/definitions/{agent_id}", response_model=AgentDefinitionResponse)
def get_agent_definition(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    return agent


@router.patch("/definitions/{agent_id}", response_model=AgentDefinitionResponse)
def update_agent_definition(
    agent_id: uuid.UUID,
    agent_in: AgentDefinitionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    update_data = agent_in.model_dump(exclude_unset=True)
    return agent_definition_repo.update(
        db=db, db_obj=agent, obj_in=update_data, updated_by=str(membership.user_id)
    )


@router.delete("/definitions/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_definition(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    agent_definition_repo.soft_delete(
        db=db, db_obj=agent, deleted_by=str(membership.user_id)
    )


# --- AGENT SESSION ENDPOINTS ---

@router.post(
    "/sessions",
    response_model=AgentSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_session(
    session_in: AgentSessionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify agent exists
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=session_in.agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target agent definition does not exist in your organization",
        )

    db_session = AgentSession(
        agent_id=session_in.agent_id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        title=session_in.title,
        context=session_in.context,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/sessions", response_model=PaginatedResponse[AgentSessionResponse])
def list_agent_sessions(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    skip = (page - 1) * page_size
    items = agent_session_repo.list_by_user_and_org(
        db=db,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        skip=skip,
        limit=page_size,
    )
    # Count sessions
    total = (
        db.query(AgentSession)
        .filter(
            AgentSession.user_id == membership.user_id,
            AgentSession.organization_id == membership.organization_id,
            AgentSession.deleted_at.is_(None),
        )
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
def get_agent_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    return session


@router.patch("/sessions/{session_id}", response_model=AgentSessionResponse)
def update_agent_session(
    session_id: uuid.UUID,
    session_in: AgentSessionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    update_data = session_in.model_dump(exclude_unset=True)
    return agent_session_repo.update(
        db=db, db_obj=session, obj_in=update_data, updated_by=str(membership.user_id)
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    agent_session_repo.soft_delete(
        db=db, db_obj=session, deleted_by=str(membership.user_id)
    )


# --- EXECUTION & LOG RUN ENDPOINTS ---

@router.post(
    "/sessions/{session_id}/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_agent_run(
    session_id: uuid.UUID,
    run_in: AgentRunCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )

    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot execute in an inactive session",
        )

    # Trigger core agent execution engine
    run = AgentExecutorService.run_agent_session(
        db=db, session=session, user_input=run_in.user_input
    )
    return run


@router.get("/sessions/{session_id}/runs", response_model=PaginatedResponse[AgentRunResponse])
def list_agent_runs(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    # Verify session access first
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )

    skip = (page - 1) * page_size
    items = agent_run_repo.list_by_session(
        db=db, session_id=session_id, skip=skip, limit=page_size
    )
    total = (
        db.query(AgentRun)
        .filter(AgentRun.session_id == session_id, AgentRun.deleted_at.is_(None))
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/runs/{run_id}/logs", response_model=List[AgentLogResponse])
def list_run_logs(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify run exists and is within organization
    run = db.query(AgentRun).filter(
        AgentRun.id == run_id,
        AgentRun.organization_id == membership.organization_id,
        AgentRun.deleted_at.is_(None),
    ).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run execution record not found",
        )

    return agent_log_repo.list_by_run(db=db, run_id=run_id)
