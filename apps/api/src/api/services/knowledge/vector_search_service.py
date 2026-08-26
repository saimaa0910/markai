"""
EAIMOS Vector Search Service (Sprint 8)
========================================
Service Layer managing Dense & Hybrid Semantic Vector Search.
"""

import logging
import uuid
import asyncio
from typing import Any, List, Optional

from api.services.base import ServiceContext, ServiceResult
from api.services.knowledge.dtos import VectorSearchQueryDTO, VectorSearchResultDTO
from api.services.knowledge.events import VectorSearchExecuted

logger = logging.getLogger("eaimos.knowledge.vector_search")


class VectorSearchService:
    """Semantic Vector Embedding Index Search Service."""

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        authorizer: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher

async def search_vector_index(
        self,
        ctx: ServiceContext,
        dto: VectorSearchQueryDTO,
    ) -> ServiceResult[List[VectorSearchResultDTO]]:
        try:
            results: List[VectorSearchResultDTO] = []
            org_uuid = ctx.get_org_id_uuid()
            if not org_uuid:
                return ServiceResult.fail(error="organization_id required", error_code="ORGANIZATION_REQUIRED")

            query_text = dto.query_text
            if not query_text:
                return ServiceResult.fail(error="query text required", error_code="QUERY_REQUIRED")

            limit = dto.top_k or 5

            async with self.uow_service:
                # Run real pgvector search (P2-2) through the shared KnowledgeService.
                from api.services.knowledge_service import KnowledgeService
                chunks = await asyncio.to_thread(
                    KnowledgeService.query_similar_chunks,
                    self.uow_service.session,
                    query_text,
                    org_uuid,
                    ctx.get_user_id_uuid(),
                    limit,
                )

            for chunk in chunks:
                results.append(
                    VectorSearchResultDTO(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        score=1.0,
                        text_content=chunk.content,
                        metadata=chunk.metadata_json or {},
                    )
                )

            if self.dispatcher:
                await self.dispatcher.publish(
                    VectorSearchExecuted(
                        aggregate_id=str(org_uuid),
                        tenant_id=str(org_uuid),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        query_text=query_text,
                        results_count=len(results),
                        search_type="semantic",
                    )
                )
            return ServiceResult.ok(data=results)
        except Exception as exc:
            logger.error(f"search_vector_index failed: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), error_code="SEARCH_FAILED")
            return ServiceResult.from_exception(exc)
