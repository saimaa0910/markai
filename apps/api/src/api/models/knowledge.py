import uuid
import json
from typing import Optional, List, Any
from sqlalchemy import ForeignKey, String, Text, TypeDecorator, JSON, Integer, Float, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class SafeVector(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dimensions))
            except ImportError:
                return dialect.type_descriptor(Text)
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class KnowledgeCollection(Base):
    __tablename__ = "knowledge_collections"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="ORGANIZATION", nullable=False)  # ORGANIZATION, TEAM, PRIVATE, PUBLIC

    # Relationships
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="collection", cascade="all, delete-orphan"
    )
    folders: Mapped[List["KnowledgeFolder"]] = relationship(
        "KnowledgeFolder", back_populates="collection", cascade="all, delete-orphan"
    )


class KnowledgeFolder(Base):
    __tablename__ = "knowledge_folders"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    collection: Mapped["KnowledgeCollection"] = relationship("KnowledgeCollection", back_populates="folders")
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="folder"
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, csv, md, url
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Extensions
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_info: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    collection: Mapped[Optional["KnowledgeCollection"]] = relationship(
        "KnowledgeCollection", back_populates="documents"
    )
    folder: Mapped[Optional["KnowledgeFolder"]] = relationship(
        "KnowledgeFolder", back_populates="documents"
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    versions: Mapped[List["KnowledgeDocumentVersion"]] = relationship(
        "KnowledgeDocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["KnowledgeProcessingJob"]] = relationship(
        "KnowledgeProcessingJob", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", back_populates="versions"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    __table_args__ = (
        UniqueConstraint("document_id", "content_hash", name="uq_chunk_content_hash_doc"),
        Index("idx_doc_chunks_doc_id", "document_id"),
        Index("idx_doc_chunks_org_id", "organization_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_dimensions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", back_populates="chunks"
    )
    embeddings: Mapped[List["DocumentChunkEmbedding"]] = relationship(
        "DocumentChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        if "content" in kwargs and "content_hash" not in kwargs:
            import hashlib
            kwargs["content_hash"] = hashlib.sha256(kwargs["content"].encode("utf-8")).hexdigest()
        if "chunk_index" not in kwargs:
            kwargs["chunk_index"] = 0
        
        # Pull embedding out if passed
        embedding_val = kwargs.pop("embedding", None)
        super().__init__(**kwargs)
        if embedding_val is not None:
            self.embedding = embedding_val

    @property
    def embedding(self) -> Optional[list[float]]:
        if self.embeddings:
            return self.embeddings[0].embedding
        return None

    @embedding.setter
    def embedding(self, val: list[float]) -> None:
        self.embeddings = [
            DocumentChunkEmbedding(
                embedding=val,
                embedding_model=self.embedding_model or "openai:text-embedding-3-small",
                organization_id=self.organization_id,
            )
        ]


class DocumentChunkEmbedding(Base):
    __tablename__ = "document_chunk_embeddings"

    __table_args__ = (
        Index("idx_embeddings_org_model", "organization_id", "embedding_model"),
        Index("idx_embeddings_chunk_id", "chunk_id"),
    )

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(SafeVector(1536), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    chunk: Mapped[DocumentChunk] = relationship("DocumentChunk", back_populates="embeddings")


class KnowledgeRetrievalLog(Base):
    """
    Audit log of RAG retrievals for tracking accuracy and AI quality.
    """
    __tablename__ = "knowledge_retrieval_logs"

    __table_args__ = (
        Index("idx_knowledge_retrieval_org", "organization_id", "created_at"),
        Index("idx_knowledge_retrieval_user", "user_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    collection_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(JSON, nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    search_type: Mapped[str] = mapped_column(String(20), default="semantic", nullable=False)
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chunk_ids_returned: Mapped[Optional[list[uuid.UUID]]] = mapped_column(JSON, nullable=True)


class KnowledgeProcessingJob(Base):
    __tablename__ = "knowledge_processing_jobs"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, QUEUED, RUNNING, RETRY, COMPLETED, FAILED, CANCELLED
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    step: Mapped[str] = mapped_column(String(50), default="UPLOAD", nullable=False)  # VIRUS_SCAN, OCR, EXTRACT_TEXT, CLEAN_TEXT, CHUNK, EMBEDDING, VECTOR_STORE
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(
        "KnowledgeDocument", back_populates="processing_jobs"
    )


class KnowledgeSearchHistory(Base):
    __tablename__ = "knowledge_search_history"

    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    search_type: Mapped[str] = mapped_column(String(50), default="SEMANTIC", nullable=False)  # SEMANTIC, KEYWORD, HYBRID
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class KnowledgeSavedSearch(Base):
    __tablename__ = "knowledge_saved_searches"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    search_type: Mapped[str] = mapped_column(String(50), default="SEMANTIC", nullable=False)
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class KnowledgePermission(Base):
    __tablename__ = "knowledge_permissions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(50), default="VIEWER", nullable=False)  # VIEWER, EDITOR, ADMIN

