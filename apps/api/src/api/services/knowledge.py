import uuid
import math
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from api.models.knowledge import KnowledgeDocument, DocumentChunk
from api.ai.gateway.coordinator import AIGateway
from api.schemas.ai import KnowledgeUploadRequest


class KnowledgeService:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Slice text using a character-based sliding window.
        """
        chunks = []
        start = 0
        if not text:
            return []
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
            if start >= len(text) or chunk_size <= overlap:
                break
        return chunks

    @classmethod
    def upload_document(
        self,
        db: Session,
        doc_in: KnowledgeUploadRequest,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> KnowledgeDocument:
        """
        Upload document, slice into overlapping chunks, generate embeddings,
        and store the records in the database.
        """
        # 1. Create document entry
        doc = KnowledgeDocument(
            title=doc_in.title,
            file_type=doc_in.file_type,
            organization_id=organization_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 2. Slice text content
        text_slices = self.chunk_text(doc_in.content)
        gateway = AIGateway()

        # 3. Embed and store chunks
        for chunk_text in text_slices:
            # Generate 1536-dimensional embedding using gateway embeddings
            embedding_vector = gateway.embeddings(
                db=db,
                text=chunk_text,
                organization_id=organization_id,
                user_id=user_id,
            )

            chunk = DocumentChunk(
                document_id=doc.id,
                organization_id=organization_id,
                content=chunk_text,
                embedding=embedding_vector,
            )
            db.add(chunk)
        
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @classmethod
    def query_similar_chunks(
        self,
        db: Session,
        query_text: str,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 3,
    ) -> List[DocumentChunk]:
        """
        Perform vector similarity search. Use native pgvector operators on PostgreSQL,
        otherwise fall back to in-memory Python calculations on SQLite/development setups.
        """
        gateway = AIGateway()
        query_embedding = gateway.embeddings(
            db=db, text=query_text, organization_id=organization_id, user_id=user_id
        )

        if db.bind.dialect.name == "postgresql":
            try:
                # Use pgvector.sqlalchemy's cosine_distance operator if pgvector is available
                query = (
                    select(DocumentChunk)
                    .where(DocumentChunk.organization_id == organization_id)
                    .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                    .limit(limit)
                )
                return list(db.scalars(query).all())
            except Exception:
                pass  # Fall back to Python calculation if pgvector operator failed

        # SQLite/In-Memory Python fallback similarity logic
        all_chunks = list(
            db.scalars(
                select(DocumentChunk).where(DocumentChunk.organization_id == organization_id)
            ).all()
        )

        # Calculate cosine similarity score for each candidate chunk
        scored_chunks = []
        for chunk in all_chunks:
            # Ensure chunk.embedding is parsed if represented as string/JSON in DB
            vec = chunk.embedding
            if isinstance(vec, str):
                import json
                try:
                    vec = json.loads(vec)
                except Exception:
                    pass
            
            if isinstance(vec, list):
                score = self._cosine_similarity(query_embedding, vec)
                scored_chunks.append((score, chunk))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:limit]]
