import * as React from 'react';
import { useCollections } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { FolderOpen, Plus, Search, Trash2, ArrowRight, FolderClosed } from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { Dialog } from '@/components/ui/dialog';

export function CollectionsPage() {
  const { collections, createCollection, deleteCollection } = useCollections();
  
  const [searchQuery, setSearchQuery] = React.useState('');
  const [showCreateModal, setShowCreateModal] = React.useState(false);
  const [newColName, setNewColName] = React.useState('');
  const [newColDesc, setNewColDesc] = React.useState('');

  const filteredCols = React.useMemo(() => {
    return collections.filter((col) =>
      col.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [collections, searchQuery]);

  const handleCreate = () => {
    if (!newColName.trim()) {
      toast.error('Invalid Name', 'Collection name cannot be empty.');
      return;
    }
    createCollection(newColName, newColDesc);
    setNewColName('');
    setNewColDesc('');
    setShowCreateModal(false);
    toast.success('Collection Created', 'Successfully established folder namespace.');
  };

  const handleDelete = (id: string) => {
    deleteCollection(id);
    toast.success('Collection Deleted', 'Removed folder structure without deleting files.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Knowledge Collections"
        description="Organize your indexed data files into structured category directories."
        icon={<FolderOpen className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Folder mapping</Badge>}
        actions={
          <Button variant="violet" size="sm" onClick={() => setShowCreateModal(true)} className="h-8 text-[11px]">
            <Plus className="w-3.5 h-3.5 mr-1" />
            Create Collection
          </Button>
        }
      />

      {/* Search and stats */}
      <div className="flex items-center gap-4 justify-between bg-neutral-950/20 border border-white/5 p-4 rounded-xl">
        <div className="relative min-w-[260px]">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-neutral-500" />
          <Input
            placeholder="Search collections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-neutral-950/40 border-white/5 h-8 text-[11px]"
          />
        </div>
        <span className="text-[10px] text-neutral-500 font-mono">
          Total folders: <b>{collections.length}</b>
        </span>
      </div>

      {/* Folder card grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCols.map((col) => (
          <Card 
            key={col.id} 
            className="flex flex-col gap-4 border border-white/5 hover:border-violet-500/20 transition-all p-5 bg-neutral-950/10 group relative"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-neutral-900 border border-white/5 text-violet-400">
                  <FolderOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white group-hover:text-violet-400 transition-colors">
                    {col.name}
                  </h3>
                  <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                    Created {new Date(col.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <button
                onClick={() => handleDelete(col.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 text-neutral-500 hover:text-rose-400 cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <p className="text-[11px] text-neutral-400 line-clamp-2 min-h-[32px] leading-relaxed">
              {col.description || 'No description provided for this collection.'}
            </p>

            <div className="flex items-center justify-between border-t border-white/5 pt-3.5 mt-2">
              <Badge variant="neutral" size="sm">
                {col.document_ids?.length || 0} documents
              </Badge>
              
              <a 
                href={`/dashboard/knowledge/collections/${col.id}`}
                className="text-[11px] text-violet-400 font-bold flex items-center gap-1 hover:underline"
              >
                Open folder
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </a>
            </div>
          </Card>
        ))}

        {filteredCols.length === 0 && (
          <div className="col-span-full py-20 flex flex-col items-center justify-center text-center gap-3">
            <FolderClosed className="w-10 h-10 text-neutral-600" />
            <h4 className="font-bold text-white text-sm">No Collections Found</h4>
            <p className="text-xs text-neutral-500">Create a folder collection to structure your document indexes.</p>
          </div>
        )}
      </div>

      {/* Creation Modal */}
      <Dialog
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Collection"
        className="max-w-md"
      >
        <div className="flex flex-col gap-4 mt-1.5">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-neutral-400 font-bold uppercase">Folder Name</label>
            <Input
              placeholder="e.g. Sales Briefs"
              value={newColName}
              onChange={(e) => setNewColName(e.target.value)}
              className="bg-neutral-950 border-white/5 text-xs h-9"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-neutral-400 font-bold uppercase">Description</label>
            <Input
              placeholder="Brief description of directory documents..."
              value={newColDesc}
              onChange={(e) => setNewColDesc(e.target.value)}
              className="bg-neutral-950 border-white/5 text-xs h-9"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-white/5 pt-3.5 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCreateModal(false)}
              className="text-xs border-white/5"
            >
              Cancel
            </Button>
            <Button
              variant="violet"
              size="sm"
              onClick={handleCreate}
              className="text-xs"
            >
              Create
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
export { FolderClosed };
