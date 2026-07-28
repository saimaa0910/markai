"""
EAIMOS Knowledge Base DTOs
===========================
Pydantic v2 DTOs for Sprint 8 Knowledge Base, Document Ingestion & Vector Indexing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Collection DTOs
# =============================================================================

class CreateKnowledgeCollectionDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: str = Field("ORGANIZATION", description="ORGANIZATION | TEAM | PRIVATE | PUBLIC")


class KnowledgeCollectionResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    visibility: str
    is_archived: bool = False
    is_favorite: bool = False
    is_pinned: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Document & Chunk DTOs
# =============================================================================

class IngestDocumentDTO(BaseModel):
    collection_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    raw_content: str = Field(..., min_length=1)
    chunk_size: int = Field(512, ge=64, le=4096)
    chunk_overlap: int = Field(64, ge=0, le=512)


class DocumentResponseDTO(BaseModel):
    id: uuid.UUID
    collection_id: uuid.UUID
    title: str
    status: str = "INDEXED"
    total_chunks: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Vector Search DTOs
# =============================================================================

class VectorSearchQueryDTO(BaseModel):
    collection_id: uuid.UUID
    query_text: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=100)
    min_score: float = Field(0.7, ge=0.0, le=1.0)


class VectorSearchResultDTO(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    score: float
    text_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
