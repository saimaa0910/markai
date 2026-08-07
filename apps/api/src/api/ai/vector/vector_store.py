import uuid
from typing import List, Dict, Any
from sqlalchemy import select
from api.models.knowledge import DocumentChunkEmbedding
from api.database.session import SessionLocal


class PgVectorStore:
    """
    PostgreSQL pgvector storage abstraction.
    """
    async def upsert_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        Upsert vector embedding and metadata into pgvector table.
        """
        db = SessionLocal()
        try:
            chunk_uuid = uuid.UUID(vector_id)
            existing = db.query(DocumentChunkEmbedding).filter_by(chunk_id=chunk_uuid).first()
            if existing:
                existing.embedding = embedding
            else:
                new_emb = DocumentChunkEmbedding(
                    chunk_id=chunk_uuid,
                    organization_id=uuid.UUID(metadata.get("organization_id", str(uuid.uuid4()))),
                    embedding=embedding,
                    embedding_model=metadata.get("embedding_model", "openai:text-embedding-3-small")
                )
                db.add(new_emb)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Execute cosine / L2 distance similarity search in pgvector.
        """
        db = SessionLocal()
        try:
            # We can use cosine_distance from pgvector:
            stmt = select(DocumentChunkEmbedding).order_by(
                DocumentChunkEmbedding.embedding.cosine_distance(query_embedding)
            ).limit(limit)
            results = db.scalars(stmt).all()
            
            output = []
            for r in results:
                output.append({
                    "chunk_id": str(r.chunk_id),
                    "organization_id": str(r.organization_id),
                    "embedding": r.embedding,
                    "embedding_model": r.embedding_model
                })
            return output
        except Exception:
            return []
        finally:
            db.close()


vector_store = PgVectorStore()

