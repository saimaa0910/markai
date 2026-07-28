"""
EAIMOS Knowledge Base Events
=============================
Domain events for Sprint 8 Knowledge Base & Vector Indexing.
"""

from api.services.base.events import DomainEvent


class KnowledgeCollectionCreated(DomainEvent):
    event_type: str = "knowledge.collection_created"
    collection_id: str = ""
    name: str = ""


class DocumentIngestionStarted(DomainEvent):
    event_type: str = "knowledge.document_ingestion_started"
    document_id: str = ""
    collection_id: str = ""


class DocumentIndexed(DomainEvent):
    event_type: str = "knowledge.document_indexed"
    document_id: str = ""
    chunks_count: int = 0


class VectorSearchExecuted(DomainEvent):
    event_type: str = "knowledge.vector_search_executed"
    collection_id: str = ""
    top_k: int = 0
