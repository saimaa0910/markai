import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { KnowledgeAPI } from '../services/knowledge';
import { useKnowledgeStore } from '../store/knowledge';
import { KnowledgeDocument, Collection, DocumentChunk } from '../types';

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
        is_favorite: favorites.includes(doc.id),
        is_archived: archived.includes(doc.id),
        is_trash: trash.includes(doc.id),
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
    },
  });

  return {
    documents: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    deleteDoc,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Single Document details
// ─────────────────────────────────────────────────────────────────────────────
export function useDocument(id: string | null) {
  const { documents } = useDocuments();

  const document = React.useMemo(() => {
    if (!id) return null;
    return documents.find((doc) => doc.id === id) || null;
  }, [documents, id]);

  return {
    document,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Collections
// ─────────────────────────────────────────────────────────────────────────────
export function useCollections() {
  const { activeOrg } = useAuthStore();
  const store = useKnowledgeStore();

  const collections = React.useMemo(() => {
    return store.localCollections.map((col) => ({
      ...col,
      organization_id: activeOrg?.id || '',
    }));
  }, [store.localCollections, activeOrg]);

  return {
    collections,
    createCollection: store.createCollection,
    deleteCollection: store.deleteCollection,
    addDoc: store.addDocToCollection,
    removeDoc: store.removeDocFromCollection,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Upload Center
// ─────────────────────────────────────────────────────────────────────────────
export function useUpload() {
  const queryClient = useQueryClient();
  const store = useKnowledgeStore();

  const uploadFileMutation = useMutation({
    mutationFn: async ({ file, uploadId }: { file: File; uploadId: string }) => {
      return await KnowledgeAPI.uploadAndIndex(file, (progress) => {
        store.updateUploadProgress(uploadId, progress, 'uploading');
      });
    },
    onSuccess: (doc, variables) => {
      store.updateUploadProgress(variables.uploadId, 100, 'completed');
      queryClient.invalidateQueries({ queryKey: ['knowledge-documents'] });
    },
    onError: (err, variables) => {
      store.updateUploadProgress(variables.uploadId, 0, 'failed');
    },
  });

  const uploadBatch = async (files: File[]) => {
    const queueItems = files.map((f) => {
      const uploadId = `up-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      return { id: uploadId, name: f.name, size: f.size, file: f };
    });

    store.addToUploadQueue(queueItems.map((q) => ({ id: q.id, name: q.name, size: q.size })));

    for (const item of queueItems) {
      try {
        await uploadFileMutation.mutateAsync({ file: item.file, uploadId: item.id });
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

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Vector similarity search
// ─────────────────────────────────────────────────────────────────────────────
export function useKnowledgeSearch() {
  const queryClient = useQueryClient();

  const searchMutation = useMutation({
    mutationFn: async ({ queryText, limit }: { queryText: string; limit?: number }) => {
      return await KnowledgeAPI.querySimilarChunks(queryText, limit);
    },
  });

  return {
    searchResults: searchMutation.data || [],
    isSearching: searchMutation.isPending,
    search: searchMutation.mutateAsync,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Embeddings dashboard
// ─────────────────────────────────────────────────────────────────────────────
export function useEmbeddings() {
  const { documents } = useDocuments();

  const models: any[] = [
    { name: 'text-embedding-3-small', provider: 'OpenAI', dimensions: 1536, status: 'active' },
    { name: 'text-embedding-3-large', provider: 'OpenAI', dimensions: 3072, status: 'active' },
    { name: 'nomic-embed-text', provider: 'Nomic', dimensions: 768, status: 'active' },
  ];

  const stats = React.useMemo(() => {
    const totalDocs = documents.length;
    const indexedDocs = documents.filter((d) => d.status === 'indexed').length;
    const embeddingDocs = documents.filter((d) => d.status === 'embedding').length;
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

// ─────────────────────────────────────────────────────────────────────────────
// Hook: Analytics
// ─────────────────────────────────────────────────────────────────────────────
export function useAnalytics() {
  const { documents } = useDocuments();
  const { collections } = useCollections();

  const stats = React.useMemo(() => {
    const totalDocs = documents.length;
    const totalStorage = documents.reduce((sum, d) => sum + (d.file_size || 0), 0);
    const chunkCount = documents.reduce((sum, d) => sum + (d.chunk_count || 1), 0);

    // Group uploads by date
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
