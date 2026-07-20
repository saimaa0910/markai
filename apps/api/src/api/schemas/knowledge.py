import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- COLLECTION SCHEMAS ---

class CollectionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    visibility: str = "ORGANIZATION"  # ORGANIZATION, TEAM, PRIVATE, PUBLIC

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    visibility: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None

class CollectionResponse(CollectionBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    is_archived: bool
    is_favorite: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- FOLDER SCHEMAS ---

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=255)
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None

class FolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    collection_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- DOCUMENT SCHEMAS ---

class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    content: str
    chunk_index: Optional[int] = None
    page_number: Optional[int] = None

    class Config:
        from_attributes = True


class KnowledgeDocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_type: str
    organization_id: uuid.UUID
    collection_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    file_size: Optional[int] = None
    storage_url: Optional[str] = None
    is_archived: bool
    is_favorite: bool
    is_pinned: bool
    status: str
    progress: float
    error_message: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    department: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None
    current_version: int
    metadata_info: Optional[Dict[str, Any]] = None
    chunks: Optional[List[DocumentChunkResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    collection_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    department: Optional[str] = None

# --- VERSION SCHEMAS ---

class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version: int
    title: str
    file_type: str
    file_size: int
    storage_url: str
    content: Optional[str] = None
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VersionCompareResponse(BaseModel):
    version_a: int
    version_b: int
    title_changed: bool
    size_diff_bytes: int
    diff_summary: str

# --- PROCESSING QUEUE SCHEMAS ---

class ProcessingJobResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    organization_id: uuid.UUID
    task_id: Optional[str] = None
    status: str
    progress: float
    step: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- PERMISSIONS SCHEMAS ---

class KnowledgePermissionCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    role: str = "VIEWER"  # VIEWER, EDITOR, ADMIN

class KnowledgePermissionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    collection_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- SEARCH & RAG SCHEMAS ---

class SearchFilters(BaseModel):
    collection_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    department: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    file_types: Optional[List[str]] = None

class KnowledgeSearchRequest(BaseModel):
    query_text: str
    limit: int = 5
    search_type: str = "HYBRID"  # SEMANTIC, KEYWORD, HYBRID
    filters: Optional[SearchFilters] = None

class SearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    file_type: str
    content: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    similarity_score: float
    collection_name: Optional[str] = None
    folder_name: Optional[str] = None

class SearchHistoryResponse(BaseModel):
    id: uuid.UUID
    query_text: str
    search_type: str
    filters_applied: Optional[Dict[str, Any]] = None
    results_count: int
    latency_ms: int
    created_at: datetime

    class Config:
        from_attributes = True

class SavedSearchCreate(BaseModel):
    name: str
    query_text: str
    search_type: str = "HYBRID"
    filters_applied: Optional[Dict[str, Any]] = None

class SavedSearchResponse(BaseModel):
    id: uuid.UUID
    name: str
    query_text: str
    search_type: str
    filters_applied: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    query_text: str
    conversation_id: Optional[uuid.UUID] = None
    limit: int = 5
    search_type: str = "HYBRID"
    filters: Optional[SearchFilters] = None
    collection_prompt: Optional[str] = None
    organization_prompt: Optional[str] = None
    system_prompt: Optional[str] = None

class RAGCitation(BaseModel):
    document_id: uuid.UUID
    document_name: str
    collection_name: Optional[str] = None
    folder_name: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    similarity_score: float
    short_snippet: str

class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[RAGCitation]
    confidence_score: float
    confidence_badge: str  # LOW, MEDIUM, HIGH
    similarity_score: float
    context_tokens: int
    prompt_tokens: int
    completion_tokens: int
    retrieved_chunks_count: int
    hallucination_risk: str  # LOW, MEDIUM, HIGH

# --- DASHBOARD & ANALYTICS SCHEMAS ---

class KnowledgeStatsResponse(BaseModel):
    document_count: int
    collection_count: int
    folder_count: int
    total_storage_bytes: int
    storage_allocated_kb: float
    indexed_ratio: float

class TopCollectionStats(BaseModel):
    id: uuid.UUID
    name: str
    document_count: int
    queries_count: int

class RecentUploadItem(BaseModel):
    id: uuid.UUID
    title: str
    file_type: str
    file_size: int
    created_at: datetime

class KnowledgeDashboardResponse(BaseModel):
    stats: KnowledgeStatsResponse
    top_collections: List[TopCollectionStats]
    recent_uploads: List[RecentUploadItem]
    storage_growth_history: List[Dict[str, Any]]  # date, storage_kb, queries
