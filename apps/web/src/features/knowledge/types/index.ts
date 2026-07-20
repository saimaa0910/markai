export interface KnowledgeDocument {
  id: string;
  title: string;
  file_type: string;
  organization_id: string;
  user_id?: string;
  file_size?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'indexed' | 'embedding';
  is_favorite: boolean;
  is_archived: boolean;
  is_trash: boolean;
  tags: string[];
  created_at: string;
  chunk_count?: number;
  collection_id?: string;
  folder_id?: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  organization_id: string;
  content: string;
  similarity?: number;
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
  document_ids: string[];
  organization_id: string;
  created_at: string;
}

export interface EmbeddingModel {
  name: string;
  provider: string;
  dimensions: number;
  status: 'active' | 'degraded';
}

export interface KnowledgeSettings {
  chunk_size: number;
  chunk_overlap: number;
  embedding_model: string;
  auto_index: boolean;
  auto_embed: boolean;
  duplicate_detection: boolean;
}

export interface Folder {
  id: string;
  name: string;
  collection_id: string;
  parent_id?: string;
  organization_id: string;
  created_at: string;
}

export interface RAGCitation {
  document_id: string;
  document_name: string;
  collection_name?: string;
  folder_name?: string;
  page_number?: number;
  chunk_index?: number;
  similarity_score: number;
  short_snippet: string;
}

export interface RAGResponse {
  answer: string;
  citations: RAGCitation[];
  confidence_score: number;
  similarity_score: number;
  context_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  retrieved_chunks_count: number;
  hallucination_risk: 'LOW' | 'MEDIUM' | 'HIGH';
  latency?: {
    total_ms: number;
    embedding_ms: number;
    retrieval_ms: number;
    inference_ms: number;
  };
}

export interface QueueJob {
  id: string;
  document_id: string;
  organization_id: string;
  task_id?: string;
  status: 'PENDING' | 'QUEUED' | 'RUNNING' | 'RETRY' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress: number;
  step: 'VIRUS_SCAN' | 'OCR' | 'EXTRACT_TEXT' | 'CLEAN_TEXT' | 'CHUNK' | 'EMBEDDING' | 'VECTOR_STORE';
  error_message?: string;
  created_at: string;
}

export interface DashboardStats {
  stats: {
    document_count: number;
    collection_count: number;
    folder_count: number;
    total_storage_bytes: number;
    storage_allocated_kb: number;
    indexed_ratio: number;
  };
  top_collections: Array<{
    id: string;
    name: string;
    document_count: number;
    queries_count: number;
  }>;
  recent_uploads: Array<{
    id: string;
    title: string;
    file_type: string;
    file_size: number;
    created_at: string;
  }>;
  storage_growth_history: Array<{
    date: string;
    storage_kb: number;
    queries: number;
  }>;
}

