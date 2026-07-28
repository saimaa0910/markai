"""
EAIMOS Chat Domain Events
==========================
Domain events for Sprint 10 Conversational AI & Real-time Messaging.
"""

from api.services.base.events import DomainEvent


class ConversationCreated(DomainEvent):
    event_type: str = "chat.conversation_created"
    conversation_id: str = ""
    title: str = ""


class MessageSent(DomainEvent):
    event_type: str = "chat.message_sent"
    message_id: str = ""
    conversation_id: str = ""
    role: str = ""


class ConversationArchived(DomainEvent):
    event_type: str = "chat.conversation_archived"
    conversation_id: str = ""
