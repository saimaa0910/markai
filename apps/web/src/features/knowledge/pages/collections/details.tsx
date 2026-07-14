import * as React from 'react';
import { useCollections, useDocuments } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  FolderOpen, ArrowLeft, Trash2, FileText, 
  Plus, ExternalLink, Calendar, Info 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

interface CollectionDetailsPageProps {
  id: string;
}

export function CollectionDetailsPage({ id }: CollectionDetailsPageProps) {
  const { collections, addDoc, removeDoc } = useCollections();
  const { documents, isLoading: loadingDocs } = useDocuments();

  const collection = React.useMemo(() => {
    return collections.find((col) => col.id === id) || null;
  }, [collections, id]);

  const [showDocSelector, setShowDocSelector] = React.useState(false);

  if (!collection) {
    return (
      <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
        <FolderOpen className="w-10 h-10 text-neutral-600" />
        <h4 className="font-bold text-white text-sm">Collection Not Found</h4>
        <a href="/dashboard/knowledge/collections">
          <Button variant="outline" size="sm" className="border-white/5">
            Back to Collections
          </Button>
        </a>
      </div>
    );
  }

  // Get documents belonging to this collection
  const allocatedDocs = React.useMemo(() => {
    return documents.filter((doc) => collection.document_ids.includes(doc.id));
  }, [documents, collection.document_ids]);

  // Get documents not in this collection
  const unallocatedDocs = React.useMemo(() => {
    return documents.filter((doc) => !collection.document_ids.includes(doc.id) && !doc.is_trash);
  }, [documents, collection.document_ids]);

  const handleAddDocument = (docId: string) => {
    addDoc(collection.id, docId);
    setShowDocSelector(false);
    toast.success('Document Added', 'Successfully linked document to collection folder.');
  };

  const handleRemoveDocument = (docId: string) => {
    removeDoc(collection.id, docId);
    toast.success('Document Removed', 'Deallocated document link from collection.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/knowledge/collections" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Collections
        </a>
      </div>

      <PageHeader
        title={collection.name}
        description={collection.description || 'Collection folder space.'}
        icon={<FolderOpen className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Collection details</Badge>}
        actions={
          <div className="relative">
            <Button
              variant="violet"
              size="sm"
              onClick={() => setShowDocSelector(!showDocSelector)}
              className="h-8 text-[11px]"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Documents
            </Button>

            {showDocSelector && (
              <div className="absolute right-0 mt-2 w-64 bg-neutral-950 border border-white/10 rounded-xl p-3 flex flex-col gap-2 z-20 shadow-xl text-xs">
                <span className="font-bold text-white">Select File to Link</span>
                <div className="max-h-48 overflow-y-auto flex flex-col gap-1.5 pr-1">
                  {unallocatedDocs.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => handleAddDocument(doc.id)}
                      className="px-2.5 py-1.5 rounded bg-neutral-900 border border-white/5 hover:border-violet-500/30 text-left hover:text-white transition-all truncate block"
                    >
                      {doc.title}
                    </button>
                  ))}
                  {unallocatedDocs.length === 0 && (
                    <span className="text-[10px] text-neutral-500 text-center py-4">
                      All active files linked.
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Side Info Card */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          <Card className="p-4 flex flex-col gap-4 bg-neutral-950/20">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-violet-400" /> Folder Information
            </span>

            <div className="flex flex-col gap-3.5 text-xs">
              <div className="flex flex-col gap-1 border-b border-white/5 pb-2.5">
                <span className="text-neutral-500">Linked Documents</span>
                <span className="text-white font-bold">{allocatedDocs.length} files</span>
              </div>
              <div className="flex flex-col gap-1 border-b border-white/5 pb-2.5">
                <span className="text-neutral-500 font-sans">Created Date</span>
                <span className="text-white font-mono flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-neutral-400" />
                  {new Date(collection.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Side Linked Files List */}
        <div className="lg:col-span-3">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Linked Documents</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Resources allocated to this directory space.</p>
            </div>

            <div className="flex flex-col gap-3 mt-2">
              <AnimatePresence mode="popLayout">
                {allocatedDocs.map((doc) => (
                  <motion.div
                    key={doc.id}
                    layoutId={doc.id}
                    className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between gap-4 group"
                  >
                    <div className="flex items-center gap-3 truncate">
                      <FileText className="w-4 h-4 text-violet-400 shrink-0" />
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-bold text-white truncate">{doc.title}</span>
                        <span className="text-[10px] text-neutral-500 font-mono mt-0.5">
                          {((doc.file_size || 0) / 1024).toFixed(1)} KB · {doc.file_type}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0">
                      <a href={`/dashboard/knowledge/documents/${doc.id}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-[9px] border-white/5 bg-neutral-900 hover:bg-neutral-800"
                        >
                          <ExternalLink className="w-3 h-3 mr-1" />
                          View file
                        </Button>
                      </a>
                      <button
                        onClick={() => handleRemoveDocument(doc.id)}
                        className="p-1.5 text-neutral-500 hover:text-rose-400 cursor-pointer"
                        title="Unlink file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {allocatedDocs.length === 0 && (
                <div className="py-16 flex flex-col items-center justify-center text-center text-neutral-600">
                  <FileText className="w-6 h-6 mb-1 text-neutral-700" />
                  <span className="text-xs font-semibold">No files linked</span>
                  <p className="text-[10px] text-neutral-500 mt-0.5">Click "Add Documents" to link files inside this directory.</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { ExternalLink };
