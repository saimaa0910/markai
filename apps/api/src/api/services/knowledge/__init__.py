"""
EAIMOS Knowledge Service Layer (Sprint 8)
===========================================
Public API for Knowledge Collections, Document Ingestion & Vector Search services.
"""

from api.services.knowledge.knowledge_collection_service import KnowledgeCollectionService
from api.services.knowledge.document_ingestion_service import DocumentIngestionService
from api.services.knowledge.vector_search_service import VectorSearchService

KnowledgeService = KnowledgeCollectionService

from api.services.knowledge.dtos import (
    CreateKnowledgeCollectionDTO,
    KnowledgeCollectionResponseDTO,
    IngestDocumentDTO,
    DocumentResponseDTO,
    VectorSearchQueryDTO,
    VectorSearchResultDTO,
)

from api.services.knowledge.events import (
    KnowledgeCollectionCreated,
    DocumentIngestionStarted,
    DocumentIndexed,
    VectorSearchExecuted,
)

from api.services.knowledge.dependencies import (
    get_knowledge_collection_service,
    get_document_ingestion_service,
    get_vector_search_service,
)

__all__ = [
    "KnowledgeCollectionService",
    "KnowledgeService",
    "DocumentIngestionService",
    "VectorSearchService",
    "CreateKnowledgeCollectionDTO",
    "KnowledgeCollectionResponseDTO",
    "IngestDocumentDTO",
    "DocumentResponseDTO",
    "VectorSearchQueryDTO",
    "VectorSearchResultDTO",
    "get_knowledge_collection_service",
    "get_document_ingestion_service",
    "get_vector_search_service",
]
