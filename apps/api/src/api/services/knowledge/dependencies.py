"""
EAIMOS Knowledge Dependencies
=============================
FastAPI dependency providers for Sprint 8 Knowledge services.
"""

from api.services.base.dependency_provider import container
from api.services.knowledge.knowledge_collection_service import KnowledgeCollectionService
from api.services.knowledge.document_ingestion_service import DocumentIngestionService
from api.services.knowledge.vector_search_service import VectorSearchService


def get_knowledge_collection_service() -> KnowledgeCollectionService:
    return KnowledgeCollectionService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_document_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_vector_search_service() -> VectorSearchService:
    return VectorSearchService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
