"""
EAIMOS Knowledge Interfaces
============================
Protocol declarations for Sprint 8 Knowledge services.
"""

from typing import List, Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.knowledge.dtos import (
    CreateKnowledgeCollectionDTO,
    DocumentResponseDTO,
    IngestDocumentDTO,
    KnowledgeCollectionResponseDTO,
    VectorSearchQueryDTO,
    VectorSearchResultDTO,
)


class IKnowledgeCollectionService(Protocol):
    async def create_collection(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateKnowledgeCollectionDTO
    ) -> ServiceResult[KnowledgeCollectionResponseDTO]: ...


class IDocumentIngestionService(Protocol):
    async def ingest_document(
        self, ctx: ServiceContext, dto: IngestDocumentDTO
    ) -> ServiceResult[DocumentResponseDTO]: ...


class IVectorSearchService(Protocol):
    async def search_vector_index(
        self, ctx: ServiceContext, dto: VectorSearchQueryDTO
    ) -> ServiceResult[List[VectorSearchResultDTO]]: ...
