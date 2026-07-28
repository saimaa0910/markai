"""
EAIMOS AI Gateway Domain Events
=================================
Domain events for Sprint 3 AI Gateway & Orchestration.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field
from api.services.base.events import DomainEvent


class PromptTemplateCreated(DomainEvent):
    event_type: str = "ai.prompt.created"
    prompt_id: str = ""
    title: str = ""
    version: int = 1


class PromptVersionPublished(DomainEvent):
    event_type: str = "ai.prompt.version_published"
    prompt_id: str = ""
    new_version: int = 1


class ModelRouted(DomainEvent):
    event_type: str = "ai.router.model_routed"
    selected_provider: str = ""
    selected_model: str = ""
    estimated_cost_usd: float = 0.0


class ModelFailoverTriggered(DomainEvent):
    event_type: str = "ai.router.failover_triggered"
    primary_provider: str = ""
    primary_model: str = ""
    fallback_provider: str = ""
    fallback_model: str = ""
    error_reason: str = ""


class DocumentIndexed(DomainEvent):
    event_type: str = "ai.rag.document_indexed"
    knowledge_base_id: str = ""
    document_id: str = ""
    chunk_count: int = 0


class VectorSearchExecuted(DomainEvent):
    event_type: str = "ai.rag.search_executed"
    knowledge_base_count: int = 0
    results_found: int = 0
    execution_time_ms: float = 0.0


class ConversationMemoryUpdated(DomainEvent):
    event_type: str = "ai.memory.updated"
    conversation_id: str = ""
    message_role: str = ""


class MemorySummarized(DomainEvent):
    event_type: str = "ai.memory.summarized"
    conversation_id: str = ""
    summarized_message_count: int = 0


class AIUsageRecorded(DomainEvent):
    event_type: str = "ai.usage.recorded"
    provider: str = ""
    model: str = ""
    total_tokens: int = 0
    calculated_cost_usd: float = 0.0


class AGUIExecutionStarted(DomainEvent):
    event_type: str = "ai.agui.execution_started"
    prompt_id: str = ""
    conversation_id: Optional[str] = None
