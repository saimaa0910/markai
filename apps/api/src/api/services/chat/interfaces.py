"""
EAIMOS Chat Interfaces
=======================
Protocol declarations for Sprint 10 Chat services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.chat.dtos import (
    CreateConversationDTO,
    ConversationResponseDTO,
    SendMessageDTO,
    MessageResponseDTO,
)


class IChatConversationService(Protocol):
    async def create_conversation(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateConversationDTO
    ) -> ServiceResult[ConversationResponseDTO]: ...


class IChatMessageService(Protocol):
    async def send_message(
        self, ctx: ServiceContext, dto: SendMessageDTO
    ) -> ServiceResult[MessageResponseDTO]: ...
