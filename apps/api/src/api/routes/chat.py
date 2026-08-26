import uuid
import os
import re
import shutil
import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.user import User
from api.models.membership import UserOrganization, UserRole
from api.models.conversation import Conversation
from api.models.message import Message
from api.models.chat_attachment import ChatAttachment
from api.models.chat_participant import ChatParticipant
from api.models.conversation_bookmark import ConversationBookmark
from api.models.conversation_share import ConversationShare
from api.models.file_asset import FileAsset
from api.repositories.conversation import conversation_repo, message_repo
from api.services.conversation import ConversationService
from api.schemas.chat import (
    ChatConversationCreate,
    ChatConversationUpdate,
    ChatConversationResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ConversationBookmarkResponse,
    ConversationShareCreate,
    ConversationShareResponse,
    ChatParticipantCreate,
    ChatParticipantResponse,
    ChatAttachmentResponse,
    ChatSearchHighlight,
    ChatSearchResponse,
    ChatAnalyticsResponse,
    ProviderUsageMetrics,
    ModelUsageMetrics,
    DailyCostCoordinate,
)

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

chat_router = APIRouter(prefix="/chat/conversations", tags=["chat-conversations"])


@chat_router.post(
    "/",
    response_model=ChatConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conv_in: ChatConversationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new conversation session."""
    title = conv_in.title
    if not title:
        title = f"Chat Session {datetime.datetime.now().strftime('%H:%M')}"

    return ConversationService.create_conversation(
        db=db,
        title=title,
        user_id=current_user.id,
        organization_id=membership.organization_id,
        temperature=conv_in.temperature,
        system_prompt=conv_in.system_prompt,
        model_name=conv_in.model_name or "openai/gpt-oss-120b",
        provider_name=conv_in.provider_name or "groq",
    )


@chat_router.get("/", response_model=List[ChatConversationResponse])
def list_conversations(
    tab: Optional[str] = "recent",  # recent, pinned, favorite, archived
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List conversations for active organization and user supporting tabs and collaboration."""
    participant_subquery = (
        db.query(ChatParticipant.conversation_id)
        .filter(ChatParticipant.user_id == current_user.id, ChatParticipant.deleted_at.is_(None))
        .subquery()
    )

    q = db.query(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Conversation.deleted_at.is_(None),
        (Conversation.user_id == current_user.id) | (Conversation.id.in_(select(participant_subquery)))
    )

    if query:
        q = q.filter(Conversation.title.ilike(f"%{query}%"))

    if tab == "pinned":
        q = q.filter(Conversation.is_pinned == True)
    elif tab == "favorite":
        q = q.filter(Conversation.is_favorite == True)
    elif tab == "archived":
        q = q.filter(Conversation.is_archived == True)
    else:
        # Default tab recent: exclude archived threads
        q = q.filter(Conversation.is_archived == False)

    q = q.order_by(Conversation.is_pinned.desc(), Conversation.created_at.desc())
    return q.offset(offset).limit(limit).all()


@chat_router.get("/bookmarks", response_model=List[ChatConversationResponse])
def list_bookmarked_conversations(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all bookmarked conversations for the current user."""
    return (
        db.query(Conversation)
        .join(ConversationBookmark, ConversationBookmark.conversation_id == Conversation.id)
        .filter(
            ConversationBookmark.user_id == current_user.id,
            Conversation.organization_id == membership.organization_id,
            Conversation.deleted_at.is_(None)
        )
        .all()
    )


@chat_router.get("/analytics", response_model=ChatAnalyticsResponse)
def get_chat_analytics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Retrieve aggregate telemetry and usage metrics for chat dashboard."""
    total_convs = db.query(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Conversation.deleted_at.is_(None)
    ).count()

    total_msgs = db.query(Message).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.deleted_at.is_(None)
    ).count()

    active_users = db.query(Conversation.user_id).filter(
        Conversation.organization_id == membership.organization_id,
        Conversation.deleted_at.is_(None)
    ).distinct().count()

    avg_tokens = db.query(func.avg(Message.total_tokens)).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.role == "assistant",
        Message.deleted_at.is_(None)
    ).scalar() or 0.0

    avg_cost = db.query(func.avg(Message.cost_usd)).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.role == "assistant",
        Message.deleted_at.is_(None)
    ).scalar() or 0.0

    avg_latency = db.query(func.avg(Message.latency_ms)).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.role == "assistant",
        Message.deleted_at.is_(None)
    ).scalar() or 0.0

    # Provider Stats
    provider_stats = db.query(
        Message.provider_used,
        func.sum(Message.total_tokens),
        func.sum(Message.cost_usd)
    ).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.role == "assistant",
        Message.deleted_at.is_(None),
        Message.provider_used.is_not(None)
    ).group_by(Message.provider_used).all()

    total_tokens_sum = sum(stat[1] or 0 for stat in provider_stats) or 1
    provider_usage = []
    for stat in provider_stats:
        p_name, tokens, cost = stat
        tokens = tokens or 0
        cost = float(cost or 0.0)
        provider_usage.append(
            ProviderUsageMetrics(
                provider=p_name,
                tokens=tokens,
                cost_usd=cost,
                percentage=round((tokens / total_tokens_sum) * 100, 2)
            )
        )

    # Model Stats
    model_stats = db.query(
        Message.model_used,
        func.sum(Message.total_tokens),
        func.sum(Message.cost_usd)
    ).join(Conversation).filter(
        Conversation.organization_id == membership.organization_id,
        Message.role == "assistant",
        Message.deleted_at.is_(None),
        Message.model_used.is_not(None)
    ).group_by(Message.model_used).all()

    model_usage = []
    for stat in model_stats:
        m_name, tokens, cost = stat
        tokens = tokens or 0
        cost = float(cost or 0.0)
        model_usage.append(
            ModelUsageMetrics(
                model=m_name,
                tokens=tokens,
                cost_usd=cost,
                percentage=round((tokens / total_tokens_sum) * 100, 2)
            )
        )

    # Daily Stats (last 7 days coordinates)
    daily_stats = []
    for i in range(6, -1, -1):
        day = datetime.date.today() - datetime.timedelta(days=i)
        day_start = datetime.datetime.combine(day, datetime.time.min)
        day_end = datetime.datetime.combine(day, datetime.time.max)

        d_cost = db.query(func.sum(Message.cost_usd)).join(Conversation).filter(
            Conversation.organization_id == membership.organization_id,
            Message.created_at.between(day_start, day_end),
            Message.deleted_at.is_(None)
        ).scalar() or 0.0

        d_tokens = db.query(func.sum(Message.total_tokens)).join(Conversation).filter(
            Conversation.organization_id == membership.organization_id,
            Message.created_at.between(day_start, day_end),
            Message.deleted_at.is_(None)
        ).scalar() or 0

        d_msgs = db.query(Message).join(Conversation).filter(
            Conversation.organization_id == membership.organization_id,
            Message.created_at.between(day_start, day_end),
            Message.deleted_at.is_(None)
        ).count()

        daily_stats.append(
            DailyCostCoordinate(
                date=day.strftime("%m/%d"),
                cost_usd=float(d_cost),
                tokens=d_tokens,
                messages=d_msgs
            )
        )

    return ChatAnalyticsResponse(
        total_conversations=total_convs,
        total_messages=total_msgs,
        active_users=active_users,
        average_tokens_per_session=float(avg_tokens),
        average_cost_per_session=float(avg_cost),
        average_latency_ms=float(avg_latency),
        provider_usage=provider_usage,
        model_usage=model_usage,
        daily_stats=daily_stats
    )


@chat_router.get("/search", response_model=List[ChatSearchResponse])
def search_conversations_and_messages(
    query: str = Query(...),
    limit: int = Query(20),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Search conversation titles and message contents with snippet highlights."""
    results = []
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.organization_id == membership.organization_id,
            Conversation.user_id == current_user.id,
            Conversation.deleted_at.is_(None)
        )
        .all()
    )

    for conv in conversations:
        highlights = []
        title_match = query.lower() in conv.title.lower()

        # Message matches
        msgs = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.deleted_at.is_(None),
            Message.content.ilike(f"%{query}%")
        ).all()

        for msg in msgs:
            content = msg.content
            idx = content.lower().find(query.lower())
            start = max(0, idx - 40)
            end = min(len(content), idx + len(query) + 40)
            snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")
            snippet_highlighted = snippet.replace(query, f"<mark>{query}</mark>")

            highlights.append(
                ChatSearchHighlight(
                    message_id=msg.id,
                    role=msg.role,
                    snippet=snippet_highlighted,
                    created_at=msg.created_at
                )
            )

        if title_match or highlights:
            results.append(
                ChatSearchResponse(
                    conversation=ChatConversationResponse.from_attributes(conv),
                    highlights=highlights
                )
            )

    return results[offset : offset + limit]


@chat_router.get("/share/{share_token}", response_model=List[ChatMessageResponse])
def get_shared_conversation_messages(
    share_token: str,
    db: Session = Depends(get_db),
) -> Any:
    """Fetch messages of a shared conversation thread publicly."""
    share = db.query(ConversationShare).filter(
        ConversationShare.share_token == share_token,
        ConversationShare.is_active == True
    ).first()
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared conversation link not found or inactive",
        )
    return message_repo.get_by_conversation_id(db, share.conversation_id)


@chat_router.get("/{conversation_id}", response_model=ChatConversationResponse)
def get_conversation_details(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Get details of a single conversation thread."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return conv


@chat_router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a conversation session."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    conversation_repo.soft_delete(db, conv, deleted_by=current_user.email)


@chat_router.patch("/{conversation_id}", response_model=ChatConversationResponse)
def rename_conversation(
    conversation_id: uuid.UUID,
    conv_in: ChatConversationUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update title/rename a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    update_data = {}
    if conv_in.title is not None:
        update_data["title"] = conv_in.title
    if conv_in.is_archived is not None:
        update_data["is_archived"] = conv_in.is_archived
    if conv_in.is_favorite is not None:
        update_data["is_favorite"] = conv_in.is_favorite
    if conv_in.is_pinned is not None:
        update_data["is_pinned"] = conv_in.is_pinned

    return conversation_repo.update(db, conv, update_data, updated_by=current_user.email)


@chat_router.post("/{conversation_id}/archive", response_model=ChatConversationResponse)
def archive_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Toggle archive status of a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return conversation_repo.update(
        db, conv, {"is_archived": not conv.is_archived}, updated_by=current_user.email
    )


@chat_router.post("/{conversation_id}/favorite", response_model=ChatConversationResponse)
def favorite_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Toggle favorite status of a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return conversation_repo.update(
        db, conv, {"is_favorite": not conv.is_favorite}, updated_by=current_user.email
    )


@chat_router.post("/{conversation_id}/pin", response_model=ChatConversationResponse)
def pin_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Toggle pin status of a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return conversation_repo.update(
        db, conv, {"is_pinned": not conv.is_pinned}, updated_by=current_user.email
    )


@chat_router.post("/{conversation_id}/restore", response_model=ChatConversationResponse)
def restore_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Restore a soft-deleted conversation session."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.organization_id == membership.organization_id,
    ).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    conv.deleted_at = None
    conv.updated_by = current_user.email
    db.commit()
    db.refresh(conv)
    return conv


@chat_router.get("/{conversation_id}/messages", response_model=List[ChatMessageResponse])
def list_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """List chronological message history of a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return message_repo.get_by_conversation_id(db, conversation_id)


@chat_router.post(
    "/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_message(
    conversation_id: uuid.UUID,
    msg_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Post prompt message and execute completions via AI Gateway."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    kwargs = {}
    if msg_in.temperature is not None:
        kwargs["temperature"] = msg_in.temperature
    if msg_in.top_p is not None:
        kwargs["top_p"] = msg_in.top_p
    if msg_in.max_tokens is not None:
        kwargs["max_tokens"] = msg_in.max_tokens
    if msg_in.presence_penalty is not None:
        kwargs["presence_penalty"] = msg_in.presence_penalty
    if msg_in.frequency_penalty is not None:
        kwargs["frequency_penalty"] = msg_in.frequency_penalty
    if msg_in.json_mode is not None:
        kwargs["json_mode"] = msg_in.json_mode

    return ConversationService.post_message(
        db=db,
        conversation_id=conversation_id,
        content=msg_in.content,
        user_id=current_user.id,
        organization_id=membership.organization_id,
        model_name=msg_in.model_name,
        prompt_id=msg_in.prompt_id,
        system_prompt=msg_in.system_prompt,
        rag_enabled=msg_in.rag_enabled,
        attachment_ids=msg_in.attachment_ids,
        **kwargs,
    )


@chat_router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft delete a message in a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    msg = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id
    ).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    message_repo.soft_delete(db, msg, deleted_by=current_user.email)


@chat_router.post("/{conversation_id}/stream")
def stream_response(
    conversation_id: uuid.UUID,
    msg_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Submit a message and stream completion chunks via SSE."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    kwargs = {}
    if msg_in.temperature is not None:
        kwargs["temperature"] = msg_in.temperature
    if msg_in.top_p is not None:
        kwargs["top_p"] = msg_in.top_p
    if msg_in.max_tokens is not None:
        kwargs["max_tokens"] = msg_in.max_tokens
    if msg_in.presence_penalty is not None:
        kwargs["presence_penalty"] = msg_in.presence_penalty
    if msg_in.frequency_penalty is not None:
        kwargs["frequency_penalty"] = msg_in.frequency_penalty
    if msg_in.json_mode is not None:
        kwargs["json_mode"] = msg_in.json_mode

    generator = ConversationService.stream_response(
        db=db,
        conversation_id=conversation_id,
        content=msg_in.content,
        user_id=current_user.id,
        organization_id=membership.organization_id,
        model_name=msg_in.model_name,
        prompt_id=msg_in.prompt_id,
        system_prompt=msg_in.system_prompt,
        rag_enabled=msg_in.rag_enabled,
        attachment_ids=msg_in.attachment_ids,
        **kwargs,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@chat_router.post("/{conversation_id}/bookmarks", response_model=ConversationBookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Bookmark a conversation thread."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    existing = db.query(ConversationBookmark).filter(
        ConversationBookmark.user_id == current_user.id,
        ConversationBookmark.conversation_id == conversation_id
    ).first()
    if existing:
        return existing

    bookmark = ConversationBookmark(
        user_id=current_user.id,
        conversation_id=conversation_id,
        created_by=current_user.email
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@chat_router.delete("/{conversation_id}/bookmarks", status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove bookmark from a conversation thread."""
    bookmark = db.query(ConversationBookmark).filter(
        ConversationBookmark.user_id == current_user.id,
        ConversationBookmark.conversation_id == conversation_id
    ).first()
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    db.delete(bookmark)
    db.commit()


@chat_router.post("/{conversation_id}/share", response_model=ConversationShareResponse)
def share_conversation(
    conversation_id: uuid.UUID,
    share_in: ConversationShareCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a share link for a conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    # Check if active share already exists
    existing = db.query(ConversationShare).filter(
        ConversationShare.conversation_id == conversation_id,
        ConversationShare.is_active == True
    ).first()
    if existing:
        return existing

    share_token = f"share_{uuid.uuid4().hex}"
    share = ConversationShare(
        conversation_id=conversation_id,
        shared_by_id=current_user.id,
        share_token=share_token,
        permission=share_in.permission or "viewer",
        is_active=True,
        created_by=current_user.email
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


@chat_router.post("/{conversation_id}/attachments", response_model=ChatAttachmentResponse)
async def upload_attachment(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload a file, register it as FileAsset, and return metadata to link as attachment."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    from api.routes.files import UPLOAD_DIR
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4()
    ALLOWED_EXTENSIONS = {"txt", "pdf", "csv", "json", "md", "py", "html"}
    extension = file.filename.split(".")[-1] if "." in file.filename else ""
    # Sanitize: keep only alphanumeric chars; default to plain filename if not allowed
    extension = re.sub(r"[^a-zA-Z0-9]", "", extension).lower()
    local_filename = f"{file_id}.{extension}" if extension and extension in ALLOWED_EXTENSIONS else f"{file_id}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    file_asset = FileAsset(
        id=file_id,
        filename=file.filename,
        file_type=extension.upper() or "BINARY",
        mime_type=file.content_type,
        file_size=file_size,
        storage_url=f"/api/v1/files/{file_id}/download",
        organization_id=membership.organization_id,
        created_by=current_user.email
    )
    db.add(file_asset)
    db.commit()
    db.refresh(file_asset)

    return {
        "id": file_asset.id,
        "message_id": uuid.UUID(int=0),  # Placeholder
        "filename": file_asset.filename,
        "file_type": file_asset.file_type,
        "file_size": file_asset.file_size,
        "storage_url": file_asset.storage_url,
        "created_at": file_asset.created_at
    }


@chat_router.post("/{conversation_id}/voice", response_model=ChatMessageResponse)
async def upload_voice_and_transcribe(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload voice message, run Speech-to-Text transcription via Groq, and trigger agent response."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    from api.routes.files import UPLOAD_DIR
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4()
    extension = file.filename.split(".")[-1] if "." in file.filename else "wav"
    local_filename = f"{file_id}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    file_asset = FileAsset(
        id=file_id,
        filename=file.filename or "voice_recording.wav",
        file_type="AUDIO",
        mime_type=file.content_type or "audio/wav",
        file_size=file_size,
        storage_url=f"/api/v1/files/{file_id}/download",
        organization_id=membership.organization_id,
        created_by=current_user.email
    )
    db.add(file_asset)
    db.commit()
    db.refresh(file_asset)

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        from api.models.ai_platform import AIProvider, AIProviderKey
        from api.core.encryption import decrypt_key
        from sqlalchemy import func
        from api.repositories.ai_gateway_repository import AIProviderRepository, AIProviderKeyRepository
        from api.repositories.filters import FilterParam, FilterOperator
        prov = AIProviderRepository().find_one_sync(
            db,
            [FilterParam(field="name", operator=FilterOperator.EQ, value="groq")],
        )
        if prov:
            key_record = AIProviderKeyRepository().find_one_sync(
                db,
                [
                    FilterParam(field="provider_id", operator=FilterOperator.EQ, value=prov.id),
                    FilterParam(field="organization_id", operator=FilterOperator.EQ, value=membership.organization_id),
                    FilterParam(field="is_active", operator=FilterOperator.EQ, value=True),
                ],
            )
            if key_record:
                try:
                    groq_key = decrypt_key(key_record.api_key)
                except Exception:
                    pass

    transcription = ""
    if groq_key:
        try:
            import httpx
            with open(file_path, "rb") as f:
                files_payload = {"file": (file.filename or "voice_recording.wav", f, file.content_type or "audio/wav")}
                data_payload = {"model": "whisper-large-v3"}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        files=files_payload,
                        data=data_payload,
                        timeout=30.0
                    )
                    if resp.status_code == 200:
                        transcription = resp.json().get("text", "")
        except Exception as e:
            transcription = f"[Groq Whisper Transcription Failed: {str(e)}]"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Groq API key not configured. Unable to perform voice transcription."
        )

    if not transcription.strip():
        transcription = "[Inaudible voice message]"

    return ConversationService.post_message(
        db=db,
        conversation_id=conversation_id,
        content=transcription,
        user_id=current_user.id,
        organization_id=membership.organization_id,
        model_name=conv.model_name or "openai/gpt-oss-120b",
        attachment_ids=[file_id]
    )


@chat_router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: uuid.UUID,
    format: str = "markdown",  # markdown, json, txt
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Export conversation message history in selected formats."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    messages = message_repo.get_by_conversation_id(db, conversation_id)

    if format == "json":
        from fastapi.responses import JSONResponse
        content = [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages]
        return JSONResponse(content=content, headers={"Content-Disposition": f"attachment; filename={conv.title}.json"})
    elif format == "txt":
        from fastapi.responses import Response
        lines = [f"{m.role.upper()}: {m.content}\n" for m in messages]
        return Response(content="".join(lines), media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={conv.title}.txt"})
    else:  # markdown
        from fastapi.responses import Response
        lines = [f"### {m.role.capitalize()}\n\n{m.content}\n" for m in messages]
        md_text = f"# {conv.title}\n\n" + "\n".join(lines)
        return Response(content=md_text, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={conv.title}.md"})


@chat_router.get("/{conversation_id}/participants", response_model=List[ChatParticipantResponse])
def list_participants(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """List participants of a conversation thread."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    participants = db.query(ChatParticipant).filter(
        ChatParticipant.conversation_id == conversation_id,
        ChatParticipant.deleted_at.is_(None)
    ).all()

    result = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append(
            ChatParticipantResponse(
                id=p.id,
                conversation_id=p.conversation_id,
                user_id=p.user_id,
                user_email=user.email if user else None,
                role=p.role,
                created_at=p.created_at
            )
        )
    return result


@chat_router.post("/{conversation_id}/participants", response_model=ChatParticipantResponse, status_code=status.HTTP_201_CREATED)
def invite_participant(
    conversation_id: uuid.UUID,
    participant_in: ChatParticipantCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Add / invite a participant to a collaborative conversation."""
    conv = conversation_repo.get_by_id_and_org(
        db, conversation_id, membership.organization_id
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    user = db.query(User).filter(User.email == participant_in.user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {participant_in.user_email} not found",
        )

    org_mem = db.query(UserOrganization).filter(
        UserOrganization.user_id == user.id,
        UserOrganization.organization_id == membership.organization_id
    ).first()
    if not org_mem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to your organization",
        )

    existing = db.query(ChatParticipant).filter(
        ChatParticipant.conversation_id == conversation_id,
        ChatParticipant.user_id == user.id
    ).first()
    if existing:
        if existing.deleted_at is not None:
            existing.deleted_at = None
            existing.role = participant_in.role or "member"
            db.commit()
            db.refresh(existing)
            return ChatParticipantResponse(
                id=existing.id,
                conversation_id=existing.conversation_id,
                user_id=existing.user_id,
                user_email=user.email,
                role=existing.role,
                created_at=existing.created_at
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant",
        )

    p = ChatParticipant(
        conversation_id=conversation_id,
        user_id=user.id,
        role=participant_in.role or "member",
        created_by=current_user.email
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ChatParticipantResponse(
        id=p.id,
        conversation_id=p.conversation_id,
        user_id=p.user_id,
        user_email=user.email,
        role=p.role,
        created_at=p.created_at
    )


@chat_router.patch("/{conversation_id}/participants/{user_id}", response_model=ChatParticipantResponse)
def update_participant_role(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str = Query(..., description="Role value, e.g. editor, viewer"),
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update participant role (e.g. editor, viewer)."""
    p = db.query(ChatParticipant).filter(
        ChatParticipant.conversation_id == conversation_id,
        ChatParticipant.user_id == user_id,
        ChatParticipant.deleted_at.is_(None)
    ).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    p.role = role
    p.updated_by = current_user.email
    db.commit()
    db.refresh(p)

    user = db.query(User).filter(User.id == user_id).first()
    return ChatParticipantResponse(
        id=p.id,
        conversation_id=p.conversation_id,
        user_id=p.user_id,
        user_email=user.email if user else None,
        role=p.role,
        created_at=p.created_at
    )


@chat_router.delete("/{conversation_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove participant from conversation thread."""
    p = db.query(ChatParticipant).filter(
        ChatParticipant.conversation_id == conversation_id,
        ChatParticipant.user_id == user_id,
        ChatParticipant.deleted_at.is_(None)
    ).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    p.deleted_at = datetime.datetime.now(datetime.UTC) if hasattr(datetime, "UTC") else func.now()
    p.updated_by = current_user.email
    db.commit()
