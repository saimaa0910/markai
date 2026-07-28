"""
Sprint 8 Knowledge Base & Vector Indexing Service Tests
=========================================================
Tests for KnowledgeCollectionService, DocumentIngestionService, and VectorSearchService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.knowledge.knowledge_collection_service import KnowledgeCollectionService
from api.services.knowledge.document_ingestion_service import DocumentIngestionService
from api.services.knowledge.vector_search_service import VectorSearchService
from api.services.knowledge.dtos import (
    CreateKnowledgeCollectionDTO,
    IngestDocumentDTO,
    VectorSearchQueryDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer() -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = True
    return auth


def make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()
    return uow


def make_entity(**kwargs) -> MagicMock:
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = datetime.now(timezone.utc)
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


class TestKnowledgeCollectionService:
    @pytest.mark.asyncio
    async def test_create_collection(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        col_entity = make_entity(
            organization_id=ctx.organization_id,
            name="Q4 Marketing Strategy",
            description="Campaign documentation",
            visibility="ORGANIZATION",
            is_archived=False,
            is_favorite=False,
            is_pinned=False,
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = col_entity

        svc = KnowledgeCollectionService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.knowledge.knowledge_collection_service._KnowledgeCollectionRepository", return_value=repo_mock):
            res = await svc.create_collection(
                ctx,
                org_id=ctx.organization_id,
                dto=CreateKnowledgeCollectionDTO(
                    name="Q4 Marketing Strategy",
                    description="Campaign documentation",
                    visibility="ORGANIZATION",
                ),
            )

        assert res.is_success
        assert res.data.name == "Q4 Marketing Strategy"


class TestDocumentIngestionService:
    @pytest.mark.asyncio
    async def test_ingest_document(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = DocumentIngestionService(authorizer=authorizer)
        res = await svc.ingest_document(
            ctx,
            dto=IngestDocumentDTO(
                collection_id=uuid.uuid4(),
                title="Q4 Product Roadmap.md",
                raw_content="EAIMOS enterprise AI architecture guide text content...",
                chunk_size=512,
                chunk_overlap=64,
            ),
        )

        assert res.is_success
        assert res.data.status == "INDEXED"
        assert res.data.total_chunks >= 1


class TestVectorSearchService:
    @pytest.mark.asyncio
    async def test_search_vector_index(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = VectorSearchService(authorizer=authorizer)
        res = await svc.search_vector_index(
            ctx,
            dto=VectorSearchQueryDTO(
                collection_id=uuid.uuid4(),
                query_text="RAG architecture patterns",
                top_k=3,
            ),
        )

        assert res.is_success
        assert len(res.data) == 3
        assert res.data[0].score > 0.8
