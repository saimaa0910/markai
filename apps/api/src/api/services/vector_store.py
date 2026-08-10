import uuid
import math
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, text
from api.models.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeCollection, KnowledgeFolder

logger = logging.getLogger("api.services.vector_store")


class VectorStore:
    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @classmethod
    def apply_filters(cls, query_obj, filters: Optional[Dict[str, Any]], organization_id: uuid.UUID):
        """
        Applies filter criteria to a SQLAlchemy query matching document chunks.
        """
        # DocumentChunk joins KnowledgeDocument to filter on doc metadata
        query_obj = query_obj.join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
        
        conditions = [DocumentChunk.organization_id == organization_id, KnowledgeDocument.deleted_at.is_(None)]
        
        if filters:
            if filters.get("collection_id"):
                conditions.append(KnowledgeDocument.collection_id == uuid.UUID(str(filters["collection_id"])))
            if filters.get("folder_id"):
                conditions.append(KnowledgeDocument.folder_id == uuid.UUID(str(filters["folder_id"])))
            if filters.get("department"):
                conditions.append(KnowledgeDocument.department == filters["department"])
            if filters.get("category"):
                conditions.append(KnowledgeDocument.category == filters["category"])
            if filters.get("file_types"):
                conditions.append(KnowledgeDocument.file_type.in_(filters["file_types"]))
            if filters.get("start_date"):
                conditions.append(KnowledgeDocument.created_at >= filters["start_date"])
            if filters.get("end_date"):
                conditions.append(KnowledgeDocument.created_at <= filters["end_date"])
            if filters.get("tags"):
                # Handle JSON array filtering
                # For compatibility, do basic string checking in Python or raw query in Postgres
                pass
                
        return query_obj.where(and_(*conditions))

    @classmethod
    def semantic_search(
        cls,
        db: Session,
        query_embedding: List[float],
        organization_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Perform vector similarity search, querying pgvector.
        """
        # Build pgvector query
        # cosine_distance maps to 1 - cosine_similarity
        from api.models.knowledge import DocumentChunkEmbedding
        stmt = select(DocumentChunk).join(DocumentChunkEmbedding, DocumentChunk.id == DocumentChunkEmbedding.chunk_id)
        stmt = cls.apply_filters(stmt, filters, organization_id)
        stmt = stmt.order_by(DocumentChunkEmbedding.embedding.cosine_distance(query_embedding))
        stmt = stmt.limit(limit)
        
        chunks = db.scalars(stmt).all()
        results = []
        for chunk in chunks:
            # Calculate similarity: 1 - cosine_distance
            vec = chunk.embedding
            sim = cls._cosine_similarity(query_embedding, vec)
            results.append((sim, chunk))
        # Sort descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:limit]

    @classmethod
    def keyword_search(
        cls,
        db: Session,
        query_text: str,
        organization_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Full text/lexical search query using PostgreSQL Full Text Search.
        """
        stmt = select(DocumentChunk)
        stmt = cls.apply_filters(stmt, filters, organization_id)
        
        # Build search condition
        search_terms = [term for term in query_text.split() if len(term) > 2]
        ts_query = " & ".join(search_terms)
        if ts_query:
            stmt = stmt.where(
                text("to_tsvector('english', document_chunks.content) @@ to_tsquery('english', :query)")
            ).params(query=ts_query)
        else:
            stmt = stmt.where(DocumentChunk.content.ilike(f"%{query_text}%"))

        chunks = db.scalars(stmt.limit(limit * 2)).all()
        
        # Grade matches by term occurrences
        results = []
        for chunk in chunks:
            count = sum(1 for term in search_terms if term.lower() in chunk.content.lower())
            score = 0.5 + (count / max(1, len(search_terms))) * 0.5
            results.append((score, chunk))
            
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:limit]

    @classmethod
    def hybrid_search(
        cls,
        db: Session,
        query_text: str,
        query_embedding: List[float],
        organization_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Reciprocal Rank Fusion (RRF) to combine Semantic and Keyword Search.
        Score(d) = 1 / (60 + rank_semantic) + 1 / (60 + rank_keyword)
        """
        semantic_results = cls.semantic_search(db, query_embedding, organization_id, filters, limit * 2)
        keyword_results = cls.keyword_search(db, query_text, organization_id, filters, limit * 2)

        rrf_scores = {}
        chunk_map = {}

        # constant parameter
        k = 60

        for rank, (score, chunk) in enumerate(semantic_results):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            chunk_map[chunk.id] = (score, chunk) # store vector score as similarity reference

        for rank, (score, chunk) in enumerate(keyword_results):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            if chunk.id not in chunk_map:
                # If only found in keyword search, project a proxy similarity score
                chunk_map[chunk.id] = (0.5, chunk)

        # Sort based on RRF scores
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        final_results = []
        for cid in sorted_ids[:limit]:
            vector_score, chunk = chunk_map[cid]
            final_results.append((vector_score, chunk))
            
        return final_results

    @classmethod
    def mmr_rerank(
        cls,
        candidates: List[Tuple[float, DocumentChunk]],
        query_embedding: List[float],
        lambda_val: float = 0.5,
        limit: int = 5,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Maximal Marginal Relevance (MMR) to diversify retrieved chunks.
        MMR = lambda * Sim(c, q) - (1 - lambda) * max(Sim(c, selected))
        """
        if not candidates:
            return []
            
        selected = []
        remaining = list(candidates)
        
        # Select the top candidate first
        first = max(remaining, key=lambda x: x[0])
        selected.append(first)
        remaining.remove(first)
        
        while len(selected) < limit and remaining:
            best_mmr = -1.0
            best_cand = None
            
            for cand_score, cand_chunk in remaining:
                # Calculate maximum similarity with already selected chunks
                max_sim_selected = 0.0
                cand_vec = cand_chunk.embedding or []
                if isinstance(cand_vec, str):
                    cand_vec = json.loads(cand_vec)
                    
                for sel_score, sel_chunk in selected:
                    sel_vec = sel_chunk.embedding or []
                    if isinstance(sel_vec, str):
                        sel_vec = json.loads(sel_vec)
                    sim = cls._cosine_similarity(cand_vec, sel_vec)
                    if sim > max_sim_selected:
                        max_sim_selected = sim
                        
                mmr_score = lambda_val * cand_score - (1.0 - lambda_val) * max_sim_selected
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_cand = (cand_score, cand_chunk)
                    
            if best_cand:
                selected.append(best_cand)
                remaining.remove(best_cand)
            else:
                break
                
        return selected

    @classmethod
    def cross_encoder_rerank(
        cls,
        db: Session,
        candidates: List[Tuple[float, DocumentChunk]],
        query_text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Use LLM/AI Gateway to evaluate chunk relevance or perform high-fidelity cosine re-weighting.
        """
        if not candidates:
            return []
            
        # Simulating cross-encoder scoring in non-production, or calling AI Gateway to sort chunks
        from api.core.config import settings
        if settings.ENVIRONMENT != "production":
            # Heuristic reranking: boost chunks containing exact query terms
            boosted = []
            for score, chunk in candidates:
                multiplier = 1.0
                if any(word in chunk.content.lower() for word in query_text.lower().split()):
                    multiplier = 1.15
                boosted.append((min(1.0, score * multiplier), chunk))
            boosted.sort(key=lambda x: x[0], reverse=True)
            return boosted[:limit]
            
        # Production: use cheap model to re-score the top candidates
        try:
            from api.ai.coordinator import AIGateway
            gateway = AIGateway()
            
            # Pack candidates
            prompt = (
                f"You are a search ranking model. Given the user query: '{query_text}', "
                f"evaluate the following {len(candidates)} document chunks. "
                f"For each chunk, output a relevance score between 0.0 (completely irrelevant) and 1.0 (highly relevant). "
                f"Respond only in structured JSON format like: {{'scores': [0.95, 0.40, ...]}} mapping index order.\n\n"
            )
            for idx, (score, chunk) in enumerate(candidates):
                prompt += f"Chunk [{idx}]: \"{chunk.content[:400]}\"\n---\n"
                
            res = gateway.json_output(
                db=db,
                messages=[{"role": "user", "content": prompt}],
                schema={
                    "type": "object",
                    "properties": {
                        "scores": {
                            "type": "array",
                            "items": {"type": "number"}
                        }
                    },
                    "required": ["scores"]
                },
                organization_id=organization_id,
                user_id=user_id
            )
            
            scores = res.get("scores", [])
            reranked = []
            for idx, (score, chunk) in enumerate(candidates):
                new_score = scores[idx] if idx < len(scores) else score
                reranked.append((new_score, chunk))
                
            reranked.sort(key=lambda x: x[0], reverse=True)
            return reranked[:limit]
        except Exception as e:
            logger.error(f"Cross encoder reranking failed, fallback to standard scores: {e}")
            return candidates[:limit]
