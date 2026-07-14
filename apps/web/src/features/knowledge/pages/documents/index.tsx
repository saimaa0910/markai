import * as React from 'react';
import { useDocuments, useCollections } from '../../hooks';
import { useKnowledgeStore } from '../../store/knowledge';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  FileText, Search, Star, Archive, Trash, MoreVertical, 
  Download, Eye, Grid, List, ArrowUpDown, Trash2, FolderClosed, Plus 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

export function DocumentsPage() {
  const { documents, isLoading, deleteDoc } = useDocuments();
  const { collections, addDoc } = useCollections();
  const store = useKnowledgeStore();

  const [category, setCategory] = React.useState<'all' | 'favorites' | 'archived' | 'trash'>('all');
  const [viewMode, setViewMode] = React.useState<'grid' | 'table'>('grid');
  const [sortKey, setSortKey] = React.useState<string>('newest');
  const [selectedDocs, setSelectedDocs] = React.useState<string[]>([]);
  const [showAddToCollection, setShowAddToCollection] = React.useState<string | null>(null);

  // Filter list
  const filteredDocs = React.useMemo(() => {
    return documents.filter((doc) => {
      // Category filter
      if (category === 'favorites' && !doc.is_favorite) return false;
      if (category === 'archived' && !doc.is_archived) return false;
      if (category === 'trash' && !doc.is_trash) return false;
      if (category !== 'trash' && doc.is_trash) return false;
      if (category !== 'archived' && doc.is_archived && category !== 'favorites') return false;

      // Text query filter
      if (store.searchQuery) {
        return doc.title.toLowerCase().includes(store.searchQuery.toLowerCase());
      }
      return true;
    });
  }, [documents, category, store.searchQuery]);

  // Sort list
  const sortedDocs = React.useMemo(() => {
    const list = [...filteredDocs];
    if (sortKey === 'newest') {
      return list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    if (sortKey === 'oldest') {
      return list.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    }
    if (sortKey === 'size-desc') {
      return list.sort((a, b) => (b.file_size || 0) - (a.file_size || 0));
    }
    if (sortKey === 'name-asc') {
      return list.sort((a, b) => a.title.localeCompare(b.title));
    }
    return list;
  }, [filteredDocs, sortKey]);

  const handleToggleSelect = (id: string) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleBulkAction = (action: 'favorite' | 'archive' | 'trash' | 'delete') => {
    if (selectedDocs.length === 0) return;
    
    selectedDocs.forEach((id) => {
      if (action === 'favorite') store.toggleFavorite(id);
      if (action === 'archive') store.toggleArchive(id);
      if (action === 'trash') store.moveToTrash(id);
      if (action === 'delete') deleteDoc.mutate(id);
    });

    toast.success('Bulk Actions Complete', `Successfully processed ${selectedDocs.length} documents.`);
    setSelectedDocs([]);
  };

  const handleDocumentDelete = (id: string) => {
    deleteDoc.mutate(id, {
      onSuccess: () => {
        toast.success('Document Deleted', 'File removed from the active library.');
      },
    });
  };

  const handleAssignToCollection = (colId: string, docId: string) => {
    addDoc(colId, docId);
    setShowAddToCollection(null);
    toast.success('Document Mapped', 'Successfully allocated file to the target collection.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Document Library"
        description="Index and manage PDF, DOCX, TXT, and CSV resources. Run queries on metadata attributes."
        icon={<FileText className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">File indexer</Badge>}
        actions={
          <a href="/dashboard/knowledge/upload">
            <Button variant="violet" size="sm" className="h-8 text-[11px]">
              <Plus className="w-3.5 h-3.5 mr-1" />
              Upload Files
            </Button>
          </a>
        }
      />

      {/* Control panel & categories switches */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-neutral-950/20 border border-white/5 p-4 rounded-xl">
        <div className="flex items-center flex-wrap gap-2">
          {[
            { id: 'all', label: 'All Documents', icon: <FileText className="w-3.5 h-3.5" /> },
            { id: 'favorites', label: 'Starred', icon: <Star className="w-3.5 h-3.5 text-amber-400" /> },
            { id: 'archived', label: 'Archived', icon: <Archive className="w-3.5 h-3.5" /> },
            { id: 'trash', label: 'Trash', icon: <Trash className="w-3.5 h-3.5" /> },
          ].map((cat) => (
            <Button
              key={cat.id}
              variant="outline"
              size="sm"
              onClick={() => { setCategory(cat.id as any); setSelectedDocs([]); }}
              className={`h-8 text-[11px] border-white/5 gap-1.5 ${
                category === cat.id ? 'bg-violet-600 border-violet-500/20 text-white' : 'bg-neutral-900/50'
              }`}
            >
              {cat.icon}
              {cat.label}
            </Button>
          ))}
        </div>

        {/* Search, Sort and View switches */}
        <div className="flex items-center flex-wrap gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:flex-none min-w-[200px]">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-neutral-500" />
            <Input
              placeholder="Search library..."
              value={store.searchQuery}
              onChange={(e) => store.setSearchQuery(e.target.value)}
              className="pl-9 bg-neutral-950/40 border-white/5 h-8 text-[11px]"
            />
          </div>

          <Select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            className="bg-neutral-900 border-white/5 h-8 text-[11px] w-36"
            options={[
              { label: 'Newest indexed', value: 'newest' },
              { label: 'Oldest indexed', value: 'oldest' },
              { label: 'File size (Desc)', value: 'size-desc' },
              { label: 'Alphabetical A-Z', value: 'name-asc' },
            ]}
          />

          <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-0.5 text-neutral-400">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1 rounded transition-all cursor-pointer ${viewMode === 'grid' ? 'bg-violet-600 text-white' : ''}`}
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1 rounded transition-all cursor-pointer ${viewMode === 'table' ? 'bg-violet-600 text-white' : ''}`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Bulk action actionbar */}
      {selectedDocs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 bg-violet-600/10 border border-violet-500/20 rounded-xl flex items-center justify-between gap-4"
        >
          <span className="text-[11px] text-neutral-300 font-semibold">
            {selectedDocs.length} files selected:
          </span>
          <div className="flex items-center gap-2">
            {category !== 'favorites' && (
              <Button size="sm" onClick={() => handleBulkAction('favorite')} className="h-7 text-[10px] bg-neutral-900 text-amber-400 border border-amber-500/10">
                Star
              </Button>
            )}
            {category !== 'archived' && (
              <Button size="sm" onClick={() => handleBulkAction('archive')} className="h-7 text-[10px] bg-neutral-900 border border-white/5">
                Archive
              </Button>
            )}
            {category !== 'trash' && (
              <Button size="sm" onClick={() => handleBulkAction('trash')} className="h-7 text-[10px] bg-rose-950/20 border border-rose-500/20 text-rose-400">
                Trash
              </Button>
            )}
            {category === 'trash' && (
              <Button size="sm" onClick={() => handleBulkAction('delete')} className="h-7 text-[10px] bg-rose-600 text-white hover:bg-rose-700">
                Delete Permanently
              </Button>
            )}
          </div>
        </motion.div>
      )}

      {/* Main Files Display */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-28 bg-neutral-900/60 rounded-xl border border-white/5" />
          ))}
        </div>
      ) : sortedDocs.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <AnimatePresence mode="popLayout">
              {sortedDocs.map((doc) => {
                const isSel = selectedDocs.includes(doc.id);
                return (
                  <motion.div
                    key={doc.id}
                    layoutId={doc.id}
                    className={`relative p-4 rounded-xl border flex flex-col gap-3 bg-neutral-950/40 hover:border-violet-500/20 transition-all group ${
                      isSel ? 'border-violet-500' : 'border-white/5'
                    }`}
                  >
                    {/* Checkbox selector */}
                    <button 
                      onClick={() => handleToggleSelect(doc.id)}
                      className={`absolute top-4 left-4 w-4 h-4 rounded border flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100 cursor-pointer ${
                        isSel ? 'bg-violet-600 border-violet-500 opacity-100' : 'border-white/20 bg-neutral-900'
                      }`}
                    >
                      {isSel && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </button>

                    <div className="flex items-start gap-3 pl-6 pr-6">
                      <div className="p-2 rounded-lg bg-neutral-900 border border-white/5 text-violet-400 shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <a 
                          href={`/dashboard/knowledge/documents/${doc.id}`}
                          className="text-xs font-bold text-white hover:text-violet-400 hover:underline truncate block"
                          title={doc.title}
                        >
                          {doc.title}
                        </a>
                        <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                          {((doc.file_size || 0) / 1024).toFixed(1)} KB · {doc.file_type}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between border-t border-white/5 pt-3 mt-1">
                      <div className="flex items-center gap-1.5">
                        <Badge variant="emerald" size="sm" dot>Indexed</Badge>
                        <Badge variant="neutral" size="sm">{doc.chunk_count} chunks</Badge>
                      </div>

                      {/* Dropdown controls */}
                      <div className="flex items-center gap-1.5">
                        <button 
                          onClick={() => store.toggleFavorite(doc.id)}
                          className={`p-1 rounded text-neutral-500 hover:text-amber-400 cursor-pointer`}
                        >
                          <Star className={`w-3.5 h-3.5 ${doc.is_favorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                        </button>
                        
                        {doc.is_trash ? (
                          <button 
                            onClick={() => handleDocumentDelete(doc.id)}
                            className="p-1 rounded text-neutral-500 hover:text-rose-400 cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <button 
                            onClick={() => store.moveToTrash(doc.id)}
                            className="p-1 rounded text-neutral-500 hover:text-rose-400 cursor-pointer"
                          >
                            <Trash className="w-3.5 h-3.5" />
                          </button>
                        )}

                        <button 
                          onClick={() => setShowAddToCollection(showAddToCollection === doc.id ? null : doc.id)}
                          className="p-1 rounded text-neutral-500 hover:text-white cursor-pointer"
                        >
                          <FolderClosed className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Quick Add To Collection dialog */}
                    {showAddToCollection === doc.id && (
                      <div className="absolute inset-0 bg-neutral-950 border border-white/10 rounded-xl p-3 flex flex-col gap-2 z-10 text-xs">
                        <span className="font-bold text-white">Select Destination Folder</span>
                        <div className="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-1">
                          {collections.map((col) => (
                            <button
                              key={col.id}
                              onClick={() => handleAssignToCollection(col.id, doc.id)}
                              className="px-2.5 py-1.5 rounded bg-neutral-900 border border-white/5 hover:border-violet-500/30 text-left hover:text-white transition-all truncate block"
                            >
                              {col.name}
                            </button>
                          ))}
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => setShowAddToCollection(null)}
                          className="h-6 text-[9px] border-white/5"
                        >
                          Cancel
                        </Button>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        ) : (
          <div className="border border-white/5 bg-neutral-950/20 rounded-xl overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/5 text-neutral-500 uppercase tracking-wider font-semibold font-mono text-[9px]">
                  <th className="p-3">File Asset Name</th>
                  <th className="p-3">Format</th>
                  <th className="p-3">Chunks</th>
                  <th className="p-3">Size</th>
                  <th className="p-3">Created At</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-neutral-300">
                {sortedDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-neutral-900/10">
                    <td className="p-3">
                      <a href={`/dashboard/knowledge/documents/${doc.id}`} className="font-semibold text-white hover:text-violet-400 hover:underline">
                        {doc.title}
                      </a>
                    </td>
                    <td className="p-3 font-mono uppercase text-[10px]">{doc.file_type}</td>
                    <td className="p-3 font-mono">{doc.chunk_count} chunks</td>
                    <td className="p-3 font-mono">{((doc.file_size || 0) / 1024).toFixed(1)} KB</td>
                    <td className="p-3 font-mono text-neutral-500">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="p-3 text-right flex items-center justify-end gap-2">
                      <button onClick={() => store.toggleFavorite(doc.id)} className="p-1 hover:text-amber-400">
                        <Star className={`w-3.5 h-3.5 ${doc.is_favorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                      </button>
                      <button onClick={() => store.moveToTrash(doc.id)} className="p-1 hover:text-rose-400">
                        <Trash className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <Card className="py-20 flex flex-col items-center justify-center text-center gap-3">
          <FileText className="w-10 h-10 text-neutral-600" />
          <h4 className="font-bold text-white text-sm">No Documents Found</h4>
          <p className="text-xs text-neutral-500 max-w-xs">No records matched the active filter category or search inputs.</p>
        </Card>
      )}
    </div>
  );
}
export { Grid, List, ArrowUpDown };
