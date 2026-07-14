export interface KnowledgeDocument {
  id: string;
  title: string;
  file_type: string;
  organization_id: string;
  user_id?: string;
  file_size?: number;
  status: 'indexed' | 'embedding' | 'failed';
  is_favorite: boolean;
  is_archived: boolean;
  is_trash: boolean;
  tags: string[];
  created_at: string;
  chunk_count?: number;
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
