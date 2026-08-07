import uuid
import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.agent import AgentDefinition, AgentSession, AgentType, AgentStatus
from api.ai.agents.image.schemas import (
    ImageGenerateRequest, ImageEditRequest, ImageVariationRequest,
    ImageUpscaleRequest, ImageBackgroundRemoveRequest, ImageBackgroundReplaceRequest,
    ImageInpaintRequest, ImageOutpaintRequest, ImageResponse,
    ImageLibraryItemResponse, ImageProviderResponse, ImageModelResponse,
    CollectionCreateRequest, CollectionResponse, BulkActionRequest
)
from api.ai.agents.image.service import ImageAgentService
from api.ai.agents.image.executor import ImageExecutor
from api.ai.agents.image.history import AIImageLibrary, AIImageCollection
from api.ai.agents.image.constants import DEFAULT_PROVIDER_PRIORITY, SUPPORTED_MODELS, ASPECT_RATIOS

router = APIRouter(prefix="/image", tags=["image-agent"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


def _resolve_image_session(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> AgentSession:
    """Finds or creates the persistent session dedicated to the Image Studio agent."""
    agent = db.scalars(
        select(AgentDefinition).where(
            AgentDefinition.organization_id == org_id,
            AgentDefinition.agent_type == AgentType.IMAGE,
            AgentDefinition.status == AgentStatus.ACTIVE,
        )
    ).first()

    if not agent:
        agent = AgentDefinition(
            name="Image Creative Agent Studio",
            description="Flagship Enterprise Visual Designer & Layout Editor Agent",
            agent_type=AgentType.IMAGE,
            status=AgentStatus.ACTIVE,
            allowed_tools=["image_generate_tool", "image_edit_tool", "image_upscale_tool"],
            organization_id=org_id,
            memory_enabled=True,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

    session = db.scalars(
        select(AgentSession).where(
            AgentSession.agent_id == agent.id,
            AgentSession.organization_id == org_id,
            AgentSession.is_active == True,
        )
    ).first()

    if not session:
        session = AgentSession(
            agent_id=agent.id,
            user_id=user_id,
            organization_id=org_id,
            title="Image Studio Creative Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    return session


def _resolve_image_session_by_id(db: Session, org_id: uuid.UUID, user_id: uuid.UUID, agent_id: Optional[uuid.UUID] = None) -> AgentSession:
    if not agent_id:
        return _resolve_image_session(db, org_id, user_id)
        
    session = db.scalars(
        select(AgentSession).where(
            AgentSession.agent_id == agent_id,
            AgentSession.organization_id == org_id,
            AgentSession.is_active == True,
        )
    ).first()
    
    if not session:
        session = AgentSession(
            agent_id=agent_id,
            user_id=user_id,
            organization_id=org_id,
            title="Image Studio Creative Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
    return session


@router.post("/generate", response_model=ImageResponse, status_code=status.HTTP_200_OK)
def generate_image_sync(
    payload: ImageGenerateRequest,
    background: bool = Query(False, description="Run generation task in background queue asynchronously."),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Synchronous or asynchronous visual layout asset compilation."""
    session = _resolve_image_session_by_id(db, membership.organization_id, membership.user_id, payload.agent_id)

    if background:
        # Create queued record
        library_item = AIImageLibrary(
            prompt=payload.prompt,
            negative_prompt=payload.negative_prompt,
            provider="pending",
            model=payload.model or "flux",
            seed=payload.seed,
            cfg_scale=payload.cfg_scale,
            steps=payload.steps,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            campaign_id=payload.campaign_id,
            storage_url="",
            status="QUEUED",
            version=1
        )
        db.add(library_item)
        db.commit()
        db.refresh(library_item)

        # Trigger background Celery worker
        from api.worker.celery_app import generate_image_task
        generate_image_task.delay(str(library_item.id))

        return ImageResponse(
            id=str(library_item.id),
            storage_url="",
            provider="pending",
            model=payload.model or "flux",
            prompt=payload.prompt,
            compiled_prompt="",
            reflection={},
            evaluation={}
        )

    # Sync flow
    return ImageAgentService.generate_sync(
        db=db,
        session=session,
        prompt=payload.prompt,
        style=payload.style,
        aspect_ratio=payload.aspect_ratio,
        negative_prompt=payload.negative_prompt,
        campaign_id=payload.campaign_id,
        knowledge_collections=payload.knowledge_collections,
        model=payload.model,
        seed=payload.seed,
        steps=payload.steps,
        cfg_scale=payload.cfg_scale
    )


@router.post("/generate/stream")
def generate_image_stream(
    payload: ImageGenerateRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> StreamingResponse:
    """Streamed Server-Sent Events (SSE) layout timelines generator."""
    session = _resolve_image_session_by_id(db, membership.organization_id, membership.user_id, payload.agent_id)
    generator = ImageAgentService.generate_stream(
        db=db,
        session=session,
        prompt=payload.prompt,
        style=payload.style,
        aspect_ratio=payload.aspect_ratio,
        negative_prompt=payload.negative_prompt,
        campaign_id=payload.campaign_id,
        knowledge_collections=payload.knowledge_collections,
        model=payload.model,
        seed=payload.seed,
        steps=payload.steps,
        cfg_scale=payload.cfg_scale
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/edit", response_model=ImageResponse)
def edit_image(
    payload: ImageEditRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.edit(
        image_url=payload.image_url,
        prompt=payload.prompt,
        mask_url=payload.mask_url,
        style=payload.style,
        model=payload.model
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt=res["prompt"],
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/variation", response_model=ImageResponse)
def create_variation(
    payload: ImageVariationRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.variation(
        image_url=payload.image_url,
        style=payload.style,
        model=payload.model
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt="Visual variation",
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/upscale", response_model=ImageResponse)
def upscale_image(
    payload: ImageUpscaleRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.upscale(
        image_url=payload.image_url,
        scale=payload.scale or 2.0
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt="Upscaled image",
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/background/remove", response_model=ImageResponse)
def remove_background(
    payload: ImageBackgroundRemoveRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.remove_background(image_url=payload.image_url)
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt="Remove background",
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/background/replace", response_model=ImageResponse)
def replace_background(
    payload: ImageBackgroundReplaceRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.replace_background(
        image_url=payload.image_url,
        background_prompt=payload.background_prompt
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt=f"Replace background with: {payload.background_prompt}",
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/inpaint", response_model=ImageResponse)
def inpaint_image(
    payload: ImageInpaintRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.inpaint(
        image_url=payload.image_url,
        mask_url=payload.mask_url,
        prompt=payload.prompt
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt=payload.prompt,
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.post("/outpaint", response_model=ImageResponse)
def outpaint_image(
    payload: ImageOutpaintRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    executor = ImageExecutor(db, membership.organization_id, membership.user_id)
    res = executor.outpaint(
        image_url=payload.image_url,
        mask_url=payload.mask_url,
        prompt=payload.prompt
    )
    return ImageResponse(
        id=res["id"],
        storage_url=res["storage_url"],
        provider=res["provider"],
        model=res["model"],
        prompt=payload.prompt,
        compiled_prompt="",
        reflection={},
        evaluation={}
    )


@router.get("/history", response_model=List[ImageLibraryItemResponse])
def get_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    collection_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """Fetch image library items matching filters."""
    query = select(AIImageLibrary).where(
        AIImageLibrary.organization_id == membership.organization_id,
        AIImageLibrary.soft_deleted_at.is_(None)
    )

    if collection_id:
        query = query.join(AIImageLibrary.collections).where(AIImageCollection.id == collection_id)
    if status:
        query = query.where(AIImageLibrary.status == status)
    if search:
        query = query.where(AIImageLibrary.prompt.ilike(f"%{search}%"))

    query = query.order_by(AIImageLibrary.created_at.desc()).limit(limit)
    return db.scalars(query).all()


@router.get("/library", response_model=List[ImageLibraryItemResponse])
def get_library(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Legacy alias matching history for the catalog browser."""
    return get_history(db=db, membership=membership)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    """Soft delete an image asset."""
    item = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id == id,
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")
    
    item.soft_deleted_at = datetime.datetime.utcnow()
    db.commit()
    return None


@router.post("/{id}/restore-soft", response_model=ImageLibraryItemResponse)
def restore_soft_delete(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Restore a soft-deleted image asset."""
    item = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id == id,
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")
    
    item.soft_deleted_at = None
    db.commit()
    db.refresh(item)
    return item


@router.get("/{id}/versions", response_model=List[ImageLibraryItemResponse])
def get_image_versions(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Retrieve lineage versions for an image."""
    item = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id == id,
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")
    
    parent_id = item.parent_id or item.id
    query = select(AIImageLibrary).where(
        AIImageLibrary.organization_id == membership.organization_id,
        or_(AIImageLibrary.id == parent_id, AIImageLibrary.parent_id == parent_id)
    ).order_by(AIImageLibrary.version.asc())
    return db.scalars(query).all()


@router.post("/collections", response_model=CollectionResponse)
def create_collection(
    payload: CollectionCreateRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Create a new collection folder."""
    col = AIImageCollection(
        name=payload.name,
        organization_id=membership.organization_id
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.get("/collections", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """List organization image collections."""
    query = select(AIImageCollection).where(AIImageCollection.organization_id == membership.organization_id)
    return db.scalars(query).all()


@router.post("/collections/{id}/add", status_code=status.HTTP_200_OK)
def add_to_collection(
    id: uuid.UUID,
    payload: BulkActionRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Add items to a collection."""
    col = db.scalars(
        select(AIImageCollection).where(
            AIImageCollection.id == id,
            AIImageCollection.organization_id == membership.organization_id
        )
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    items = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id.in_(payload.ids),
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).all()

    for item in items:
        if item not in col.images:
            col.images.append(item)
    db.commit()
    return {"success": True}


@router.post("/collections/{id}/remove", status_code=status.HTTP_200_OK)
def remove_from_collection(
    id: uuid.UUID,
    payload: BulkActionRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Remove items from a collection."""
    col = db.scalars(
        select(AIImageCollection).where(
            AIImageCollection.id == id,
            AIImageCollection.organization_id == membership.organization_id
        )
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    items = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id.in_(payload.ids),
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).all()

    for item in items:
        if item in col.images:
            col.images.remove(item)
    db.commit()
    return {"success": True}


@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_images(
    payload: BulkActionRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    """Bulk soft delete image assets."""
    items = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id.in_(payload.ids),
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).all()

    now = datetime.datetime.utcnow()
    for item in items:
        item.soft_deleted_at = now
    db.commit()
    return None


@router.post("/bulk-move", status_code=status.HTTP_200_OK)
def bulk_move_images(
    payload: BulkActionRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Bulk move images to a collection."""
    if not payload.target_collection_id:
        raise HTTPException(status_code=400, detail="Missing target_collection_id")

    col = db.scalars(
        select(AIImageCollection).where(
            AIImageCollection.id == payload.target_collection_id,
            AIImageCollection.organization_id == membership.organization_id
        )
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    items = db.scalars(
        select(AIImageLibrary).where(
            AIImageLibrary.id.in_(payload.ids),
            AIImageLibrary.organization_id == membership.organization_id
        )
    ).all()

    for item in items:
        if item not in col.images:
            col.images.append(item)
    db.commit()
    return {"success": True}


@router.get("/providers", response_model=List[ImageProviderResponse])
def get_providers(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Lists configuration and health state of image providers dynamically from registry."""
    import os
    from api.models.ai_platform import AIProvider
    from api.models.ai_registry import AIModelRegistry
    
    db_provs = db.query(AIProvider).all()
    models = db.query(AIModelRegistry).all()
    
    from api.routes.ai import resolve_provider_capabilities
    
    out = []
    for prov in db_provs:
        prov_name = prov.name.lower()
        caps = resolve_provider_capabilities(prov_name, models)
        
        if "Image Generation" in caps or prov_name in ("pollinations", "cloudflare", "replicate", "stability", "ideogram", "blackforestlabs", "fal"):
            has_key = False
            if prov_name == "pollinations":
                has_key = True
            elif prov.config and prov.config.get("api_key"):
                has_key = True
            else:
                env_var = f"{prov.name.upper()}_API_KEY"
                has_key = bool(os.getenv(env_var))
                
            out.append(
                ImageProviderResponse(
                    name=prov_name,
                    label=prov.name.capitalize(),
                    priority=prov.priority,
                    configured=prov.is_active and has_key
                )
            )
    return out


@router.get("/models", response_model=List[ImageModelResponse])
def get_models(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Lists supported layout generation models from the database registry."""
    from api.models.ai_registry import AIModelRegistry
    models_in_db = db.query(AIModelRegistry).filter(AIModelRegistry.supports_images == True).all()
    
    ratios = list(ASPECT_RATIOS.keys())
    out = []
    for m in models_in_db:
        out.append(
            ImageModelResponse(
                name=m.model_name,
                label=m.model_name.upper().replace("-", " ").replace("@CF/", "").replace("STABILITY-AI/", ""),
                provider=m.provider,
                supported_ratios=ratios
            )
        )
    return out
