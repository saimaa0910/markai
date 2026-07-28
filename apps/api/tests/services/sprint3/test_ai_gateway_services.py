"""
Sprint 3 AI Gateway Service Tests
===================================
Tests for PromptService, ModelRouterService, RAGService, MemoryService, and AIUsageService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.ai.prompt_service import PromptService
from api.services.ai.model_router_service import ModelRouterService
from api.services.ai.rag_service import RAGService
from api.services.ai.memory_service import MemoryService
from api.services.ai.ai_usage_service import AIUsageService
from api.services.ai.dtos import (
    CreatePromptDTO,
    RenderPromptDTO,
    RouteRequestDTO,
    IndexDocumentDTO,
    SearchQueryDTO,
    StoreMessageDTO,
    RecordUsageDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.get_org_id_uuid.return_value = ctx.organization_id
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


class TestPromptService:
    @pytest.mark.asyncio
    async def test_create_prompt_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        prompt_entity = make_entity(
            organization_id=ctx.organization_id,
            title="Welcome Email",
            template="Hello {{name}}, welcome to {{company}}!",
            version=1,
            variables=["name", "company"],
            tags=[],
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = prompt_entity
        uow.get_repository.return_value = repo_mock

        svc = PromptService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.ai.prompt_service._PromptRepository", return_value=repo_mock):
            res = await svc.create_prompt(
                ctx,
                org_id=ctx.organization_id,
                dto=CreatePromptDTO(
                    title="Welcome Email",
                    template="Hello {{name}}, welcome to {{company}}!",
                ),
            )

        assert res.is_success
        assert res.data.title == "Welcome Email"
        assert "name" in res.data.variables

    @pytest.mark.asyncio
    async def test_render_prompt_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        prompt_id = uuid.uuid4()
        prompt_entity = make_entity(
            id=prompt_id,
            organization_id=ctx.organization_id,
            title="Welcome Email",
            template="Hello {{name}}, welcome to {{company}}!",
            version=1,
            variables=["name", "company"],
            tags=[],
        )

        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = prompt_entity
        uow.get_repository.return_value = repo_mock

        svc = PromptService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.ai.prompt_service._PromptRepository", return_value=repo_mock):
            res = await svc.render_prompt(
                ctx,
                dto=RenderPromptDTO(
                    prompt_id=prompt_id,
                    variables={"name": "Alice", "company": "Acme Inc"},
                ),
            )

        assert res.is_success
        assert res.data.rendered_text == "Hello Alice, welcome to Acme Inc!"
        assert len(res.data.unresolved_variables) == 0


class TestModelRouterService:
    @pytest.mark.asyncio
    async def test_route_request_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        uow = make_uow()

        svc = ModelRouterService(uow_service=uow, authorizer=authorizer)
        res = await svc.route_request(
            ctx,
            dto=RouteRequestDTO(
                messages=[{"role": "user", "content": "Hello world!"}],
                preferred_provider="openai",
                preferred_model="gpt-4o",
            ),
        )

        assert res.is_success
        assert res.data.selected_provider == "openai"
        assert res.data.selected_model == "gpt-4o"
        assert res.data.estimated_cost_usd > 0.0


class TestRAGService:
    @pytest.mark.asyncio
    async def test_index_document(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        uow = make_uow()

        svc = RAGService(uow_service=uow, authorizer=authorizer)
        with patch("api.services.knowledge_service.KnowledgeService") as mock_kb:
            mock_doc = MagicMock()
            mock_doc.id = uuid.uuid4()
            mock_doc.chunks = []
            mock_kb.upload_document.return_value = mock_doc

            res = await svc.index_document(
                ctx,
                dto=IndexDocumentDTO(
                    knowledge_base_id=uuid.uuid4(),
                    title="Product Guide",
                    content="This is the main product guide documentation content.",
                ),
            )

        assert res.is_success
        assert res.data is True

    @pytest.mark.asyncio
    async def test_search_rag(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        uow = make_uow()

        svc = RAGService(uow_service=uow, authorizer=authorizer)
        with patch("api.services.knowledge_service.KnowledgeService") as mock_kb:
            mock_chunk = MagicMock()
            mock_chunk.document_id = uuid.uuid4()
            mock_chunk.id = uuid.uuid4()
            mock_chunk.content = "Relevant knowledge context matching: How to set up account?"
            mock_chunk._similarity_score = 0.89
            mock_chunk.metadata_json = {"source": "kb_doc.pdf"}

            mock_kb.query_similar_chunks.return_value = [mock_chunk]

            res = await svc.search(
                ctx,
                dto=SearchQueryDTO(
                    knowledge_base_ids=[uuid.uuid4()],
                    query_text="How to set up account?",
                ),
            )

        assert res.is_success
        assert res.data.total_found == 1
        assert res.data.results[0].similarity_score > 0.8


class TestMemoryService:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()
        conv_id = uuid.uuid4()

        svc = MemoryService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        await svc.store_message(
            ctx,
            dto=StoreMessageDTO(
                conversation_id=conv_id,
                role="user",
                content="Hello AI!",
            ),
        )

        res = await svc.get_memory(ctx, conversation_id=conv_id)
        assert res.is_success
        assert len(res.data.messages) == 1
        assert res.data.messages[0]["content"] == "Hello AI!"


class TestAIUsageService:
    @pytest.mark.asyncio
    async def test_record_usage(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        uow = make_uow()

        svc = AIUsageService(uow_service=uow, authorizer=authorizer)
        res = await svc.record_usage(
            ctx,
            org_id=ctx.organization_id,
            dto=RecordUsageDTO(
                provider="openai",
                model="gpt-4o",
                prompt_tokens=1000,
                completion_tokens=500,
                execution_time_ms=350.0,
            ),
        )

        assert res.is_success
        assert res.data is True
