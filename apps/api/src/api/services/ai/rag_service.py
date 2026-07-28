"""
EAIMOS RAG Service (Sprint 3)
==============================
Service Layer for Vector Search, Document Chunking & Ingestion, and Semantic Retrieval.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from api.services.base import ServiceContext, ServiceResult
from api.services.ai.dtos import (
    IndexDocumentDTO,
    RAGSearchResultDTO,
    RAGSearchResultItemDTO,
    SearchQueryDTO,
)
from api.services.ai.events import DocumentIndexed, VectorSearchExecuted
from api.services.ai.policies import RAGPolicy
from api.services.ai.validators import validate_chunk_size_and_overlap

logger = logging.getLogger("eaimos.ai.rag")


class RAGService:
    """Vector Store & Semantic Retrieval RAG Domain Service."""

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

    async def index_document(
        self,
        ctx: ServiceContext,
        dto: IndexDocumentDTO,
    ) -> ServiceResult[bool]:
        try:
            RAGPolicy.can_index(self.authorizer, ctx, ctx.get_org_id_str())
            validate_chunk_size_and_overlap(dto.chunk_size, dto.chunk_overlap)

            org_id = ctx.get_org_id_uuid()
            user_id = ctx.get_user_id_uuid()

            async with self.uow_service:
                from api.services.knowledge_service import KnowledgeService
                from api.schemas.ai import KnowledgeUploadRequest
                
                doc_in = KnowledgeUploadRequest(
                    title=dto.title,
                    content=dto.content,
                    file_type=getattr(dto, "file_type", "txt") or "text",
                )
                
                doc = KnowledgeService.upload_document(
                    db=self.uow_service.session,
                    doc_in=doc_in,
                    organization_id=org_id,
                    user_id=user_id,
                )
                
                chunk_count = len(doc.chunks) if doc.chunks else 0

                if self.dispatcher:
                    await self.dispatcher.publish(
                        DocumentIndexed(
                            aggregate_id=str(doc.id),
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            knowledge_base_id=str(dto.knowledge_base_id),
                            document_id=str(doc.id),
                            chunk_count=chunk_count,
                        )
                    )

            return ServiceResult.ok(data=True, status_code=201)

        except Exception as exc:
            logger.error(f"index_document failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def search(
        self,
        ctx: ServiceContext,
        dto: SearchQueryDTO,
    ) -> ServiceResult[RAGSearchResultDTO]:
        try:
            RAGPolicy.can_search(self.authorizer, ctx, ctx.get_org_id_str())
            org_id = ctx.get_org_id_uuid()
            user_id = ctx.get_user_id_uuid()

            async with self.uow_service:
                from api.services.knowledge_service import KnowledgeService
                import time

                start_time = time.perf_counter()
                chunks = KnowledgeService.query_similar_chunks(
                    db=self.uow_service.session,
                    query_text=dto.query_text,
                    organization_id=org_id,
                    user_id=user_id,
                    limit=getattr(dto, "limit", None) or getattr(dto, "top_k", 3),
                )
                execution_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

                results = []
                for chunk in chunks:
                    # Compute a dummy similarity score for SQLite fallback if not stored
                    similarity = 0.85
                    if hasattr(chunk, "_similarity_score"):
                        similarity = chunk._similarity_score
                    
                    results.append(
                        RAGSearchResultItemDTO(
                            document_id=chunk.document_id,
                            chunk_id=chunk.id,
                            text_content=chunk.content,
                            similarity_score=similarity,
                            metadata=chunk.metadata_json or {},
                        )
                    )

                res_dto = RAGSearchResultDTO(
                    query_text=dto.query_text,
                    results=results,
                    total_found=len(results),
                    execution_time_ms=execution_time_ms,
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        VectorSearchExecuted(
                            aggregate_id=ctx.get_user_id_str() or "system",
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            knowledge_base_count=len(dto.knowledge_base_ids or []),
                            results_found=len(results),
                            execution_time_ms=execution_time_ms,
                        )
                    )

            return ServiceResult.ok(data=res_dto)

        except Exception as exc:
            logger.error(f"search failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
