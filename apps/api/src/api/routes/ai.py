import uuid
from typing import Any, List, Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.prompt import (
    Prompt, PromptCollection, PromptFolder,
    PromptTestCase, PromptEvaluation, PromptExecution
)
from api.models.conversation import Conversation
from api.models.message import Message
from api.services.llm import LLMGateway
from api.repositories.prompt import PromptRepository, CollectionRepository, FolderRepository
from api.services.prompt import (
    PromptService, VariableEngine, ExecutionService,
    EvaluationService, OptimizationService, ImportExportService,
    AnalyticsService, ShareService, FavoriteService
)
from api.services.knowledge import KnowledgeService
from api.schemas.ai import (
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    PromptCollectionCreate,
    PromptCollectionResponse,
    PromptFolderCreate,
    PromptFolderResponse,
    PromptTestCaseCreate,
    PromptTestCaseResponse,
    PromptEvaluationResponse,
    PromptExecuteRequest,
    PromptOptimizeRequest,
    PromptImportRequest,
    PromptShareRequest,
    PromptShareResponse,
    PromptBulkActionRequest,
    PromptSearchRequest,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    KnowledgeUploadRequest,
    DocumentChunkResponse,
    KnowledgeDocumentResponse,
    QuerySimilarChunksRequest,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
)

prompts_router = APIRouter(prefix="/ai/prompts", tags=["ai-prompts"])
conversations_router = APIRouter(prefix="/ai/conversations", tags=["ai-conversations"])
knowledge_router = APIRouter(prefix="/ai/knowledge", tags=["ai-knowledge"])
models_router = APIRouter(prefix="/ai/models", tags=["ai-models"])
routing_rules_router = APIRouter(prefix="/ai/routing-rules", tags=["ai-routing-rules"])
usage_router = APIRouter(prefix="/ai/usage", tags=["ai-usage"])
providers_router = APIRouter(prefix="/ai/providers", tags=["ai-providers"])
playground_router = APIRouter(prefix="/ai/playground", tags=["ai-playground"])
compare_router = APIRouter(prefix="/ai/compare", tags=["ai-compare"])
analytics_router = APIRouter(prefix="/ai/analytics", tags=["ai-analytics"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER, UserRole.GUEST])


@providers_router.get("/{provider_name}/models")
def list_provider_models(
    provider_name: str,
    membership: UserOrganization = Depends(active_member)
):
    models = [
        {"model_name": "llama3-70b-8192", "provider": "groq", "supports_streaming": True},
        {"model_name": "llama3-8b-8192", "provider": "groq", "supports_streaming": True},
        {"model_name": "mixtral-8x7b-32768", "provider": "groq", "supports_streaming": True},
        {"model_name": "gemini-1.5-flash", "provider": "google", "supports_streaming": True},
        {"model_name": "gemini-1.5-pro", "provider": "google", "supports_streaming": True},
        {"model_name": "gpt-4o", "provider": "openai", "supports_streaming": True},
    ]
    filtered = [m for m in models if m["provider"].lower() == provider_name.lower()]
    return filtered or models


# ==========================================
# PROMPT LIBRARY ENDPOINTS (BACKWARD COMPATIBILITY)
# ==========================================


@prompts_router.post(
    "/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED
)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.create_prompt_version(
        db=db,
        prompt_in=prompt_in,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@prompts_router.post(
    "/{name}/update", response_model=PromptResponse
)
def update_prompt(
    name: str,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.update_prompt_version(
        db=db,
        name=name,
        prompt_in=prompt_in,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@prompts_router.get("/", response_model=List[PromptResponse])
def list_prompts(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.list_latest_prompts(
        db=db, organization_id=membership.organization_id
    )


@prompts_router.post("/collections", response_model=PromptCollectionResponse)
def create_collection(
    col_in: PromptCollectionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.create_collection(
        db=db,
        name=col_in.name,
        description=col_in.description,
        organization_id=membership.organization_id,
        parent_id=col_in.parent_id,
        visibility=col_in.visibility or "ORGANIZATION",
        owner_id=membership.user_id
    )


@prompts_router.get("/collections", response_model=List[PromptCollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.list_collections(db=db, organization_id=membership.organization_id)


@prompts_router.post("/folders", response_model=PromptFolderResponse)
def create_folder(
    folder_in: PromptFolderCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.create_folder(
        db=db,
        name=folder_in.name,
        collection_id=folder_in.collection_id,
        organization_id=membership.organization_id,
        parent_id=folder_in.parent_id,
        owner_id=membership.user_id
    )


@prompts_router.get("/folders", response_model=List[PromptFolderResponse])
def list_folders(
    collection_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.list_folders(
        db=db,
        organization_id=membership.organization_id,
        collection_id=collection_id
    )


@prompts_router.post("/optimize")
def optimize_prompt(
    opt_in: PromptOptimizeRequest,
    membership: UserOrganization = Depends(active_member),
):
    return OptimizationService.analyze(content=opt_in.content)


@prompts_router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return AnalyticsService.get_dashboard_stats(db=db, organization_id=membership.organization_id)


@prompts_router.post("/import", response_model=List[PromptResponse])
def import_prompts(
    imp_in: PromptImportRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return ImportExportService.import_prompts(
        db=db,
        file_content=imp_in.file_content,
        format_type=imp_in.format_type,
        organization_id=membership.organization_id,
        user_id=membership.user_id
    )


@prompts_router.get("/export")
def export_prompts(
    format_type: str = "json",
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return ImportExportService.export_prompts(
        db=db, format_type=format_type, organization_id=membership.organization_id
    )


@prompts_router.get("/recent", response_model=List[PromptResponse])
def list_recent_prompts(
    limit: Optional[int] = 10,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    prompts, _ = PromptRepository.list_by_organization(
        db=db, organization_id=membership.organization_id, limit=limit or 10
    )
    return prompts


@prompts_router.post("/bulk-action")
def perform_bulk_action(
    req: PromptBulkActionRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    results = []
    for name in req.prompt_names:
        if req.action in ["archive", "delete"]:
            PromptService.soft_delete(db, name, membership.organization_id, user_id=membership.user_id)
            results.append({"name": name, "status": "archived"})
        elif req.action == "restore":
            PromptService.restore(db, name, membership.organization_id, user_id=membership.user_id)
            results.append({"name": name, "status": "restored"})
        elif req.action in ["purge", "permanent_delete"]:
            PromptService.permanent_delete(db, name, membership.organization_id, user_id=membership.user_id)
            results.append({"name": name, "status": "purged"})
        else:
            results.append({"name": name, "status": "processed"})
    return {"action": req.action, "results": results, "affected_count": len(results)}


@prompts_router.post("/search", response_model=List[PromptResponse])
def search_prompts(
    req: PromptSearchRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    prompts, _ = PromptRepository.search(
        db=db,
        organization_id=membership.organization_id,
        query=getattr(req, "query", None),
        category=getattr(req, "category", None),
        tag=getattr(req, "tag", None),
        folder_id=getattr(req, "folder_id", None),
        collection_id=getattr(req, "collection_id", None),
        status=getattr(req, "status", None),
        owner_id=getattr(req, "owner_id", None),
        is_archived=getattr(req, "is_archived", False) or False,
        skip=getattr(req, "skip", 0) or 0,
        limit=getattr(req, "limit", 50) or 50
    )
    return prompts


class PromptTestRequest(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: str
    model_name: str


@prompts_router.post("/test")
def test_prompt(
    req: PromptTestRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Runs a sandboxed prompt execution using the centralized AI Gateway."""
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    import time
    
    messages = [{"role": "user", "content": req.user_prompt}]
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    start_time = time.perf_counter()
    res = gateway.chat(
        db=db,
        messages=messages,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        model_name=req.model_name
    )
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    
    return {
        "output": res["content"],
        "provider": res.get("provider", "unknown"),
        "model": req.model_name,
        "tokens_used": res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        "cost_usd": float(res.get("cost_usd", 0.0)),
        "latency_ms": latency_ms
    }


@prompts_router.post("/test/stream")
def test_prompt_stream(
    req: PromptTestRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Streams a sandboxed prompt execution using the centralized AI Gateway."""
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    import json
    
    messages = [{"role": "user", "content": req.user_prompt}]
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    def sse_generator():
        try:
            chunks = gateway.stream(
                db=db,
                messages=messages,
                organization_id=membership.organization_id,
                user_id=membership.user_id,
                model_name=req.model_name
            )
            for chunk in chunks:
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@prompts_router.get("/shared/{token}", response_model=PromptResponse)
def get_shared_prompt(
    token: str,
    db: Session = Depends(get_db),
):
    return ShareService.get_shared_prompt(db=db, token=token)


@prompts_router.get("/{name}", response_model=PromptResponse)
def get_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.get_latest_prompt(
        db=db, name=name, organization_id=membership.organization_id
    )


@prompts_router.post("/{name}", response_model=PromptResponse)
@prompts_router.put("/{name}", response_model=PromptResponse)
def update_prompt(
    name: str,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.update_prompt_version(
        db=db,
        name=name,
        prompt_in=prompt_in,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@prompts_router.get("/{name}/history", response_model=List[PromptResponse])
def get_prompt_history(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.get_prompt_history(
        db=db, name=name, organization_id=membership.organization_id
    )


@prompts_router.delete("/{name}/purge", status_code=status.HTTP_204_NO_CONTENT)
def purge_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    PromptService.permanent_delete(
        db=db, name=name, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@prompts_router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    PromptService.soft_delete(
        db=db, name=name, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@prompts_router.delete("/{name}/permanent", status_code=status.HTTP_200_OK)
@prompts_router.delete("/{name}/purge", status_code=status.HTTP_200_OK)
def purge_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    PromptService.permanent_delete(
        db=db, name=name, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )
    return {"success": True}


@prompts_router.post("/{name}/rollback", response_model=PromptResponse)
def rollback_prompt(
    name: str,
    version: Optional[int] = Query(1, alias="target_version"),
    version_query: Optional[int] = Query(None, alias="version"),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    target = version_query or version or 1
    return PromptService.rollback_version(
        db=db,
        name=name,
        target_version=target,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@prompts_router.post("/{name}/restore", response_model=PromptResponse)
def restore_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.restore(
        db=db, name=name, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )


@prompts_router.post("/{name}/draft", response_model=PromptResponse)
def save_prompt_draft(
    name: str,
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.save_draft(
        db=db, name=name, prompt_in=prompt_in, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )


@prompts_router.post("/{name}/release", response_model=PromptResponse)
def release_prompt_version(
    name: str,
    release_notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.release_version(
        db=db, name=name, release_notes=release_notes, organization_id=membership.organization_id, user_id=membership.user_id, user_role=str(membership.role)
    )




@prompts_router.post("/{name}/duplicate", response_model=PromptResponse)
@prompts_router.post("/{name}/clone", response_model=PromptResponse)
def clone_prompt(
    name: str,
    new_name: str = Query(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.duplicate_prompt(
        db=db,
        name=name,
        new_name=new_name,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        user_role=str(membership.role)
    )


@prompts_router.post("/{name}/share", response_model=PromptShareResponse)
def share_prompt(
    name: str,
    req: PromptShareRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return ShareService.share_prompt(
        db=db,
        prompt_name=name,
        share_in=req,
        organization_id=membership.organization_id,
        user_id=membership.user_id
    )


@prompts_router.get("/{name}/diff")
def get_unified_diff(
    name: str,
    version_a: int = 1,
    version_b: int = 2,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return PromptService.compute_diff(
        db=db, name=name, version_a=version_a, version_b=version_b, organization_id=membership.organization_id
    )


@prompts_router.post("/{name}/execute")
def execute_prompt(
    name: str,
    exec_in: PromptExecuteRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    return ExecutionService.execute_prompt_template(
        db=db,
        prompt_name=name,
        variables=exec_in.variables or {},
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        version=exec_in.version,
        model_name=exec_in.model_name,
        system_prompt=exec_in.system_prompt,
        rag_enabled=exec_in.rag_enabled or False,
        temperature=exec_in.temperature or 0.7
    )


@prompts_router.post("/{name}/stream")
def stream_prompt(
    name: str,
    exec_in: PromptExecuteRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    def event_generator():
        res = ExecutionService.execute_prompt_template(
            db=db,
            prompt_name=name,
            variables=exec_in.variables or {},
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            version=exec_in.version,
            model_name=exec_in.model_name,
            system_prompt=exec_in.system_prompt,
            rag_enabled=exec_in.rag_enabled or False,
            temperature=exec_in.temperature or 0.7
        )
        output_text = res.get("output", "")
        for chunk in output_text.split(" "):
            yield f"data: {json.dumps({'content': chunk + ' '})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@prompts_router.post("/{name}/testcases", response_model=PromptTestCaseResponse)
def create_test_case(
    name: str,
    tc_in: PromptTestCaseCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    prompt = PromptService.get_latest_prompt(db, name, membership.organization_id)
    prompt_id = prompt.id if prompt else None
    
    tc = PromptTestCase(
        prompt_id=prompt_id,
        name=tc_in.name,
        inputs=tc_in.inputs,
        expected_output=tc_in.expected_output,
        organization_id=membership.organization_id
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


@prompts_router.get("/{name}/testcases", response_model=List[PromptTestCaseResponse])
def list_test_cases(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    prompt = PromptService.get_latest_prompt(db, name, membership.organization_id)
    if not prompt:
        return []
    return list(
        db.scalars(
            select(PromptTestCase).where(
                and_(
                    PromptTestCase.prompt_id == prompt.id,
                    PromptTestCase.organization_id == membership.organization_id
                )
            )
        ).all()
    )


@prompts_router.post("/{name}/evaluate", response_model=List[PromptEvaluationResponse])
def evaluate_prompt(
    name: str,
    model_name: Optional[str] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
):
    prompt = PromptService.get_latest_prompt(db, name, membership.organization_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        
    test_cases = db.scalars(
        select(PromptTestCase).where(PromptTestCase.prompt_id == prompt.id)
    ).all()
    
    results = []
    for tc in test_cases:
        res = ExecutionService.execute(
            db=db,
            name=name,
            variables=tc.inputs,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            model_name=model_name
        )
        
        eval_result = EvaluationService.evaluate_run(
            db=db,
            prompt_id=prompt.id,
            test_case_id=tc.id,
            model_name=res["model"],
            actual_output=res["output"],
            expected_output=tc.expected_output,
            latency_ms=res["latency_ms"],
            tokens_used=res["tokens_used"],
            cost_usd=res["cost_usd"],
            organization_id=membership.organization_id
        )
        results.append(eval_result)
    return results





# ==========================================
# CONVERSATION HISTORY ENDPOINTS
# ==========================================


@conversations_router.post(
    "/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    conv = Conversation(
        title=conv_in.title,
        user_id=current_user.id,
        organization_id=membership.organization_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@conversations_router.get("/", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    return (
        db.query(Conversation)
        .filter(
            Conversation.organization_id == membership.organization_id,
            Conversation.user_id == current_user.id,
        )
        .all()
    )


@conversations_router.delete(
    "/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    db.delete(conv)
    db.commit()


@conversations_router.patch(
    "/{conversation_id}", response_model=ConversationResponse
)
def rename_conversation(
    conversation_id: uuid.UUID,
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    conv.title = conv_in.title
    db.commit()
    db.refresh(conv)
    return conv


@conversations_router.get(
    "/{conversation_id}/messages", response_model=List[MessageResponse]
)
def list_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Ensure conversation belongs to current organization
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@conversations_router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_message(
    conversation_id: uuid.UUID,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # 1. Verify conversation session context
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    # 2. Extract optional prompt instruction
    system_instruction = None
    if msg_in.prompt_id:
        prompt = (
            db.query(Prompt)
            .filter(
                Prompt.id == msg_in.prompt_id,
                Prompt.organization_id == membership.organization_id,
            )
            .first()
        )
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Applied prompt template does not exist inside this organization.",
            )
        system_instruction = prompt.content
    elif msg_in.system_prompt:
        system_instruction = msg_in.system_prompt

    # 3. Log user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=msg_in.content,
        model_used=msg_in.model_name,
    )
    db.add(user_msg)
    db.commit()

    # 4. Fetch session history to construct chat payload
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    messages_payload = []
    if system_instruction:
        messages_payload.append({"role": "system", "content": system_instruction})
    for h in history:
        messages_payload.append({"role": h.role, "content": h.content})

    # 5. Trigger AI Gateway 2.0 Orchestrator
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    res = gateway.chat(
        db=db,
        messages=messages_payload,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        rag_enabled=msg_in.rag_enabled,
        model_name=msg_in.model_name,
    )

    # 6. Log assistant response with full telemetry metrics
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=res["content"],
        model_used=res.get("model", msg_in.model_name),
        provider_used=res.get("provider"),
        latency_ms=res.get("latency_ms"),
        prompt_tokens=res.get("prompt_tokens"),
        completion_tokens=res.get("completion_tokens"),
        cost_usd=res.get("cost_usd"),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


from api.routes.knowledge import router as knowledge_router


# ==========================================
# MODEL REGISTRY, ROUTING & USAGE ENDPOINTS
# ==========================================

from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.ai.registry.manager import ModelRegistryManager
from api.schemas.ai import (
    ModelRegistryResponse,
    ModelRegistryUpdate,
    RoutingRuleResponse,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    TokenUsageResponse,
)
from sqlalchemy import select, delete
import random
import datetime
from datetime import timedelta
from decimal import Decimal

models_router = APIRouter(prefix="/ai/models", tags=["ai-models"])
routing_rules_router = APIRouter(prefix="/ai/routing-rules", tags=["ai-routing-rules"])
usage_router = APIRouter(prefix="/ai/usage", tags=["ai-usage"])


@models_router.get("/", response_model=List[ModelRegistryResponse])
def list_models(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Auto-seed standard models if registry is empty
    ModelRegistryManager.seed_default_models(db)
    models = db.scalars(
        select(AIModelRegistry)
        .where(
            (AIModelRegistry.organization_id == None) | 
            (AIModelRegistry.organization_id == membership.organization_id)
        )
        .order_by(AIModelRegistry.provider.asc(), AIModelRegistry.priority.desc())
    ).all()
    return models


@models_router.patch("/{model_id}", response_model=ModelRegistryResponse)
def update_model(
    model_id: uuid.UUID,
    model_in: ModelRegistryUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    model = db.scalars(
        select(AIModelRegistry)
        .where(
            AIModelRegistry.id == model_id,
            (AIModelRegistry.organization_id == None) |
            (AIModelRegistry.organization_id == membership.organization_id)
        )
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found in registry",
        )
    
    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
        
    db.commit()
    db.refresh(model)
    return model


@routing_rules_router.get("/", response_model=List[RoutingRuleResponse])
def list_routing_rules(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Make sure default models are seeded so routing rules exist
    ModelRegistryManager.seed_default_models(db)
    rules = db.scalars(
        select(AIRoutingRule)
        .where(
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).all()
    return rules


@routing_rules_router.post("/", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    rule_in: RoutingRuleCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify model exists
    model = db.scalars(
        select(AIModelRegistry).where(AIModelRegistry.id == rule_in.model_registry_id)
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target model registry ID does not exist"
        )
    
    rule = AIRoutingRule(
        request_type=rule_in.request_type,
        model_registry_id=rule_in.model_registry_id,
        is_active=rule_in.is_active,
        organization_id=membership.organization_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@routing_rules_router.patch("/{rule_id}", response_model=RoutingRuleResponse)
def update_routing_rule(
    rule_id: uuid.UUID,
    rule_in: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    rule = db.scalars(
        select(AIRoutingRule)
        .where(
            AIRoutingRule.id == rule_id,
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )
    
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
        
    db.commit()
    db.refresh(rule)
    return rule


@routing_rules_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    rule = db.scalars(
        select(AIRoutingRule)
        .where(
            AIRoutingRule.id == rule_id,
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )
    db.delete(rule)
    db.commit()


def seed_dummy_usages(db: Session, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
    # Check if there is any usage logged for this org
    existing = db.scalars(
        select(AITokenUsage).where(AITokenUsage.organization_id == organization_id)
    ).first()
    if existing:
        return
        
    # Generate mock logs over the last 14 days
    now = datetime.datetime.now(datetime.timezone.utc)
    models_sample = [
        {"provider": "openai", "model": "gpt-4o-mini", "in_cost": 0.00015, "out_cost": 0.0006},
        {"provider": "openai", "model": "gpt-4o", "in_cost": 0.005, "out_cost": 0.015},
        {"provider": "groq", "model": "llama3-70b-8192", "in_cost": 0.00059, "out_cost": 0.00079},
        {"provider": "groq", "model": "llama3-8b-8192", "in_cost": 0.00005, "out_cost": 0.0001},
        {"provider": "google", "model": "gemini-1.5-flash", "in_cost": 0.000075, "out_cost": 0.0003},
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "in_cost": 0.003, "out_cost": 0.015},
    ]
    
    statuses = ["success"] * 90 + ["failure"] * 10
    error_messages = ["Rate limit exceeded", "Context window overflow", "Provider connection timed out", "Internal server error"]
    
    for i in range(120):
        # random date in last 14 days
        days_ago = random.randint(0, 13)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        created_time = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
        
        m = random.choice(models_sample)
        prompt_t = random.randint(100, 4000)
        compl_t = random.randint(50, 2000)
        cost = Decimal(prompt_t * m["in_cost"] / 1000 + compl_t * m["out_cost"] / 1000)
        latency = random.randint(80, 2500) if m["provider"] == "groq" else random.randint(400, 4000)
        
        status_val = random.choice(statuses)
        err = random.choice(error_messages) if status_val == "failure" else None
        
        usage = AITokenUsage(
            organization_id=organization_id,
            user_id=user_id,
            provider=m["provider"],
            model_name=m["model"],
            prompt_tokens=prompt_t,
            completion_tokens=compl_t,
            total_tokens=prompt_t + compl_t,
            cost_usd=cost,
            latency_ms=latency,
            status=status_val,
            error_message=err,
        )
        # Override the server default created_at
        usage.created_at = created_time
        db.add(usage)
        
    db.commit()


@usage_router.get("/", response_model=List[TokenUsageResponse])
def list_usage(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Seed mock usage data for better analytics display if empty
    seed_dummy_usages(db, membership.organization_id, membership.user_id)
    
    usages = db.scalars(
        select(AITokenUsage)
        .where(AITokenUsage.organization_id == membership.organization_id)
        .order_by(AITokenUsage.created_at.desc())
    ).all()
    return usages


# ==========================================
# ENTERPRISE AI GATEWAY & PLATFORM ROUTERS
# ==========================================

from api.models.ai_platform import (
    AIProvider, AIModel, AIProviderKey, AIProviderHealth,
    AIRequest, AIUsage, AICost, AIPlaygroundSession, AIPlaygroundMessage,
    AIOrgLimit
)
from api.core.encryption import encrypt_key, decrypt_key
from pydantic import BaseModel
from api.schemas.ai import (
    ProviderResponse, ProviderCreate, ProviderUpdate, ProviderHealthResponse,
    PlaygroundChatRequest, CompareRequest, CompareResponse, CompareResponseElement,
    RouterSettingsResponse, RouterSettingsUpdate
)
import httpx
import os
import time
import json
from fastapi.responses import StreamingResponse

providers_router = APIRouter(prefix="/ai/providers", tags=["ai-providers"])
playground_router = APIRouter(prefix="/ai/playground", tags=["ai-playground"])
compare_router = APIRouter(prefix="/ai/compare", tags=["ai-compare"])
router_settings_router = APIRouter(prefix="/ai/router", tags=["ai-router"])
analytics_router = APIRouter(prefix="/ai/analytics", tags=["ai-analytics"])


def sync_providers_and_models(db: Session) -> None:
    """
    Synchronize dynamic list of providers and models in PostgreSQL.
    """
    from sqlalchemy import text
    try:
        db.execute(text("ALTER TABLE ai_providers ADD COLUMN IF NOT EXISTS config JSONB"))
        db.commit()
    except Exception:
        try:
            db.execute(text("ALTER TABLE ai_providers ADD COLUMN config JSON"))
            db.commit()
        except Exception:
            pass

    try:
        db.execute(text("ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS supports_images BOOLEAN DEFAULT FALSE"))
        db.commit()
    except Exception:
        try:
            db.execute(text("ALTER TABLE ai_models ADD COLUMN supports_images BOOLEAN"))
            db.commit()
        except Exception:
            pass

    try:
        db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0"))
        db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN IF NOT EXISTS capability VARCHAR(50) DEFAULT 'text'"))
        db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN IF NOT EXISTS agent VARCHAR(100)"))
        db.commit()
    except Exception:
        try:
            db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN retry_count INTEGER"))
            db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN capability VARCHAR(50)"))
            db.execute(text("ALTER TABLE ai_token_usages ADD COLUMN agent VARCHAR(100)"))
            db.commit()
        except Exception:
            pass

    provider_names = ["groq", "openai", "anthropic", "google", "openrouter", "deepseek", "mistral", "ollama", "cloudflare", "pollinations", "replicate", "together", "fal", "stability", "ideogram", "blackforestlabs"]
    providers = {}
    for name in provider_names:
        prov = db.query(AIProvider).filter(AIProvider.name == name).first()
        if not prov:
            prov = AIProvider(name=name, is_active=True, priority=1, config={})
            db.add(prov)
            db.flush()
        providers[name] = prov
    db.commit()

    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_models = []
    if groq_api_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {groq_api_key}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    for m in data.get("data", []):
                        m_id = m.get("id")
                        if m_id:
                            groq_models.append(m_id)
        except Exception:
            pass

    if not groq_models:
        groq_models = [
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

    # Seed defaults inside ModelRegistry
    ModelRegistryManager.seed_default_models(db)

    registry_models = {model.model_name: model for model in db.query(AIModelRegistry).all()}
    
    # Register Groq models if not present
    for model_name in groq_models:
        if model_name in registry_models:
            continue
        reg = AIModelRegistry(
            provider="groq",
            model_name=model_name,
            context_window=131072 if "70b" in model_name or model_name == "openai/gpt-oss-120b" else 8192,
            supports_streaming=True,
            supports_json=True,
            supports_images=False,
            input_token_price=Decimal("0.0000"),
            output_token_price=Decimal("0.0000"),
            latency=Decimal("0.20"),
            priority=8,
            is_healthy=True,
        )
        db.add(reg)
        registry_models[model_name] = reg

    # Seed additional models in AIModelRegistry
    new_provider_models = [
        {"provider": "deepseek", "model_name": "deepseek-chat", "context_window": 64000, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 10},
        {"provider": "deepseek", "model_name": "deepseek-reasoner", "context_window": 64000, "supports_streaming": True, "supports_json": False, "supports_images": False, "priority": 10},
        {"provider": "mistral", "model_name": "mistral-large-latest", "context_window": 32000, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 9},
        {"provider": "mistral", "model_name": "open-mixtral-8x22b", "context_window": 64000, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 8},
        {"provider": "ollama", "model_name": "llama3", "context_window": 8192, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 7},
        {"provider": "ollama", "model_name": "mistral", "context_window": 8192, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 7},
        # Cloudflare Workers AI
        {"provider": "cloudflare", "model_name": "@cf/stabilityai/stable-diffusion-xl-base-1.0", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 6},
        {"provider": "cloudflare", "model_name": "@cf/meta/llama-3-8b-instruct", "context_window": 8192, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 5},
        # Pollinations
        {"provider": "pollinations", "model_name": "flux-schnell", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 8},
        {"provider": "pollinations", "model_name": "flux-dev", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 7},
        {"provider": "pollinations", "model_name": "sdxl", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 6},
        # Other multi-modal
        {"provider": "replicate", "model_name": "replicate/flux-1.1-pro", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 5},
        {"provider": "together", "model_name": "togethercomputer/llama-2-70b-chat", "context_window": 4096, "supports_streaming": True, "supports_json": True, "supports_images": False, "priority": 5},
        {"provider": "stability", "model_name": "stable-diffusion-xl", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 5},
        {"provider": "ideogram", "model_name": "ideogram-v1", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 5},
        {"provider": "blackforestlabs", "model_name": "flux-pro", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 5},
        {"provider": "fal", "model_name": "fal-ai/flux/schnell", "context_window": 0, "supports_streaming": False, "supports_json": False, "supports_images": True, "priority": 5},
    ]
    for pm in new_provider_models:
        if pm["model_name"] in registry_models:
            continue
        reg = AIModelRegistry(
            provider=pm["provider"],
            model_name=pm["model_name"],
            context_window=pm["context_window"],
            supports_streaming=pm["supports_streaming"],
            supports_json=pm["supports_json"],
            supports_images=pm["supports_images"],
            input_token_price=Decimal("0.0000"),
            output_token_price=Decimal("0.0000"),
            latency=Decimal("0.30"),
            priority=pm["priority"],
            is_healthy=True,
        )
        db.add(reg)
        registry_models[pm["model_name"]] = reg

    db.commit()

    # Sync default registry entries to new ai_models table
    for reg_model in db.query(AIModelRegistry).all():
        m = db.query(AIModel).filter(AIModel.model_name == reg_model.model_name).first()
        if not m:
            prov = providers.get(reg_model.provider)
            if prov:
                m = AIModel(
                    provider_id=prov.id,
                    model_name=reg_model.model_name,
                    context_window=reg_model.context_window,
                    input_token_price=reg_model.input_token_price,
                    output_token_price=reg_model.output_token_price,
                    supports_streaming=reg_model.supports_streaming,
                    supports_vision=reg_model.supports_vision,
                    supports_tools=reg_model.supports_tool_calling,
                    supports_json=reg_model.supports_json,
                    supports_images=reg_model.supports_images,
                    is_active=True
                )
                db.add(m)
    db.commit()


def resolve_provider_capabilities(provider_name: str, models: list) -> list:
    caps = []
    # Check multi-modal registry first
    from api.ai.providers.base_provider import ProviderRegistry
    provider_instance = ProviderRegistry.get_provider(provider_name)
    if provider_instance:
        caps_dict = provider_instance.capabilities()
        for k, v in caps_dict.items():
            if v and k.startswith("supports_"):
                cap_name = k.replace("supports_", "")
                if cap_name == "generation":
                    caps.append("Image Generation")
                elif cap_name == "editing":
                    caps.append("Image Editing")
                elif cap_name == "variation":
                    caps.append("Image Variations")
                elif cap_name == "upscale":
                    caps.append("Image Upscaling")
                else:
                    caps.append(cap_name.capitalize())
    
    # Also check database model capabilities
    prov_models = [m for m in models if m.provider == provider_name]
    if any(m.supports_streaming for m in prov_models) or (prov_models and not caps):
        if "Text" not in caps: caps.append("Text")
        if "Chat" not in caps: caps.append("Chat")
        if "Streaming" not in caps: caps.append("Streaming")
    if any(m.supports_vision for m in prov_models):
        if "Vision" not in caps: caps.append("Vision")
    if any(m.supports_json for m in prov_models):
        if "JSON" not in caps: caps.append("JSON")
    if any(m.supports_images for m in prov_models):
        if "Image Generation" not in caps: caps.append("Image Generation")
    if any(m.supports_embeddings for m in prov_models):
        if "Embeddings" not in caps: caps.append("Embeddings")
        
    return list(set(caps))


@providers_router.get("/")
def get_providers(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sync_providers_and_models(db)
    provs = db.query(AIProvider).order_by(AIProvider.priority.desc()).all()
    models = db.query(AIModelRegistry).all()
    
    # Fetch recent usage records to calculate statistics
    usages = db.query(AITokenUsage).filter(
        AITokenUsage.organization_id == membership.organization_id
    ).all()
    
    # Fetch organization default settings to append defaults badges
    from api.models.membership import OrganizationSettings
    settings_rows = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == membership.organization_id,
        OrganizationSettings.namespace == "ai"
    ).all()
    settings_dict = {row.key: row.value for row in settings_rows}
    
    out = []
    for prov in provs:
        prov_name = prov.name.lower()
        caps = resolve_provider_capabilities(prov_name, models)
        prov_models = [m.model_name for m in models if m.provider == prov_name]
        
        # Health check
        health_check = db.query(AIProviderHealth).filter(
            AIProviderHealth.provider_id == prov.id
        ).order_by(AIProviderHealth.last_checked.desc()).first()
        
        status = "Healthy" if prov.is_active else "Offline"
        latency = 0.0
        last_error = None
        last_checked = None
        
        if health_check:
            latency = float(health_check.latency)
            last_checked = health_check.last_checked.isoformat() if health_check.last_checked else None
            if not health_check.is_healthy:
                status = "Offline"
                last_error = health_check.error_message
                
        # Recent health stats
        recent_checks = db.query(AIProviderHealth).filter(
            AIProviderHealth.provider_id == prov.id
        ).order_by(AIProviderHealth.last_checked.desc()).limit(20).all()
        
        if recent_checks:
            successes = sum(1 for c in recent_checks if c.is_healthy)
            success_rate = (successes / len(recent_checks)) * 100.0
            failure_rate = 100.0 - success_rate
        else:
            success_rate = 100.0
            failure_rate = 0.0
            
        # Usage stats
        import datetime
        now = datetime.datetime.utcnow()
        today_start = now - datetime.timedelta(days=1)
        seven_days_start = now - datetime.timedelta(days=7)
        thirty_days_start = now - datetime.timedelta(days=30)
        
        def _get_naive_dt(u):
            val = getattr(u, "created_at", None) or now
            return val.replace(tzinfo=None) if val.tzinfo else val
            
        prov_usages = [u for u in usages if u.provider == prov_name]
        
        # Today
        today_usages = [u for u in prov_usages if _get_naive_dt(u) >= today_start]
        today_req = len(today_usages)
        today_tokens = sum(u.total_tokens for u in today_usages)
        today_cost = sum(float(u.cost_usd) for u in today_usages)
        
        # 7d
        seven_usages = [u for u in prov_usages if _get_naive_dt(u) >= seven_days_start]
        seven_req = len(seven_usages)
        seven_tokens = sum(u.total_tokens for u in seven_usages)
        seven_cost = sum(float(u.cost_usd) for u in seven_usages)
        
        # 30d
        thirty_usages = [u for u in prov_usages if _get_naive_dt(u) >= thirty_days_start]
        thirty_req = len(thirty_usages)
        thirty_tokens = sum(u.total_tokens for u in thirty_usages)
        thirty_cost = sum(float(u.cost_usd) for u in thirty_usages)
        
        # Determine defaults
        is_default = False
        default_for = []
        for k, v in settings_dict.items():
            if k.startswith("default_") and v == prov_name:
                is_default = True
                default_for.append(k.replace("default_", "").replace("_provider", "").capitalize())
                
        # Mask configuration values
        masked_config = {}
        if prov.config:
            for k, v in prov.config.items():
                if k in ("api_key", "secret_key") and v:
                    masked_config[k] = "sk-••••" + v[-4:] if len(v) > 4 else "sk-••••"
                else:
                    masked_config[k] = v

        out.append({
            "id": str(prov.id),
            "name": prov.name,
            "is_active": prov.is_active,
            "priority": prov.priority,
            "config": masked_config,
            "status": status,
            "latency": latency,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "last_error": last_error,
            "last_checked": last_checked,
            "supported_models": prov_models,
            "supported_capabilities": caps,
            "estimated_cost": 0.04,
            "is_default": is_default,
            "default_for": default_for,
            "usage": {
                "today": {"requests": today_req, "tokens": today_tokens, "cost": today_cost},
                "last_7_days": {"requests": seven_req, "tokens": seven_tokens, "cost": seven_cost},
                "last_30_days": {"requests": thirty_req, "tokens": thirty_tokens, "cost": thirty_cost}
            }
        })
        
    return out


@providers_router.get("/{provider_name}/models", response_model=List[ModelRegistryResponse])
def get_provider_models(
    provider_name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.registry.manager import ModelRegistryManager
    return ModelRegistryManager.list_models_by_provider(db=db, provider_name=provider_name)


@providers_router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(
    prov_in: ProviderCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    existing = db.query(AIProvider).filter(AIProvider.name == prov_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists.")
    prov = AIProvider(name=prov_in.name, is_active=prov_in.is_active, priority=prov_in.priority or 1, config={})
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov


@providers_router.put("/{id}", response_model=ProviderResponse)
def update_provider(
    id: uuid.UUID,
    prov_in: ProviderUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    
    update_data = prov_in.model_dump(exclude_unset=True)
    
    if "config" in update_data and update_data["config"]:
        from api.core.encryption import encrypt_key
        config = dict(prov.config or {})
        new_config = update_data["config"]
        
        # If API key is provided and is not masked, encrypt it!
        if "api_key" in new_config and new_config["api_key"] and not new_config["api_key"].startswith("sk-") and "********" not in new_config["api_key"]:
            new_config["api_key"] = encrypt_key(new_config["api_key"])
        elif "api_key" in new_config and (not new_config["api_key"] or new_config["api_key"].startswith("sk-") or "********" in new_config["api_key"]):
            if "api_key" in config:
                new_config["api_key"] = config["api_key"]
                
        if "secret_key" in new_config and new_config["secret_key"] and not new_config["secret_key"].startswith("sk-") and "********" not in new_config["secret_key"]:
            new_config["secret_key"] = encrypt_key(new_config["secret_key"])
        elif "secret_key" in new_config and (not new_config["secret_key"] or new_config["secret_key"].startswith("sk-") or "********" in new_config["secret_key"]):
            if "secret_key" in config:
                new_config["secret_key"] = config["secret_key"]
                
        config.update(new_config)
        prov.config = config
        del update_data["config"]
        
    for field, value in update_data.items():
        setattr(prov, field, value)
        
    db.commit()
    db.refresh(prov)
    return prov


@providers_router.post("/{id}/health-check")
def trigger_provider_health_check(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    
    prov_name_lower = prov.name.lower()
    
    # Run health check
    is_healthy = False
    error_message = None
    start_time = time.perf_counter()
    
    try:
        from api.ai.providers.base_provider import ProviderRegistry
        # If registered in visual/multi-modal registry
        if ProviderRegistry.get_provider_cls(prov_name_lower):
            provider_instance = ProviderRegistry.get_provider(prov_name_lower)
            if provider_instance:
                api_key = None
                if prov.config:
                    from api.core.encryption import decrypt_key
                    encrypted_key = prov.config.get("api_key")
                    if encrypted_key:
                        api_key = decrypt_key(encrypted_key)
                provider_instance.api_key = api_key or os.getenv(f"{prov.name.upper()}_API_KEY")
                is_healthy = provider_instance.health()
        else:
            from api.ai.gateway.coordinator import AIGateway
            gateway = AIGateway()
            adapter = gateway._get_provider_adapter(db, prov.name, membership.organization_id)
            if adapter:
                is_healthy = adapter.health()
    except Exception as e:
        error_message = str(e)
        
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    
    health_record = AIProviderHealth(
        provider_id=prov.id,
        latency=float(latency_ms),
        is_healthy=is_healthy,
        last_checked=datetime.datetime.utcnow(),
        error_message=error_message
    )
    db.add(health_record)
    db.commit()
    
    return {
        "provider_name": prov.name,
        "is_healthy": is_healthy,
        "latency": float(latency_ms),
        "last_checked": health_record.last_checked.isoformat(),
        "error_message": error_message
    }


@providers_router.get("/logs")
def get_execution_logs(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    provider: Optional[str] = Query(None),
    capability: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
) -> Any:
    query = select(AITokenUsage).where(
        AITokenUsage.organization_id == membership.organization_id
    )
    
    if provider:
        query = query.where(func.lower(AITokenUsage.provider) == provider.lower())
    if capability:
        query = query.where(func.lower(AITokenUsage.capability) == capability.lower())
    if status:
        query = query.where(func.lower(AITokenUsage.status) == status.lower())
        
    query = query.order_by(AITokenUsage.id.desc()).limit(limit)
    rows = db.scalars(query).all()
    
    from api.models.user import User
    from api.models.organization import Organization
    
    out = []
    for r in rows:
        user = db.query(User).filter(User.id == r.user_id).first()
        org = db.query(Organization).filter(Organization.id == r.organization_id).first()
        
        c = getattr(r, "capability", "text")
        retries = getattr(r, "retry_count", 0)
        agent = getattr(r, "agent", "system")
        
        out.append({
            "id": str(r.id),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "provider": r.provider,
            "model": r.model_name,
            "capability": c or "text",
            "latency": r.latency_ms,
            "cost": float(r.cost_usd),
            "status": r.status,
            "error": r.error_message,
            "retry_count": retries or 0,
            "agent": agent or "system",
            "user": user.full_name if user else "Unknown User",
            "organization": org.name if org else "Unknown Org"
        })
    return out


@providers_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    db.delete(prov)
    db.commit()


@providers_router.get("/{id}/health", response_model=ProviderHealthResponse)
def check_provider_health(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    adapter = gateway._get_provider_adapter(db, prov.name, membership.organization_id)
    
    is_healthy = False
    start_time = time.perf_counter()
    err_msg = None
    if adapter:
        try:
            is_healthy = adapter.health()
        except Exception as e:
            err_msg = str(e)
    latency = int((time.perf_counter() - start_time) * 1000)

    health = AIProviderHealth(
        provider_id=prov.id,
        latency=latency,
        is_healthy=is_healthy,
        last_checked=datetime.datetime.utcnow(),
        error_message=err_msg
    )
    db.add(health)
    db.commit()

    return {
        "provider_name": prov.name,
        "is_healthy": is_healthy,
        "latency": latency,
        "last_checked": datetime.datetime.utcnow(),
        "error_message": err_msg
    }


# ==============================================================================
# SCHEMAS AND ENDPOINTS FOR KEYS, INCIDENTS, BUDGETS, AND LIMITS (PHASE 1)
# ==============================================================================

class ProviderKeyResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    provider_name: str
    is_active: bool
    masked_key: str
    created_at: datetime.datetime
    user_id: Optional[uuid.UUID] = None
    level: Optional[str] = None # "user" or "organization"

    class Config:
        from_attributes = True

class ProviderKeyCreate(BaseModel):
    provider_id: uuid.UUID
    api_key: str
    is_active: Optional[bool] = True
    level: Optional[str] = "organization" # "user" or "organization"

class ProviderKeyRotate(BaseModel):
    api_key: str

class ProviderHealthLogResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    latency: int
    is_healthy: bool
    last_checked: datetime.datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class OrgCapLimitResponse(BaseModel):
    organization_id: uuid.UUID
    credit_limit: float
    credit_used: float
    rpm_limit: int
    tpm_limit: int

    class Config:
        from_attributes = True

class AddCreditsRequest(BaseModel):
    amount: float

class UpdateLimitsRequest(BaseModel):
    rpm_limit: int
    tpm_limit: int
    credit_limit: Optional[float] = None


@providers_router.get("/keys/", response_model=List[ProviderKeyResponse])
def get_provider_keys(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    keys = db.query(AIProviderKey).filter(
        (AIProviderKey.organization_id == membership.organization_id) &
        ((AIProviderKey.user_id == None) | (AIProviderKey.user_id == membership.user_id))
    ).all()
    
    result = []
    for k in keys:
        plain_key = ""
        try:
            plain_key = decrypt_key(k.api_key)
        except Exception:
            pass
        
        masked = "sk-*****"
        if len(plain_key) > 10:
            masked = f"{plain_key[:7]}*****{plain_key[-4:]}"
            
        result.append({
            "id": k.id,
            "provider_id": k.provider_id,
            "provider_name": k.provider_rel.name if k.provider_rel else "unknown",
            "is_active": k.is_active,
            "masked_key": masked,
            "created_at": k.created_at,
            "user_id": k.user_id,
            "level": "user" if k.user_id else "organization",
        })
    return result

@providers_router.post("/keys/", response_model=ProviderKeyResponse)
def create_or_update_provider_key(
    key_in: ProviderKeyCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == key_in.provider_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
        
    if key_in.level == "user":
        existing = db.query(AIProviderKey).filter(
            AIProviderKey.provider_id == key_in.provider_id,
            AIProviderKey.organization_id == membership.organization_id,
            AIProviderKey.user_id == membership.user_id
        ).first()
    else:
        existing = db.query(AIProviderKey).filter(
            AIProviderKey.provider_id == key_in.provider_id,
            AIProviderKey.organization_id == membership.organization_id,
            AIProviderKey.user_id == None
        ).first()
    
    encrypted = encrypt_key(key_in.api_key)
    
    if existing:
        existing.api_key = encrypted
        existing.is_active = key_in.is_active if key_in.is_active is not None else existing.is_active
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_key = AIProviderKey(
            provider_id=key_in.provider_id,
            organization_id=membership.organization_id,
            user_id=membership.user_id if key_in.level == "user" else None,
            api_key=encrypted,
            is_active=key_in.is_active if key_in.is_active is not None else True
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        target = new_key
        
    plain_key = key_in.api_key
    masked = f"{plain_key[:7]}*****{plain_key[-4:]}" if len(plain_key) > 10 else "sk-*****"
    
    return {
        "id": target.id,
        "provider_id": target.provider_id,
        "provider_name": prov.name,
        "is_active": target.is_active,
        "masked_key": masked,
        "created_at": target.created_at,
        "user_id": target.user_id,
        "level": "user" if target.user_id else "organization",
    }

@providers_router.post("/keys/{key_id}/rotate", response_model=ProviderKeyResponse)
def rotate_provider_key(
    key_id: uuid.UUID,
    rotate_in: ProviderKeyRotate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    key_rec = db.query(AIProviderKey).filter(
        AIProviderKey.id == key_id,
        AIProviderKey.organization_id == membership.organization_id,
        ((AIProviderKey.user_id == None) | (AIProviderKey.user_id == membership.user_id))
    ).first()
    if not key_rec:
        raise HTTPException(status_code=404, detail="Provider key record not found.")
        
    encrypted = encrypt_key(rotate_in.api_key)
    key_rec.api_key = encrypted
    db.commit()
    db.refresh(key_rec)
    
    plain_key = rotate_in.api_key
    masked = f"{plain_key[:7]}*****{plain_key[-4:]}" if len(plain_key) > 10 else "sk-*****"
    
    return {
        "id": key_rec.id,
        "provider_id": key_rec.provider_id,
        "provider_name": key_rec.provider_rel.name if key_rec.provider_rel else "unknown",
        "is_active": key_rec.is_active,
        "masked_key": masked,
        "created_at": key_rec.created_at,
        "user_id": key_rec.user_id,
        "level": "user" if key_rec.user_id else "organization",
    }

@providers_router.get("/health-logs", response_model=List[ProviderHealthLogResponse])
def get_provider_health_logs(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    logs = db.query(AIProviderHealth).order_by(AIProviderHealth.last_checked.desc()).limit(100).all()
    return logs

@providers_router.get("/health/incidents")
def get_provider_incidents(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    failures = db.query(AIProviderHealth).filter(
        AIProviderHealth.is_healthy == False
    ).order_by(AIProviderHealth.last_checked.desc()).limit(30).all()
    
    incidents = []
    for f in failures:
        newer_check = db.query(AIProviderHealth).filter(
            AIProviderHealth.provider_id == f.provider_id,
            AIProviderHealth.last_checked > f.last_checked
        ).order_by(AIProviderHealth.last_checked.asc()).first()
        
        resolved = newer_check.is_healthy if newer_check else False
        
        incidents.append({
            "id": str(f.id),
            "provider": f.provider_rel.name if f.provider_rel else "unknown",
            "timestamp": f.last_checked.isoformat(),
            "type": "Outage" if "timeout" in (f.error_message or "").lower() else "API Error",
            "message": f.error_message or "Connectivity failure.",
            "resolved": resolved,
        })
    return incidents

@providers_router.post("/health/incidents/{id}/resolve")
def resolve_health_incident(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    log_rec = db.query(AIProviderHealth).filter(AIProviderHealth.id == id).first()
    if not log_rec:
        raise HTTPException(status_code=404, detail="Incident record not found.")
    
    log_rec.is_healthy = True
    db.commit()
    return {"success": True}

@providers_router.get("/limits/orgs", response_model=List[OrgCapLimitResponse])
def list_orgs_limits(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limits = db.query(AIOrgLimit).all()
    return limits

@providers_router.get("/limits/current", response_model=OrgCapLimitResponse)
def get_current_org_limit(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    limit = db.query(AIOrgLimit).filter(
        AIOrgLimit.organization_id == membership.organization_id
    ).first()
    
    if not limit:
        limit = AIOrgLimit(
            organization_id=membership.organization_id,
            credit_limit=100.00,
            credit_used=0.000000,
            rpm_limit=60,
            tpm_limit=50000
        )
        db.add(limit)
        db.commit()
        db.refresh(limit)
        
    return limit

@providers_router.post("/limits/{org_id}/credits", response_model=OrgCapLimitResponse)
def add_credits_to_org(
    org_id: uuid.UUID,
    req: AddCreditsRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limit = db.query(AIOrgLimit).filter(AIOrgLimit.organization_id == org_id).first()
    if not limit:
        limit = AIOrgLimit(
            organization_id=org_id,
            credit_limit=req.amount,
            credit_used=0.000000,
            rpm_limit=60,
            tpm_limit=50000
        )
        db.add(limit)
    else:
        limit.credit_limit = float(Decimal(str(limit.credit_limit)) + Decimal(str(req.amount)))
        
    db.commit()
    db.refresh(limit)
    return limit

@providers_router.post("/limits/{org_id}/limits", response_model=OrgCapLimitResponse)
def update_org_limits(
    org_id: uuid.UUID,
    req: UpdateLimitsRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limit = db.query(AIOrgLimit).filter(AIOrgLimit.organization_id == org_id).first()
    if not limit:
        limit = AIOrgLimit(
            organization_id=org_id,
            credit_limit=req.credit_limit or 100.00,
            credit_used=0.000000,
            rpm_limit=req.rpm_limit,
            tpm_limit=req.tpm_limit
        )
        db.add(limit)
    else:
        limit.rpm_limit = req.rpm_limit
        limit.tpm_limit = req.tpm_limit
        if req.credit_limit is not None:
            limit.credit_limit = req.credit_limit
            
    db.commit()
    db.refresh(limit)
    return limit


@models_router.post("/sync")
def sync_models_endpoint(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sync_providers_and_models(db)
    return {"success": True, "message": "Successfully synchronized AI models."}


@models_router.put("/{id}", response_model=ModelRegistryResponse)
def put_model_details(
    id: uuid.UUID,
    is_favorite: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    m = db.query(AIModel).filter(AIModel.id == id).first()
    if not m:
        reg_model = db.query(AIModelRegistry).filter(AIModelRegistry.id == id).first()
        if reg_model:
            if is_active is not None:
                reg_model.is_healthy = is_active
            db.commit()
            db.refresh(reg_model)
            return reg_model
        raise HTTPException(status_code=404, detail="Model not found.")
    
    if is_favorite is not None:
        m.is_favorite = is_favorite
    if is_active is not None:
        m.is_active = is_active
    db.commit()
    db.refresh(m)
    return m


@playground_router.post("/chat")
def playground_chat(
    req: PlaygroundChatRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    messages = list(req.messages)
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    res = gateway.chat(
        db=db,
        messages=messages,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        temperature=req.temperature,
        model_name=req.model_name
    )
    
    session = AIPlaygroundSession(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        name=f"Chat via {req.model_name}",
        provider=res.get("provider", "unknown"),
        model=req.model_name,
        temperature=req.temperature,
        system_prompt=req.system_prompt
    )
    db.add(session)
    db.flush()
    
    for msg in req.messages:
        db.add(AIPlaygroundMessage(session_id=session.id, role=msg["role"], content=msg["content"]))
    db.add(AIPlaygroundMessage(session_id=session.id, role="assistant", content=res["content"]))
    db.commit()
    
    return {
        "output": res["content"],
        "provider": res.get("provider", "unknown"),
        "model": req.model_name,
        "tokens_used": res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        "cost_usd": float(res.get("cost_usd", 0.0)),
        "latency_ms": res.get("latency_ms", 0),
    }


@playground_router.post("/stream")
def playground_stream(
    req: PlaygroundChatRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    messages = list(req.messages)
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    def sse_generator():
        try:
            chunks = gateway.stream(
                db=db,
                messages=messages,
                organization_id=membership.organization_id,
                user_id=membership.user_id,
                temperature=req.temperature,
                model_name=req.model_name
            )
            for chunk in chunks:
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@playground_router.get("/history")
def get_playground_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sessions = (
        db.query(AIPlaygroundSession)
        .filter(AIPlaygroundSession.organization_id == membership.organization_id)
        .order_by(AIPlaygroundSession.created_at.desc())
        .limit(20)
        .all()
    )
    res = []
    for s in sessions:
        msgs = db.query(AIPlaygroundMessage).filter(AIPlaygroundMessage.session_id == s.id).order_by(AIPlaygroundMessage.created_at.asc()).all()
        res.append({
            "id": s.id,
            "name": s.name,
            "provider": s.provider,
            "model": s.model,
            "temperature": float(s.temperature),
            "system_prompt": s.system_prompt,
            "created_at": s.created_at,
            "messages": [{"role": m.role, "content": m.content} for m in msgs]
        })
    return res


class PlaygroundSessionCreate(BaseModel):
    name: str
    provider: str
    model: str
    temperature: float = 0.7
    system_prompt: Optional[str] = None


class PlaygroundSessionUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None


class PlaygroundMessageCreate(BaseModel):
    role: str
    content: str


@playground_router.get("/sessions")
def list_playground_sessions(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sessions = db.query(AIPlaygroundSession).filter(
        AIPlaygroundSession.organization_id == membership.organization_id,
        AIPlaygroundSession.user_id == membership.user_id
    ).order_by(AIPlaygroundSession.created_at.desc()).all()
    
    res = []
    for s in sessions:
        res.append({
            "id": s.id,
            "name": s.name,
            "provider": s.provider,
            "model": s.model,
            "temperature": float(s.temperature),
            "system_prompt": s.system_prompt,
            "created_at": s.created_at
        })
    return res


@playground_router.post("/sessions")
def create_playground_session(
    sess_in: PlaygroundSessionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sess = AIPlaygroundSession(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        name=sess_in.name,
        provider=sess_in.provider,
        model=sess_in.model,
        temperature=sess_in.temperature,
        system_prompt=sess_in.system_prompt
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


@playground_router.patch("/sessions/{session_id}")
def update_playground_session(
    session_id: uuid.UUID,
    sess_in: PlaygroundSessionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sess = db.query(AIPlaygroundSession).filter(
        AIPlaygroundSession.id == session_id,
        AIPlaygroundSession.organization_id == membership.organization_id
    ).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if sess_in.name is not None:
        sess.name = sess_in.name
    if sess_in.provider is not None:
        sess.provider = sess_in.provider
    if sess_in.model is not None:
        sess.model = sess_in.model
    if sess_in.temperature is not None:
        sess.temperature = sess_in.temperature
    if sess_in.system_prompt is not None:
        sess.system_prompt = sess_in.system_prompt
        
    db.commit()
    db.refresh(sess)
    return sess


@playground_router.delete("/sessions/{session_id}")
def delete_playground_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sess = db.query(AIPlaygroundSession).filter(
        AIPlaygroundSession.id == session_id,
        AIPlaygroundSession.organization_id == membership.organization_id
    ).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.delete(sess)
    db.commit()
    return {"success": True}


@playground_router.get("/sessions/{session_id}/messages")
def get_playground_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sess = db.query(AIPlaygroundSession).filter(
        AIPlaygroundSession.id == session_id,
        AIPlaygroundSession.organization_id == membership.organization_id
    ).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    msgs = db.query(AIPlaygroundMessage).filter(
        AIPlaygroundMessage.session_id == session_id
    ).order_by(AIPlaygroundMessage.created_at.asc()).all()
    
    return [{"role": m.role, "content": m.content} for m in msgs]


@playground_router.post("/sessions/{session_id}/messages")
def create_playground_message(
    session_id: uuid.UUID,
    msg_in: PlaygroundMessageCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sess = db.query(AIPlaygroundSession).filter(
        AIPlaygroundSession.id == session_id,
        AIPlaygroundSession.organization_id == membership.organization_id
    ).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    msg = AIPlaygroundMessage(
        session_id=session_id,
        role=msg_in.role,
        content=msg_in.content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router_settings_router.get("/", response_model=RouterSettingsResponse)
def get_router_settings(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.models.membership import OrganizationSettings
    settings_rows = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == membership.organization_id,
        OrganizationSettings.namespace == "ai"
    ).all()
    
    settings_dict = {row.key: row.value for row in settings_rows}
    
    def to_bool(val: Any) -> bool:
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)
        
    return {
        "routing_mode": settings_dict.get("routing_mode", "cheapest"),
        "fallback_provider": settings_dict.get("fallback_provider", "groq"),
        "is_active": to_bool(settings_dict.get("is_active", "true")),
        "default_text_provider": settings_dict.get("default_text_provider", "openai"),
        "default_image_provider": settings_dict.get("default_image_provider", "pollinations"),
        "default_video_provider": settings_dict.get("default_video_provider", "pollinations"),
        "default_audio_provider": settings_dict.get("default_audio_provider", "openai"),
        "default_speech_provider": settings_dict.get("default_speech_provider", "openai"),
        "default_embeddings_provider": settings_dict.get("default_embeddings_provider", "openai"),
        "default_vision_provider": settings_dict.get("default_vision_provider", "google"),
        "default_ocr_provider": settings_dict.get("default_ocr_provider", "google"),
        "default_moderation_provider": settings_dict.get("default_moderation_provider", "openai"),
        "default_multimodal_provider": settings_dict.get("default_multimodal_provider", "google")
    }


@router_settings_router.put("/", response_model=RouterSettingsResponse)
def update_router_settings(
    settings_in: RouterSettingsUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.models.membership import OrganizationSettings
    
    def set_setting(key: str, value: Any):
        if value is None:
            return
        row = db.query(OrganizationSettings).filter(
            OrganizationSettings.organization_id == membership.organization_id,
            OrganizationSettings.namespace == "ai",
            OrganizationSettings.key == key
        ).first()
        if row:
            row.value = str(value)
        else:
            row = OrganizationSettings(
                organization_id=membership.organization_id,
                namespace="ai",
                key=key,
                value=str(value)
            )
            db.add(row)

    fields = [
        "routing_mode", "fallback_provider", "is_active",
        "default_text_provider", "default_image_provider", "default_video_provider",
        "default_audio_provider", "default_speech_provider", "default_embeddings_provider",
        "default_vision_provider", "default_ocr_provider", "default_moderation_provider",
        "default_multimodal_provider"
    ]
    
    update_data = settings_in.model_dump(exclude_unset=True)
    for f in fields:
        if f in update_data:
            set_setting(f, update_data[f])
            
    db.commit()
    return get_router_settings(db, membership)


@compare_router.post("/", response_model=CompareResponse)
def compare_models(
    req: CompareRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    results = []
    category = getattr(req, "category", "text")
    
    for model_name in req.model_names:
        try:
            if category == "image":
                from api.ai.agents.image.provider_router import ImageProviderRouter
                image_router = ImageProviderRouter(db, membership.organization_id, membership.user_id)
                model_meta = db.query(AIModelRegistry).filter(AIModelRegistry.model_name == model_name).first()
                provider = model_meta.provider if model_meta else "pollinations"
                
                import time
                start_time = time.perf_counter()
                image_bytes, resolved_prov, resolved_model = image_router.generate_image(
                    prompt=req.prompt,
                    width=512,
                    height=512,
                    model=model_name
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                
                from api.ai.agents.image.asset_manager import AssetManager
                import uuid
                file_asset = AssetManager.save_image_asset(
                    db=db,
                    image_bytes=image_bytes,
                    filename=f"compare_creative_{uuid.uuid4().hex[:8]}.png",
                    organization_id=membership.organization_id
                )
                
                usage_record = AITokenUsage(
                    organization_id=membership.organization_id,
                    user_id=membership.user_id,
                    provider=resolved_prov,
                    model_name=resolved_model,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.04,
                    latency_ms=latency_ms,
                    status="success",
                    capability="image",
                    agent="compare_lab"
                )
                db.add(usage_record)
                db.commit()
                
                results.append({
                    "model_name": model_name,
                    "provider": resolved_prov,
                    "response": file_asset.storage_url,
                    "latency_ms": latency_ms,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost_usd": 0.04,
                    "status": "success"
                })
            else:
                messages = [{"role": "user", "content": req.prompt}]
                if req.system_prompt:
                    messages.insert(0, {"role": "system", "content": req.system_prompt})
                    
                import time
                start_time = time.perf_counter()
                res = gateway.chat(
                    db=db,
                    messages=messages,
                    organization_id=membership.organization_id,
                    user_id=membership.user_id,
                    model_name=model_name
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                
                usage_record = AITokenUsage(
                    organization_id=membership.organization_id,
                    user_id=membership.user_id,
                    provider=res.get("provider", "unknown"),
                    model_name=model_name,
                    prompt_tokens=res.get("prompt_tokens", 0),
                    completion_tokens=res.get("completion_tokens", 0),
                    total_tokens=res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
                    cost_usd=float(res.get("cost_usd", 0.0)),
                    latency_ms=latency_ms,
                    status="success",
                    capability="text",
                    agent="compare_lab"
                )
                db.add(usage_record)
                db.commit()
                
                results.append({
                    "model_name": model_name,
                    "provider": res.get("provider", "unknown"),
                    "response": res["content"],
                    "latency_ms": latency_ms,
                    "prompt_tokens": res.get("prompt_tokens", 0),
                    "completion_tokens": res.get("completion_tokens", 0),
                    "cost_usd": float(res.get("cost_usd", 0.0)),
                    "status": "success"
                })
        except Exception as e:
            results.append({
                "model_name": model_name,
                "provider": "unknown",
                "response": "",
                "latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
                "status": "failure",
                "error_message": str(e)
            })
            
    return {"results": results}


@analytics_router.get("/")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    seed_dummy_usages(db, membership.organization_id, membership.user_id)
    
    usages = db.scalars(
        select(AITokenUsage)
        .where(AITokenUsage.organization_id == membership.organization_id)
        .order_by(AITokenUsage.created_at.desc())
        .limit(200)
    ).all()
    
    total_cost = sum(float(u.cost_usd or 0.0) for u in usages)
    total_tokens = sum(u.total_tokens or 0 for u in usages)
    success_rate = (len([u for u in usages if u.status == "success"]) / len(usages) * 100) if usages else 100.0
    avg_latency = (sum(u.latency_ms or 0 for u in usages) / len(usages)) if usages else 0
    
    return {
        "kpis": {
            "total_requests": len(usages),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "success_rate": round(success_rate, 2),
            "avg_latency": round(avg_latency, 2)
        },
        "usages": [
            {
                "id": u.id,
                "provider": u.provider,
                "model_name": u.model_name,
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
                "total_tokens": u.total_tokens,
                "cost_usd": float(u.cost_usd or 0.0),
                "latency_ms": u.latency_ms,
                "status": u.status,
                "created_at": u.created_at
            }
            for u in usages
        ]
    }


