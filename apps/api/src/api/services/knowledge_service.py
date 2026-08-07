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
        Perform vector similarity search using native pgvector operators.
        """
        gateway = AIGateway()
        query_embedding = gateway.embeddings(
            db=db, text=query_text, organization_id=organization_id, user_id=user_id
        )

        from api.models.knowledge import DocumentChunkEmbedding
        query = (
            select(DocumentChunk)
            .join(DocumentChunkEmbedding, DocumentChunk.id == DocumentChunkEmbedding.chunk_id)
            .where(DocumentChunk.organization_id == organization_id)
            .order_by(DocumentChunkEmbedding.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(db.scalars(query).all())
