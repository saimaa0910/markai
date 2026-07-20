import { apiClient } from '@/services/api-client';
import { KnowledgeDocument, Collection, Folder, DocumentChunk, RAGResponse, QueueJob, DashboardStats } from '../types';

export const KnowledgeAPI = {
  // --- DOCUMENTS ---
  listDocuments: async (): Promise<KnowledgeDocument[]> => {
    const res = await apiClient.get('/ai/knowledge/documents');
    return res.data || [];
  },

  getDocument: async (id: string): Promise<KnowledgeDocument> => {
    const res = await apiClient.get(`/ai/knowledge/documents/${id}`);
    return res.data;
  },

  updateDocument: async (id: string, data: any): Promise<KnowledgeDocument> => {
    const res = await apiClient.patch(`/ai/knowledge/documents/${id}`, data);
    return res.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/ai/knowledge/documents/${id}`);
  },

  archiveDocument: async (id: string): Promise<KnowledgeDocument> => {
    const res = await apiClient.post(`/ai/knowledge/documents/${id}/archive`);
    return res.data;
  },

  favoriteDocument: async (id: string): Promise<KnowledgeDocument> => {
    const res = await apiClient.post(`/ai/knowledge/documents/${id}/favorite`);
    return res.data;
  },

  pinDocument: async (id: string): Promise<KnowledgeDocument> => {
    const res = await apiClient.post(`/ai/knowledge/documents/${id}/pin`);
    return res.data;
  },

  duplicateDocument: async (id: string): Promise<KnowledgeDocument> => {
    const res = await apiClient.post(`/ai/knowledge/documents/${id}/duplicate`);
    return res.data;
  },

  getDocumentVersions: async (id: string): Promise<any[]> => {
    const res = await apiClient.get(`/ai/knowledge/documents/${id}/versions`);
    return res.data || [];
  },

  restoreDocumentVersion: async (id: string, version: number): Promise<KnowledgeDocument> => {
    const res = await apiClient.post(`/ai/knowledge/documents/${id}/versions/${version}/restore`);
    return res.data;
  },

  compareDocumentVersions: async (id: string, vA: number, vB: number): Promise<any> => {
    const res = await apiClient.get(`/ai/knowledge/documents/${id}/versions/compare?version_a=${vA}&version_b=${vB}`);
    return res.data;
  },

  // --- COLLECTIONS ---
  listCollections: async (): Promise<Collection[]> => {
    const res = await apiClient.get('/ai/knowledge/collections');
    return res.data || [];
  },

  createCollection: async (name: string, description?: string, parentId?: string, visibility?: string): Promise<Collection> => {
    const res = await apiClient.post('/ai/knowledge/collections', {
      name,
      description,
      parent_id: parentId,
      visibility: visibility || 'ORGANIZATION',
    });
    return res.data;
  },

  updateCollection: async (id: string, data: any): Promise<Collection> => {
    const res = await apiClient.patch(`/ai/knowledge/collections/${id}`, data);
    return res.data;
  },

  deleteCollection: async (id: string): Promise<void> => {
    await apiClient.delete(`/ai/knowledge/collections/${id}`);
  },

  archiveCollection: async (id: string): Promise<Collection> => {
    const res = await apiClient.post(`/ai/knowledge/collections/${id}/archive`);
    return res.data;
  },

  favoriteCollection: async (id: string): Promise<Collection> => {
    const res = await apiClient.post(`/ai/knowledge/collections/${id}/favorite`);
    return res.data;
  },

  pinCollection: async (id: string): Promise<Collection> => {
    const res = await apiClient.post(`/ai/knowledge/collections/${id}/pin`);
    return res.data;
  },

  // --- FOLDERS ---
  listFolders: async (): Promise<Folder[]> => {
    const res = await apiClient.get('/ai/knowledge/folders');
    return res.data || [];
  },

  createFolder: async (name: string, collectionId: string, parentId?: string): Promise<Folder> => {
    const res = await apiClient.post('/ai/knowledge/folders', {
      name,
      collection_id: collectionId,
      parent_id: parentId,
    });
    return res.data;
  },

  updateFolder: async (id: string, name: string, parentId?: string): Promise<Folder> => {
    const res = await apiClient.patch(`/ai/knowledge/folders/${id}`, { name, parent_id: parentId });
    return res.data;
  },

  deleteFolder: async (id: string): Promise<void> => {
    await apiClient.delete(`/ai/knowledge/folders/${id}`);
  },

  // --- UPLOAD PIPELINE ---
  uploadAndIndex: async (
    file: File,
    onProgress?: (progress: number) => void,
    options?: {
      collection_id?: string;
      folder_id?: string;
      chunk_size?: number;
      chunk_overlap?: number;
      strategy?: string;
      embedding_model?: string;
    }
  ): Promise<KnowledgeDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.collection_id) formData.append('collection_id', options.collection_id);
    if (options?.folder_id) formData.append('folder_id', options.folder_id);
    formData.append('chunk_size', String(options?.chunk_size || 500));
    formData.append('chunk_overlap', String(options?.chunk_overlap || 100));
    formData.append('strategy', options?.strategy || 'recursive');
    formData.append('embedding_model', options?.embedding_model || 'text-embedding-3-small');

    const res = await apiClient.post('/ai/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    // Trigger simulated progress increments
    let progress = 0;
    const interval = setInterval(() => {
      progress = Math.min(progress + 15, 95);
      onProgress?.(progress);
    }, 400);

    // Call stats or list docs to check completion
    setTimeout(() => {
      clearInterval(interval);
      onProgress?.(100);
    }, 3000);

    return res.data;
  },

  // --- PROCESSING QUEUE ---
  listQueueJobs: async (): Promise<QueueJob[]> => {
    const res = await apiClient.get('/ai/knowledge/queue');
    return res.data || [];
  },

  cancelQueueJob: async (id: string): Promise<void> => {
    await apiClient.post(`/ai/knowledge/queue/${id}/cancel`);
  },

  retryQueueJob: async (id: string): Promise<void> => {
    await apiClient.post(`/ai/knowledge/queue/${id}/retry`);
  },

  // --- SEARCH & RAG ---
  querySimilarChunks: async (queryText: string, limit: number = 5, searchType: string = 'HYBRID', filters?: any): Promise<DocumentChunk[]> => {
    const res = await apiClient.post('/ai/knowledge/search', {
      query_text: queryText,
      limit,
      search_type: searchType,
      filters,
    });
    return res.data || [];
  },

  queryRAG: async (
    queryText: string,
    conversationId?: string,
    limit: number = 5,
    searchType: string = 'HYBRID',
    filters?: any
  ): Promise<RAGResponse> => {
    const res = await apiClient.post('/ai/knowledge/rag', {
      query_text: queryText,
      conversation_id: conversationId,
      limit,
      search_type: searchType,
      filters,
    });
    return res.data;
  },

  getSearchHistory: async (): Promise<any[]> => {
    const res = await apiClient.get('/ai/knowledge/search/history');
    return res.data || [];
  },

  // --- DASHBOARD & ANALYTICS ---
  getDashboardStats: async (): Promise<DashboardStats> => {
    const res = await apiClient.get('/ai/knowledge/dashboard/stats');
    return res.data;
  },
};

