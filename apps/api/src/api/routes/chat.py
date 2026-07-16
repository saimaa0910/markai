import uuid
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.user import User
from api.models.membership import UserOrganization, UserRole
from api.repositories.conversation import conversation_repo, message_repo
from api.services.conversation import ConversationService
from api.schemas.chat import (
    ChatConversationCreate,
    ChatConversationUpdate,
    ChatConversationResponse,
    ChatMessageCreate,
    ChatMessageResponse,
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
    title = conv_in.title or f"Chat Session {datetime.now().strftime('%H:%M')}" if "datetime" in globals() else conv_in.title or "New Chat"
    if not conv_in.title:
        import datetime
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
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List conversations for active organization and user."""
    if query:
        return conversation_repo.search_conversations(
            db, membership.organization_id, current_user.id, query
        )
    return conversation_repo.list_by_org_and_user(
        db, membership.organization_id, current_user.id
    )


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
    """Post prompt message and execute non-streaming chat completions via AI Gateway."""
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
        **kwargs,
    )


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
        **kwargs,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
