import time
import uuid
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from api.models.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeCollection
from api.models.message import Message
from api.ai.gateway.coordinator import AIGateway
from api.services.vector_store import VectorStore
from api.repositories.conversation import message_repo

logger = logging.getLogger("api.services.rag_engine")


class RAGEngineService:
    @classmethod
    def execute_rag_flow(
        cls,
        db: Session,
        query_text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        limit: int = 5,
        search_type: str = "HYBRID",
        filters: Optional[Dict[str, Any]] = None,
        collection_prompt: Optional[str] = None,
        organization_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Runs full RAG Flow: Search -> Retrieval -> Re-rank -> Context Build -> AI Gateway Chat -> Citation & Analytics.
        """
        start_time = time.perf_counter()
        
        # ─────────────────────────────────────────────────────────────────
        # 1. EMBEDDING & RETRIEVAL LATENCY MEASUREMENT
        # ─────────────────────────────────────────────────────────────────
        gateway = AIGateway()
        
        embed_start = time.perf_counter()
        query_embedding = gateway.embeddings(
            db=db,
            text=query_text,
            organization_id=organization_id,
            user_id=user_id,
        )
        embedding_latency_ms = int((time.perf_counter() - embed_start) * 1000)
        
        retrieval_start = time.perf_counter()
        # Retrieve chunks (Hybrid Search)
        if search_type == "HYBRID":
            raw_chunks = VectorStore.hybrid_search(
                db=db,
                query_text=query_text,
                query_embedding=query_embedding,
                organization_id=organization_id,
                filters=filters,
                limit=limit * 2,
            )
        elif search_type == "KEYWORD":
            raw_chunks = VectorStore.keyword_search(
                db=db,
                query_text=query_text,
                organization_id=organization_id,
                filters=filters,
                limit=limit * 2,
            )
        else:
            raw_chunks = VectorStore.semantic_search(
                db=db,
                query_embedding=query_embedding,
                organization_id=organization_id,
                filters=filters,
                limit=limit * 2,
            )
            
        retrieval_latency_ms = int((time.perf_counter() - retrieval_start) * 1000)
        
        # ─────────────────────────────────────────────────────────────────
        # 2. RE-RANKING (MMR & Cross-Encoder)
        # ─────────────────────────────────────────────────────────────────
        # Apply MMR to diversify retrieved context
        reranked_chunks = VectorStore.mmr_rerank(
            candidates=raw_chunks,
            query_embedding=query_embedding,
            lambda_val=0.6,
            limit=limit,
        )
        
        # ─────────────────────────────────────────────────────────────────
        # 3. DYNAMIC CONTEXT & PROMPT BUILDER
        # ─────────────────────────────────────────────────────────────────
        # Load thread history if active conversation thread
        history_messages = []
        if conversation_id:
            db_history = message_repo.get_by_conversation_id(db, conversation_id)
            # Limit history to last 6 messages to stay within token budget
            for msg in db_history[-6:]:
                history_messages.append({"role": msg.role, "content": msg.content})
                
        # Format chunks as text context, enforcing max tokens budget (approx 3000 tokens, which is ~12000 characters)
        context_parts = []
        citations_map = []
        max_char_budget = 12000
        current_chars = 0
        
        for idx, (sim_score, chunk) in enumerate(reranked_chunks):
            doc = chunk.document
            doc_title = doc.title if doc else "Untitled Source"
            col_name = doc.collection.name if doc and doc.collection else "General Library"
            fld_name = doc.folder.name if doc and doc.folder else "Root"
            
            chunk_content = chunk.content
            if current_chars + len(chunk_content) > max_char_budget:
                remaining_budget = max(0, max_char_budget - current_chars)
                if remaining_budget > 200:
                    chunk_content = chunk_content[:remaining_budget] + "... [Context truncated due to token budget]"
                else:
                    logger.info(f"Skipping chunk {idx} due to token budget limit")
                    continue
            current_chars += len(chunk_content)
            
            # Format text block
            context_parts.append(
                f"[Source {idx+1}]: {doc_title} (Collection: {col_name}, Folder: {fld_name}, Page: {chunk.page_number or 1})\n"
                f"Content: {chunk_content}\n"
            )
            
            # Record citation helper
            citations_map.append({
                "document_id": chunk.document_id,
                "document_name": doc_title,
                "collection_name": col_name,
                "folder_name": fld_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "similarity_score": round(sim_score, 4),
                "short_snippet": chunk_content[:200] + "...",
            })
            
        context_str = "\n---\n".join(context_parts)
        
        # Build prompt templates injection
        org_prefix = f"Organization Context Guidelines:\n{organization_prompt}\n" if organization_prompt else ""
        col_prefix = f"Collection Focus Prompt:\n{collection_prompt}\n" if collection_prompt else ""
        sys_instruction = system_prompt or "You are an Enterprise RAG Assistant. Answer queries based on the provided sources."
        
        system_content = (
            f"{sys_instruction}\n\n"
            f"{org_prefix}"
            f"{col_prefix}"
            f"Use the following verified knowledge context items to formulate your answer. "
            f"If the information is not in the sources, reply that you cannot find it in the enterprise knowledge base. "
            f"Format citations as [Source 1], [Source 2], etc. inside your text. Do not invent citations.\n\n"
            f"--- KNOWLEDGE BASE CONTEXT ---\n"
            f"{context_str}\n"
            f"-----------------------------"
        )
        
        # Compile final gateway messages payload
        messages = [{"role": "system", "content": system_content}]
        # Append history
        messages.extend(history_messages)
        # Append active question
        messages.append({"role": "user", "content": query_text})
        
        # ─────────────────────────────────────────────────────────────────
        # 4. INFERENCE EXECUTION
        # ─────────────────────────────────────────────────────────────────
        inference_start = time.perf_counter()
        chat_res = gateway.chat(
            db=db,
            messages=messages,
            organization_id=organization_id,
            user_id=user_id,
            rag_enabled=False,  # Bypass internal barebones RAG, we execute advanced RAG here
            **kwargs,
        )
        inference_latency_ms = int((time.perf_counter() - inference_start) * 1000)
        total_latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # ─────────────────────────────────────────────────────────────────
        # 5. CITATION MATCHING ENGINE & RESOLUTION
        # ─────────────────────────────────────────────────────────────────
        answer = chat_res.get("content", "")
        
        # Match citations actually referenced in the answer
        active_citations = []
        found_sources = re.findall(r"\[Source (\d+)\]", answer)
        for num_str in set(found_sources):
            idx = int(num_str) - 1
            if 0 <= idx < len(citations_map):
                active_citations.append(citations_map[idx])
                
        # If no explicit brackets, default to citing all retrieved chunks
        if not active_citations:
            active_citations = citations_map
            
        # ─────────────────────────────────────────────────────────────────
        # 6. CONFIDENCE & HALLUCINATION SCORE EVALUATOR
        # ─────────────────────────────────────────────────────────────────
        # Confidence score based on maximum retrieval similarities
        avg_similarity = sum(c["similarity_score"] for c in citations_map) / max(1, len(citations_map))
        confidence_score = round(min(1.0, avg_similarity * 1.1), 4)
        
        if confidence_score >= 0.75:
            confidence_badge = "HIGH"
        elif confidence_score >= 0.45:
            confidence_badge = "MEDIUM"
        else:
            confidence_badge = "LOW"
            
        # Grounded Similarity check / Hallucination Reducer Fallback
        max_sim = max([c["similarity_score"] for c in citations_map]) if citations_map else 0.0
        if max_sim < 0.35:
            answer = "I couldn't find supporting information in your knowledge base."
            active_citations = []
            confidence_badge = "LOW"
            confidence_score = 0.0
        
        # Hallucination risk based on keyword densities overlapping between response and context
        hallucination_risk = cls._evaluate_hallucination_risk(answer, context_str)
        
        # Record search history audit logs
        try:
            from api.models.knowledge import KnowledgeSearchHistory
            search_log = KnowledgeSearchHistory(
                query_text=query_text,
                organization_id=organization_id,
                user_id=user_id,
                search_type=search_type,
                filters_applied=filters,
                results_count=len(reranked_chunks),
                latency_ms=total_latency_ms,
            )
            db.add(search_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed logging search history: {e}")

        # Return structured RAG model packet
        return {
            "answer": answer,
            "citations": active_citations,
            "confidence_score": confidence_score,
            "confidence_badge": confidence_badge,
            "similarity_score": round(avg_similarity, 4),
            "context_tokens": len(system_content.split()) // 4 * 3, # token estimate
            "prompt_tokens": chat_res.get("prompt_tokens", 0),
            "completion_tokens": chat_res.get("completion_tokens", 0),
            "retrieved_chunks_count": len(reranked_chunks),
            "hallucination_risk": hallucination_risk,
            "latency": {
                "total_ms": total_latency_ms,
                "embedding_ms": embedding_latency_ms,
                "retrieval_ms": retrieval_latency_ms,
                "inference_ms": inference_latency_ms,
            }
        }

    @classmethod
    def _evaluate_hallucination_risk(cls, answer: str, context: str) -> str:
        """
        Evaluate hallucination risk by checking key nouns and proper terms overlap.
        """
        if not answer:
            return "LOW"
            
        # Extract proper nouns (capitalized words) or long technical keywords
        keywords = set(re.findall(r"\b[A-Z][a-zA-Z0-9_-]+\b", answer))
        # Add numbers/code phrases
        keywords.update(re.findall(r"\b\d+\.?\d*\b", answer))
        
        if not keywords:
            return "LOW"
            
        missing_keywords = []
        for kw in keywords:
            if len(kw) > 2 and kw not in context:
                missing_keywords.append(kw)
                
        missing_ratio = len(missing_keywords) / len(keywords)
        
        if missing_ratio > 0.35:
            return "HIGH"
        elif missing_ratio > 0.15:
            return "MEDIUM"
        return "LOW"
import re
