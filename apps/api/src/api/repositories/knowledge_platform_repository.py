"""
EAIMOS Knowledge Platform Repository Module — Sprint 5
======================================================
Repository implementations for Knowledge Platform models:
KnowledgeDocument, DocumentChunk, KnowledgeCollection, KnowledgeFolder, KnowledgeProcessingJob, FileAsset.
"""

from typing import Any, List, Optional
import uuid

from api.models.knowledge import (
    KnowledgeDocument,
    DocumentChunk,
    KnowledgeCollection,
    KnowledgeFolder,
    KnowledgeProcessingJob,
)
from api.models.file_asset import FileAsset
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class KnowledgeDocumentRepository(TenantRepository[KnowledgeDocument]):
    """Data access layer for Knowledge RAG Documents."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(KnowledgeDocument, organization_id=organization_id)

    async def list_by_collection(self, session: Any, collection_id: uuid.UUID) -> List[KnowledgeDocument]:
        filters = [FilterParam(field="collection_id", operator=FilterOperator.EQ, value=collection_id)]
        return await self.find_many(session=session, filters=filters)


class DocumentChunkRepository(TenantRepository[DocumentChunk]):
    """Data access layer for vector document chunks."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(DocumentChunk, organization_id=organization_id)

    async def list_by_document(self, session: Any, document_id: uuid.UUID) -> List[DocumentChunk]:
        filters = [FilterParam(field="document_id", operator=FilterOperator.EQ, value=document_id)]
        return await self.find_many(session=session, filters=filters)


class KnowledgeCollectionRepository(TenantRepository[KnowledgeCollection]):
    """Data access layer for Knowledge Collections."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(KnowledgeCollection, organization_id=organization_id)


class KnowledgeFolderRepository(TenantRepository[KnowledgeFolder]):
    """Data access layer for Knowledge Folders."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(KnowledgeFolder, organization_id=organization_id)


class KnowledgeProcessingJobRepository(TenantRepository[KnowledgeProcessingJob]):
    """Data access layer for ingestion jobs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(KnowledgeProcessingJob, organization_id=organization_id)


class FileAssetRepository(TenantRepository[FileAsset]):
    """Data access layer for uploaded file assets."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(FileAsset, organization_id=organization_id)
