import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { KnowledgeAPI } from '../services/knowledge';
import { useKnowledgeStore } from '../store/knowledge';
import { KnowledgeDocument, Collection, Folder, DocumentChunk, RAGResponse, QueueJob, DashboardStats } from '../types';

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Documents
// ─────────────────────────────────────────────────────────────────────────────
export function useDocuments() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();
  const { favorites, archived, trash } = useKnowledgeStore();

  const query = useQuery<KnowledgeDocument[]>({
    queryKey: ['knowledge-documents', activeOrg?.id],
    queryFn: async () => {
      const docs = await KnowledgeAPI.listDocuments();
      return docs.map((doc) => ({
        ...doc,
        is_favorite: doc.is_favorite || favorites.includes(doc.id),
        is_archived: doc.is_archived || archived.includes(doc.id),
        is_trash: doc.is_trash || trash.includes(doc.id),
      }));
    },
    enabled: !!activeOrg,
  });

  const deleteDoc = useMutation({
    mutationFn: async (id: string) => {
      await KnowledgeAPI.deleteDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-dashboard-stats'] });
    },
  });

  const toggleFavorite = useMutation({
    mutationFn: async (id: string) => {
      return await KnowledgeAPI.favoriteDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });

  const toggleArchive = useMutation({
    mutationFn: async (id: string) => {
      return await KnowledgeAPI.archiveDocument(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });

  return {
    documents: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    deleteDoc,
    toggleFavorite,
    toggleArchive,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Single Document details
// ─────────────────────────────────────────────────────────────────────────────
export function useDocument(id: string | null) {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<KnowledgeDocument | null>({
    queryKey: ['knowledge-document', id],
    queryFn: async () => {
      if (!id) return null;
      return await KnowledgeAPI.getDocument(id);
    },
    enabled: !!id && !!activeOrg,
  });

  const versionsQuery = useQuery<any[]>({
    queryKey: ['knowledge-document-versions', id],
    queryFn: async () => {
      if (!id) return [];
      return await KnowledgeAPI.getDocumentVersions(id);
    },
    enabled: !!id && !!activeOrg,
  });

  const restoreVersion = useMutation({
    mutationFn: async (version: number) => {
      if (!id) return;
      return await KnowledgeAPI.restoreDocumentVersion(id, version);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-document', id] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-document-versions', id] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });

  return {
    document: query.data || null,
    isLoading: query.isLoading,
    versions: versionsQuery.data || [],
    isLoadingVersions: versionsQuery.isLoading,
    restoreVersion,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Collections
// ─────────────────────────────────────────────────────────────────────────────
export function useCollections() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<Collection[]>({
    queryKey: ['knowledge-collections', activeOrg?.id],
    queryFn: async () => {
      const [cols, docs] = await Promise.all([
        KnowledgeAPI.listCollections(),
        KnowledgeAPI.listDocuments(),
      ]);
      return cols.map((col) => ({
        ...col,
        document_ids: docs
          .filter((d) => d.collection_id === col.id)
          .map((d) => d.id),
      }));
    },
    enabled: !!activeOrg,
  });

  const createCollectionMutation = useMutation({
    mutationFn: async ({ name, description, parentId, visibility }: { name: string; description?: string; parentId?: string; visibility?: string }) => {
      return await KnowledgeAPI.createCollection(name, description, parentId, visibility);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-collections'] });
    },
  });

  const deleteCollectionMutation = useMutation({
    mutationFn: async (id: string) => {
      await KnowledgeAPI.deleteCollection(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-collections'] });
    },
  });

  const addDocMutation = useMutation({
    mutationFn: async ({ collectionId, docId }: { collectionId: string; docId: string }) => {
      return await KnowledgeAPI.updateDocument(docId, { collection_id: collectionId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-collections'] });
    },
  });

  const removeDocMutation = useMutation({
    mutationFn: async ({ docId }: { docId: string }) => {
      return await KnowledgeAPI.updateDocument(docId, { collection_id: null });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-collections'] });
    },
  });

  return {
    collections: query.data || [],
    isLoading: query.isLoading,
    createCollection: async (name: string, description?: string) => {
      await createCollectionMutation.mutateAsync({ name, description });
    },
    deleteCollection: async (id: string) => {
      await deleteCollectionMutation.mutateAsync(id);
    },
    addDoc: async (collectionId: string, docId: string) => {
      await addDocMutation.mutateAsync({ collectionId, docId });
    },
    removeDoc: async (collectionId: string, docId: string) => {
      await removeDocMutation.mutateAsync({ docId });
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Folders
// ─────────────────────────────────────────────────────────────────────────────
export function useFolders() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<Folder[]>({
    queryKey: ['knowledge-folders', activeOrg?.id],
    queryFn: async () => {
      return await KnowledgeAPI.listFolders();
    },
    enabled: !!activeOrg,
  });

  const createFolderMutation = useMutation({
    mutationFn: async ({ name, collectionId, parentId }: { name: string; collectionId: string; parentId?: string }) => {
      return await KnowledgeAPI.createFolder(name, collectionId, parentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-folders'] });
    },
  });

  return {
    folders: query.data || [],
    isLoading: query.isLoading,
    createFolder: async (name: string, collectionId: string, parentId?: string) => {
      await createFolderMutation.mutateAsync({ name, collectionId, parentId });
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Upload Center & Queue
// ─────────────────────────────────────────────────────────────────────────────
export function useUpload() {
  const queryClient = useQueryClient();
  const store = useKnowledgeStore();

  const uploadFileMutation = useMutation({
    mutationFn: async ({ file, uploadId, options }: { file: File; uploadId: string; options?: any }) => {
      return await KnowledgeAPI.uploadAndIndex(
        file,
        (progress) => {
          store.updateUploadProgress(uploadId, progress, 'uploading');
        },
        options
      );
    },
    onSuccess: (doc, variables) => {
      store.updateUploadProgress(variables.uploadId, 100, 'completed');
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-queue'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-dashboard-stats'] });
    },
    onError: (err, variables) => {
      store.updateUploadProgress(variables.uploadId, 0, 'failed');
    },
  });

  const uploadBatch = async (files: File[], options?: any) => {
    const queueItems = files.map((f) => {
      const uploadId = `up-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      return { id: uploadId, name: f.name, size: f.size, file: f };
    });

    store.addToUploadQueue(queueItems.map((q) => ({ id: q.id, name: q.name, size: q.size })));

    for (const item of queueItems) {
      try {
        await uploadFileMutation.mutateAsync({ file: item.file, uploadId: item.id, options });
      } catch (e) {
        console.error('Failed upload of:', item.name);
      }
    }
  };

  return {
    uploadQueue: store.uploadQueue,
    clearQueue: store.clearUploadQueue,
    uploadBatch,
    isPending: uploadFileMutation.isPending,
  };
}

export function useQueueJobs() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  const query = useQuery<QueueJob[]>({
    queryKey: ['knowledge-queue', activeOrg?.id],
    queryFn: async () => {
      return await KnowledgeAPI.listQueueJobs();
    },
    enabled: !!activeOrg,
    refetchInterval: 3000, // Poll every 3s during active builds
  });

  const cancelJob = useMutation({
    mutationFn: async (id: string) => {
      await KnowledgeAPI.cancelQueueJob(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-queue'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });

  const retryJob = useMutation({
    mutationFn: async (id: string) => {
      await KnowledgeAPI.retryQueueJob(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-queue'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
  });

  return {
    jobs: query.data || [],
    isLoading: query.isLoading,
    cancelJob,
    retryJob,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Vector similarity search & RAG
// ─────────────────────────────────────────────────────────────────────────────
export function useKnowledgeSearch() {
  const queryClient = useQueryClient();

  const searchMutation = useMutation({
    mutationFn: async ({ queryText, limit, searchType, filters }: { queryText: string; limit?: number; searchType?: string; filters?: any }) => {
      return await KnowledgeAPI.querySimilarChunks(queryText, limit, searchType, filters);
    },
  });

  return {
    searchResults: searchMutation.data || [],
    isSearching: searchMutation.isPending,
    search: searchMutation.mutateAsync,
  };
}

export function useRAG() {
  const queryClient = useQueryClient();

  const ragMutation = useMutation({
    mutationFn: async ({ queryText, conversationId, limit, searchType, filters }: { queryText: string; conversationId?: string; limit?: number; searchType?: string; filters?: any }) => {
      return await KnowledgeAPI.queryRAG(queryText, conversationId, limit, searchType, filters);
    },
  });

  return {
    answer: ragMutation.data?.answer || '',
    citations: ragMutation.data?.citations || [],
    confidenceScore: ragMutation.data?.confidence_score || 0.0,
    similarityScore: ragMutation.data?.similarity_score || 0.0,
    contextTokens: ragMutation.data?.context_tokens || 0,
    promptTokens: ragMutation.data?.prompt_tokens || 0,
    completion_tokens: ragMutation.data?.completion_tokens || 0,
    hallucinationRisk: ragMutation.data?.hallucination_risk || 'LOW',
    latency: ragMutation.data?.latency,
    isQuerying: ragMutation.isPending,
    query: ragMutation.mutateAsync,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Dashboard Stats & Analytics
// ─────────────────────────────────────────────────────────────────────────────
export function useDashboardStats() {
  const { activeOrg } = useAuthStore();

  const query = useQuery<DashboardStats>({
    queryKey: ['knowledge-dashboard-stats', activeOrg?.id],
    queryFn: async () => {
      return await KnowledgeAPI.getDashboardStats();
    },
    enabled: !!activeOrg,
  });

  return {
    dashboardData: query.data || null,
    isLoading: query.isLoading,
    refetch: query.refetch,
  };
}

export function useEmbeddings() {
  const { documents } = useDocuments();

  const models: any[] = [
    { name: 'text-embedding-3-small', provider: 'OpenAI', dimensions: 1536, status: 'active' },
    { name: 'text-embedding-3-large', provider: 'OpenAI', dimensions: 3072, status: 'active' },
    { name: 'nomic-embed-text', provider: 'Nomic', dimensions: 768, status: 'active' },
  ];

  const stats = React.useMemo(() => {
    const totalDocs = documents.length;
    const indexedDocs = documents.filter((d) => d.status === 'completed').length;
    const embeddingDocs = documents.filter((d) => d.status === 'processing').length;
    const progressPercent = totalDocs ? Math.round((indexedDocs / totalDocs) * 100) : 100;
    const chunkCount = documents.reduce((sum, d) => sum + (d.chunk_count || 1), 0);

    return {
      totalDocs,
      indexedDocs,
      embeddingDocs,
      progressPercent,
      chunkCount,
      vectorCount: chunkCount,
      models,
    };
  }, [documents]);

  return {
    stats,
    models,
  };
}

export function useAnalytics() {
  const { documents } = useDocuments();
  const { collections } = useCollections();

  const stats = React.useMemo(() => {
    const totalDocs = documents.length;
    const totalStorage = documents.reduce((sum, d) => sum + (d.file_size || 0), 0);
    const chunkCount = documents.reduce((sum, d) => sum + (d.chunk_count || 1), 0);

    const dailyUploads: Record<string, number> = {};
    for (const doc of documents) {
      const dateStr = new Date(doc.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      dailyUploads[dateStr] = (dailyUploads[dateStr] || 0) + 1;
    }

    const uploadHistory = Object.entries(dailyUploads).map(([date, count]) => ({
      date,
      count,
    })).slice(-10);

    return {
      totalDocs,
      totalStorageBytes: totalStorage,
      totalStorageKb: parseFloat((totalStorage / 1024).toFixed(2)),
      chunkCount,
      collectionsCount: collections.length,
      uploadHistory,
    };
  }, [documents, collections]);

  return {
    stats,
  };
}

