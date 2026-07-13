import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.prompt import Prompt
from api.models.conversation import Conversation
from api.models.message import Message
from api.services.llm import LLMGateway
from api.schemas.ai import (
    PromptCreate,
    PromptResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

prompts_router = APIRouter(prefix="/ai/prompts", tags=["ai-prompts"])
conversations_router = APIRouter(prefix="/ai/conversations", tags=["ai-conversations"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# ==========================================
# PROMPT LIBRARY ENDPOINTS
# ==========================================


@prompts_router.post(
    "/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED
)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Ensure name uniqueness inside organization
    existing = (
        db.query(Prompt)
        .filter(
            Prompt.name == prompt_in.name,
            Prompt.organization_id == membership.organization_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt template with this name already exists in your library.",
        )

    prompt = Prompt(
        name=prompt_in.name,
        content=prompt_in.content,
        version=prompt_in.version or 1,
        organization_id=membership.organization_id,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@prompts_router.get("/", response_model=List[PromptResponse])
def list_prompts(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return (
        db.query(Prompt)
        .filter(Prompt.organization_id == membership.organization_id)
        .all()
    )


@prompts_router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    prompt = (
        db.query(Prompt)
        .filter(
            Prompt.id == prompt_id, Prompt.organization_id == membership.organization_id
        )
        .first()
    )
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found"
        )
    db.delete(prompt)
    db.commit()


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

    # 3. Log user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=msg_in.content,
        model_used=msg_in.model_name,
    )
    db.add(user_msg)

    # 4. Trigger LLM Gateway Response
    assistant_content = LLMGateway.generate_response(
        prompt_content=msg_in.content,
        model_name=msg_in.model_name,
        system_instruction=system_instruction,
    )

    # 5. Log assistant response
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        model_used=msg_in.model_name,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg
