import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Collection, KnowledgeSettings } from '../types';

interface UploadItem {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
}

interface KnowledgeState {
  selectedDocumentId: string | null;
  selectedCollectionId: string | null;
  searchQuery: string;
  searchFilters: {
    fileType: string;
    status: string;
    tag: string;
  };
  uploadQueue: UploadItem[];
  settings: KnowledgeSettings;
  favorites: string[];
  archived: string[];
  trash: string[];
  localCollections: Collection[];

  setSelectedDocumentId: (id: string | null) => void;
  setSelectedCollectionId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setSearchFilters: (filters: Partial<KnowledgeState['searchFilters']>) => void;
  addToUploadQueue: (items: Omit<UploadItem, 'progress' | 'status'>[]) => void;
  updateUploadProgress: (id: string, progress: number, status?: UploadItem['status']) => void;
  clearUploadQueue: () => void;
  updateSettings: (settings: Partial<KnowledgeSettings>) => void;
  toggleFavorite: (docId: string) => void;
  toggleArchive: (docId: string) => void;
  moveToTrash: (docId: string) => void;
  restoreFromTrash: (docId: string) => void;
  createCollection: (name: string, description?: string) => void;
  deleteCollection: (id: string) => void;
  addDocToCollection: (colId: string, docId: string) => void;
  removeDocFromCollection: (colId: string, docId: string) => void;
}

export const useKnowledgeStore = create<KnowledgeState>()(
  persist(
    (set) => ({
      selectedDocumentId: null,
      selectedCollectionId: null,
      searchQuery: '',
      searchFilters: {
        fileType: 'all',
        status: 'all',
        tag: '',
      },
      uploadQueue: [],
      settings: {
        chunk_size: 500,
        chunk_overlap: 100,
        embedding_model: 'text-embedding-3-small',
        auto_index: true,
        auto_embed: true,
        duplicate_detection: true,
      },
      favorites: [],
      archived: [],
      trash: [],
      localCollections: [
        { id: 'col-1', name: 'Product Specifications', description: 'Technical design sheets and docs', document_ids: [], organization_id: '', created_at: new Date().toISOString() },
        { id: 'col-2', name: 'Marketing Strategy', description: 'Social outreach campaigns and briefings', document_ids: [], organization_id: '', created_at: new Date().toISOString() },
      ],

      setSelectedDocumentId: (id) => set({ selectedDocumentId: id }),
      setSelectedCollectionId: (id) => set({ selectedCollectionId: id }),
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchFilters: (filters) =>
        set((state) => ({ searchFilters: { ...state.searchFilters, ...filters } })),

      addToUploadQueue: (items) =>
        set((state) => ({
          uploadQueue: [
            ...state.uploadQueue,
            ...items.map((item) => ({ ...item, progress: 0, status: 'pending' as const })),
          ],
        })),

      updateUploadProgress: (id, progress, status) =>
        set((state) => ({
          uploadQueue: state.uploadQueue.map((item) =>
            item.id === id
              ? { ...item, progress, ...(status ? { status } : {}) }
              : item
          ),
        })),

      clearUploadQueue: () => set({ uploadQueue: [] }),

      updateSettings: (settings) =>
        set((state) => ({ settings: { ...state.settings, ...settings } })),

      toggleFavorite: (docId) =>
        set((state) => {
          const isFav = state.favorites.includes(docId);
          return {
            favorites: isFav
              ? state.favorites.filter((id) => id !== docId)
              : [...state.favorites, docId],
          };
        }),

      toggleArchive: (docId) =>
        set((state) => {
          const isArchived = state.archived.includes(docId);
          return {
            archived: isArchived
              ? state.archived.filter((id) => id !== docId)
              : [...state.archived, docId],
          };
        }),

      moveToTrash: (docId) =>
        set((state) => ({
          trash: [...state.trash, docId],
          favorites: state.favorites.filter((id) => id !== docId),
          archived: state.archived.filter((id) => id !== docId),
        })),

      restoreFromTrash: (docId) =>
        set((state) => ({
          trash: state.trash.filter((id) => id !== docId),
        })),

      createCollection: (name, description) =>
        set((state) => {
          const newCol: Collection = {
            id: `col-${Date.now()}`,
            name,
            description,
            document_ids: [],
            organization_id: '',
            created_at: new Date().toISOString(),
          };
          return { localCollections: [...state.localCollections, newCol] };
        }),

      deleteCollection: (id) =>
        set((state) => ({
          localCollections: state.localCollections.filter((col) => col.id !== id),
        })),

      addDocToCollection: (colId, docId) =>
        set((state) => ({
          localCollections: state.localCollections.map((col) => {
            if (col.id !== colId) return col;
            if (col.document_ids.includes(docId)) return col;
            return { ...col, document_ids: [...col.document_ids, docId] };
          }),
        })),

      removeDocFromCollection: (colId, docId) =>
        set((state) => ({
          localCollections: state.localCollections.map((col) =>
            col.id === colId
              ? { ...col, document_ids: col.document_ids.filter((id) => id !== docId) }
              : col
          ),
        })),
    }),
    {
      name: 'viptant-knowledge-store',
      partialize: (state) => ({
        favorites: state.favorites,
        archived: state.archived,
        trash: state.trash,
        localCollections: state.localCollections,
        settings: state.settings,
      }),
    }
  )
);
