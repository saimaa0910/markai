import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.schemas.prompt import (
    PromptCreate, PromptUpdate, PromptResponse,
    PromptCollectionCreate, PromptCollectionResponse,
    PromptFolderCreate, PromptFolderResponse,
    PromptCategoryCreate, PromptCategoryResponse,
    PromptTagCreate, PromptTagResponse,
    PromptExecuteRequest, PromptExecuteResponse,
    PromptOptimizeRequest, PromptImportRequest,
    PromptShareRequest, PromptShareResponse,
    PromptBulkActionRequest, PromptSearchRequest,
    PromptTestCaseCreate, PromptTestCaseResponse,
    PromptEvaluationResponse, PromptAuditLogResponse
)
from api.services.prompt import (
    PromptService, VersionService, FolderService,
    CollectionService, ExecutionService, EvaluationService,
    AnalyticsService, ShareService, FavoriteService,
    CategoryService, TagService, OptimizationService, ImportExportService
)
from api.repositories.prompt import PromptRepository, AuditLogRepository

router = APIRouter(prefix="/prompts", tags=["prompts"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER, UserRole.GUEST])
admin_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN])


def _resolve_prompt(db: Session, identifier: str, organization_id: uuid.UUID, include_deleted: bool = False):
    """Resolve prompt by UUID or name."""
    try:
        val_uuid = uuid.UUID(identifier)
        prompt = PromptRepository.get_by_id(db, val_uuid, organization_id, include_deleted=include_deleted)
    except ValueError:
        prompt = PromptRepository.get_by_name(db, identifier, organization_id)
    return prompt


# -------------------------------------------------------------------
# PROMPTS CRUD
# -------------------------------------------------------------------

from api.services.base import ServiceContext
from api.services.ai import PromptService as ServicePromptService, CreatePromptDTO, get_prompt_service


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(  # Sprint 8.3.1
    prompt_in: PromptCreate,
    membership: UserOrganization = Depends(active_member),
    prompt_service: ServicePromptService = Depends(get_prompt_service),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    role_val = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    role_mapping = {
        "OWNER": "super_admin",
        "ADMIN": "organization_admin",
        "MEMBER": "developer",
        "GUEST": "viewer",
    }
    mapped_role = role_mapping.get(role_val.upper(), "viewer")

    ctx = ServiceContext(
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        roles=[mapped_role],
    )
    template_str = getattr(prompt_in, "template", None) or getattr(prompt_in, "content", None) or ""
    dto = CreatePromptDTO(
        title=getattr(prompt_in, "title", None) or prompt_in.name,
        template=template_str,
        description=getattr(prompt_in, "description", None),
    )
    result = await prompt_service.create_prompt(ctx, org_id=membership.organization_id, dto=dto)
    if result.is_failure:
        raise HTTPException(status_code=result.status_code, detail=result.errors)

    res = result.unwrap()
    return {
        "id": res.id,
        "organization_id": res.organization_id,
        "name": res.title,
        "title": res.title,
        "content": res.template,
        "template": res.template,
        "description": res.description,
        "version": res.version,
        "is_active": res.is_active,
        "created_at": res.created_at,
    }


@router.get("/", response_model=dict)
def list_prompts(  # Sprint 8.3.1
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    folder_id: Optional[uuid.UUID] = None,
    collection_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompts, total = PromptRepository.list_by_organization(
        db=db,
        organization_id=membership.organization_id,
        skip=skip,
        limit=limit,
        category=category,
        folder_id=folder_id,
        collection_id=collection_id,
        status=status_filter
    )
    from pydantic import TypeAdapter
    ta = TypeAdapter(List[PromptResponse])
    items = ta.validate_python([p.__dict__ for p in prompts], from_attributes=True)
    return {"items": [i.model_dump() for i in items], "total": total, "skip": skip, "limit": limit}


# -------------------------------------------------------------------
# STATIC ROUTES (must be before parameterized routes)
# -------------------------------------------------------------------

@router.get("/folders", response_model=List[PromptFolderResponse])
def list_folders(  # Sprint 8.3.1
    collection_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return FolderService.list_folders(
        db=db, organization_id=membership.organization_id, collection_id=collection_id
    )


@router.post("/folders", response_model=PromptFolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(  # Sprint 8.3.1
    folder_in: PromptFolderCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return FolderService.create_folder(
        db=db, folder_in=folder_in, organization_id=membership.organization_id, user_id=membership.user_id
    )


@router.get("/collections", response_model=List[PromptCollectionResponse])
def list_collections(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return CollectionService.list_collections(db=db, organization_id=membership.organization_id)


@router.post("/collections", response_model=PromptCollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(  # Sprint 8.3.1
    col_in: PromptCollectionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return CollectionService.create_collection(
        db=db, col_in=col_in, organization_id=membership.organization_id, user_id=membership.user_id
    )


@router.get("/categories", response_model=List[PromptCategoryResponse])
def list_categories(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return CategoryService.list_categories(db=db, organization_id=membership.organization_id)


@router.post("/categories", response_model=PromptCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(  # Sprint 8.3.1
    cat_in: PromptCategoryCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return CategoryService.create_category(
        db=db, cat_in=cat_in, organization_id=membership.organization_id
    )


@router.get("/tags", response_model=List[PromptTagResponse])
def list_tags(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return TagService.list_tags(db=db, organization_id=membership.organization_id)


@router.post("/tags", response_model=PromptTagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(  # Sprint 8.3.1
    tag_in: PromptTagCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    return TagService.create_tag(
        db=db, tag_in=tag_in, organization_id=membership.organization_id
    )


@router.get("/audit-logs", response_model=dict)
def list_audit_logs(  # Sprint 8.3.1
    prompt_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    logs = AuditLogRepository.list_by_org(
        db=db, organization_id=membership.organization_id, limit=limit
    )
    # Filter by prompt_id if provided
    if prompt_id:
        logs = [log for log in logs if log.prompt_id == prompt_id]
    from pydantic import TypeAdapter
    ta = TypeAdapter(List[PromptAuditLogResponse])
    items = ta.validate_python([log.__dict__ for log in logs], from_attributes=True)
    return {"items": [i.model_dump() for i in items], "total": len(items)}


@router.post("/search", response_model=dict)
def search_prompts(  # Sprint 8.3.1
    search_req: PromptSearchRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompts, total = PromptRepository.search(
        db=db,
        organization_id=membership.organization_id,
        query=search_req.query,
        category=search_req.category,
        tag=search_req.tag,
        folder_id=search_req.folder_id,
        collection_id=search_req.collection_id,
        status=search_req.status,
        owner_id=search_req.owner_id,
        is_archived=search_req.is_archived or False,
        skip=search_req.skip or 0,
        limit=search_req.limit or 50,
        sort_by=search_req.sort_by or "updated_at",
        sort_order=search_req.sort_order or "desc"
    )
    from pydantic import TypeAdapter
    ta = TypeAdapter(List[PromptResponse])
    items = ta.validate_python([p.__dict__ for p in prompts], from_attributes=True)
    return {"items": [i.model_dump() for i in items], "total": total}


# -------------------------------------------------------------------
# PARAMETERIZED ROUTES — specific sub-paths before generic /{identifier}
# -------------------------------------------------------------------

@router.get("/{identifier}", response_model=PromptResponse)
def get_prompt(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{identifier}' not found."
        )
    return prompt


@router.put("/{identifier}", response_model=PromptResponse)
def update_prompt(  # Sprint 8.3.1
    identifier: str,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    name = prompt.name if prompt else identifier

    return PromptService.update_prompt_version(
        db=db,
        name=name,
        prompt_in=prompt_in,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@router.delete("/{identifier}", status_code=status.HTTP_200_OK)
def delete_prompt(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    name = prompt.name if prompt else identifier

    PromptService.soft_delete(
        db=db,
        prompt_name=name,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )
    return {"success": True, "message": f"Prompt '{name}' soft-deleted."}


@router.post("/{identifier}/restore", response_model=PromptResponse)
def restore_prompt(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id, include_deleted=True)
    name = prompt.name if prompt else identifier

    return PromptService.restore(
        db=db,
        prompt_name=name,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@router.delete("/{identifier}/purge", status_code=status.HTTP_204_NO_CONTENT)
def purge_prompt(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> None:
    prompt = _resolve_prompt(db, identifier, membership.organization_id, include_deleted=True)
    name = prompt.name if prompt else identifier

    PromptService.permanent_delete(
        db=db,
        prompt_name=name,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@router.post("/{identifier}/clone", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
def clone_prompt(  # Sprint 8.3.1
    identifier: str,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    new_name = body.get("new_name") if body else None
    if not new_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'new_name' is required in request body."
        )

    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    name = prompt.name if prompt else identifier

    return PromptService.duplicate_prompt(
        db=db,
        name=name,
        new_name=new_name,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@router.post("/{identifier}/archive", response_model=PromptResponse)
def archive_prompt(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Archive a prompt by setting is_archived=True on the LATEST version."""
    # First resolve by id/name to get the canonical name
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{identifier}' not found."
        )

    # Archive ALL versions of this prompt (by name) to ensure latest is archived
    from sqlalchemy import update as sa_update
    from api.models.prompt import Prompt as PromptModel
    db.execute(
        sa_update(PromptModel)
        .where(
            PromptModel.name == prompt.name,
            PromptModel.organization_id == membership.organization_id,
        )
        .values(is_archived=True, status="archived")
    )
    db.commit()
    db.refresh(prompt)

    AuditLogRepository.log_action(
        db=db,
        prompt_id=prompt.id,
        prompt_name=prompt.name,
        action="ARCHIVED",
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        metadata_json={}
    )

    return prompt


@router.post("/{identifier}/favorite", status_code=status.HTTP_200_OK)
def toggle_favorite(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    name = prompt.name if prompt else identifier

    is_fav = FavoriteService.toggle_favorite(
        db=db, prompt_name=name, user_id=membership.user_id, organization_id=membership.organization_id
    )
    return {"success": True, "is_favorite": is_fav}


@router.post("/{identifier}/pin", status_code=status.HTTP_200_OK)
def toggle_pin(  # Sprint 8.3.1
    identifier: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    prompt = _resolve_prompt(db, identifier, membership.organization_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt '{identifier}' not found.")

    prompt.is_pinned = not prompt.is_pinned
    db.commit()
    db.refresh(prompt)
    return {"success": True, "is_pinned": prompt.is_pinned}
