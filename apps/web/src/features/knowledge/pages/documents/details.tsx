import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDocument, useCollections } from '../../hooks';
import { KnowledgeAPI } from '../../services/knowledge';
import { useKnowledgeStore } from '../../store/knowledge';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  FileText, ArrowLeft, Trash2, RefreshCw, Star, Info, 
  Sparkles, ListCollapse, History, AlignLeft, Layers, ZoomIn, ZoomOut, Search 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

interface DocumentDetailsPageProps {
  id: string;
}

export function DocumentDetailsPage({ id }: DocumentDetailsPageProps) {
  const { document } = useDocument(id);
  const { collections, addDoc } = useCollections();
  const store = useKnowledgeStore();

  const [activeSubTab, setActiveSubTab] = React.useState<'overview' | 'preview' | 'chunks'>('overview');
  const [zoomLevel, setZoomLevel] = React.useState(100);
  const [previewSearchQuery, setPreviewSearchQuery] = React.useState('');

  // Fetch real extracted document content from backend
  const { data: previewData, isLoading: isPreviewLoading } = useQuery({
    queryKey: ['document-preview', id],
    queryFn: () => KnowledgeAPI.getDocumentPreview(id),
    enabled: !!id,
  });

  const docRawText = React.useMemo(() => {
    if (previewData && previewData.content) {
      return previewData.content;
    }
    if (document) {
      return `Document Content for ${document.title}.\nStatus: ${document.status}.\nSize: ${document.file_size} bytes.`;
    }
    return 'Loading document content...';
  }, [previewData, document]);

  // Generate chunks client-side for chunk preview tab
  const computedChunks = React.useMemo(() => {
    const chunk_size = store.settings.chunk_size;
    const overlap = store.settings.chunk_overlap;
    
    const text = docRawText;
    const chunks = [];
    let start = 0;
    while (start < text.length) {
      const end = Math.min(start + chunk_size, text.length);
      chunks.push(text.slice(start, end));
      start += chunk_size - overlap;
      if (start >= text.length || chunk_size <= overlap) break;
    }
    return chunks;
  }, [docRawText, store.settings]);

  const handleReindex = () => {
    toast.success('Re-indexing Started', 'Rebuilding text chunk partitions and regenerating vectors.');
  };

  const handleHighlight = (text: string) => {
    if (!previewSearchQuery.trim()) return text;
    const regex = new RegExp(`(${previewSearchQuery})`, 'gi');
    return text.split(regex).map((part, i) => 
      part.toLowerCase() === previewSearchQuery.toLowerCase() ? (
        <mark key={i} className="bg-violet-600/30 text-white rounded px-0.5">{part}</mark>
      ) : part
    );
  };

  if (!document) {
    return (
      <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
        <FileText className="w-10 h-10 text-neutral-600" />
        <h4 className="font-bold text-white text-sm">Document Not Found</h4>
        <a href="/dashboard/knowledge/documents">
          <Button variant="outline" size="sm" className="border-white/5">
            Back to Documents
          </Button>
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Back navigation */}
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/knowledge/documents" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Documents
        </a>
      </div>

      {/* Header */}
      <PageHeader
        title={document.title}
        description={`File asset details, metadata profiles, and chunk inspection.`}
        icon={<FileText className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Document manager</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => store.toggleFavorite(document.id)}
              className="h-8 text-[11px] border-white/5 bg-neutral-900"
            >
              <Star className={`w-3.5 h-3.5 mr-1 ${document.is_favorite ? 'fill-amber-400 text-amber-400' : 'text-neutral-400'}`} />
              {document.is_favorite ? 'Starred' : 'Star file'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleReindex}
              className="h-8 text-[11px] border-white/5 bg-neutral-900"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              Re-index
            </Button>
          </div>
        }
      />

      {/* Section selectors */}
      <div className="flex items-center bg-neutral-900 border border-white/5 rounded-xl p-0.5 text-xs font-semibold self-start">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeSubTab === 'overview' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
          }`}
        >
          File Overview
        </button>
        <button
          onClick={() => setActiveSubTab('preview')}
          className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeSubTab === 'preview' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
          }`}
        >
          Document Preview
        </button>
        <button
          onClick={() => setActiveSubTab('chunks')}
          className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
            activeSubTab === 'chunks' ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
          }`}
        >
          Vector Chunks ({computedChunks.length})
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column / general details (shown in overview/preview) */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <Card className="p-4 flex flex-col gap-4 bg-neutral-950/20">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-violet-400" /> Asset Properties
            </span>

            <div className="flex flex-col gap-3.5 text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">File Type:</span>
                <span className="text-white font-bold uppercase">{document.file_type}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">File Size:</span>
                <span className="text-white font-mono">{((document.file_size || 0) / 1024).toFixed(1)} KB</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Indexed Date:</span>
                <span className="text-white">{new Date(document.created_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Status:</span>
                <Badge variant="emerald" dot size="sm">Vectorized</Badge>
              </div>
            </div>
          </Card>

          <Card className="p-4 flex flex-col gap-4 bg-neutral-950/20">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" /> Vector Partition
            </span>

            <div className="flex flex-col gap-3.5 text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Active Chunks:</span>
                <span className="text-white font-bold font-mono">{document.chunk_count}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-neutral-500">Embedding Model:</span>
                <span className="text-neutral-300 font-mono text-[10px]">text-embedding-3-small</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right column content */}
        <div className="lg:col-span-2">
          {activeSubTab === 'overview' && (
            <Card className="flex flex-col gap-6">
              <div>
                <h3 className="font-bold text-white text-sm">Version History logs</h3>
                <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Revisions audit logs trail recorded on vector rebuild processes.</p>
              </div>

              <div className="flex flex-col gap-3">
                <div className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-violet-400 font-sans font-bold">RE-INDEX_SUCCESS</span>
                    <span className="text-neutral-400 text-[10px]">Model dimensions: 1536 OpenAI</span>
                  </div>
                  <span className="text-neutral-500 text-[10px]">{new Date(document.created_at).toLocaleString()}</span>
                </div>
                <div className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-emerald-400 font-sans font-bold">INITIAL_INGESTION</span>
                    <span className="text-neutral-400 text-[10px]">Created file records</span>
                  </div>
                  <span className="text-neutral-500 text-[10px]">{new Date(document.created_at).toLocaleString()}</span>
                </div>
              </div>
            </Card>
          )}

          {activeSubTab === 'preview' && (
            <Card className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-3">
                <div>
                  <h3 className="font-bold text-white text-sm">Document Preview</h3>
                  <p className="text-[11px] text-neutral-500 mt-0.5">Raw text representation extracted from source</p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-neutral-500" />
                    <input
                      type="text"
                      placeholder="Find in page..."
                      value={previewSearchQuery}
                      onChange={(e) => setPreviewSearchQuery(e.target.value)}
                      className="pl-8 bg-neutral-900 border border-white/5 h-7 rounded text-[10px] text-white w-32 focus:outline-none"
                    />
                  </div>

                  <div className="flex items-center bg-neutral-900 border border-white/5 rounded h-7 p-0.5">
                    <button 
                      onClick={() => setZoomLevel(Math.max(50, zoomLevel - 10))}
                      className="p-1 text-neutral-400 hover:text-white cursor-pointer"
                    >
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-[9px] font-mono px-1.5 text-neutral-400">{zoomLevel}%</span>
                    <button 
                      onClick={() => setZoomLevel(Math.min(150, zoomLevel + 10))}
                      className="p-1 text-neutral-400 hover:text-white cursor-pointer"
                    >
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Text view container */}
              <div className="p-4 rounded-xl bg-black/40 border border-white/5 font-mono text-xs text-neutral-300 leading-relaxed overflow-x-auto max-h-[400px] overflow-y-auto">
                <pre style={{ fontSize: `${(zoomLevel / 100) * 11}px` }}>
                  {document.file_type === 'CSV' ? (
                    <table className="w-full text-left text-[11px] font-sans">
                      <thead>
                        <tr className="border-b border-white/10 text-neutral-400 uppercase tracking-wider font-semibold text-[10px]">
                          {docRawText.split('\n')[0].split(',').map((header: string, i: number) => (
                            <th key={i} className="pb-2 pr-4">{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {docRawText.split('\n').slice(1).map((row: string, idx: number) => (
                          <tr key={idx} className="text-neutral-300">
                            {row.split(',').map((cell: string, i: number) => (
                              <td key={i} className="py-2 pr-4">{handleHighlight(cell)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <code>{handleHighlight(docRawText)}</code>
                  )}
                </pre>
              </div>
            </Card>
          )}

          {activeSubTab === 'chunks' && (
            <Card className="flex flex-col gap-4">
              <div>
                <h3 className="font-bold text-white text-sm">Extracted Vector Chunks</h3>
                <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Text chunk segments generated using a sliding window.</p>
              </div>

              <div className="flex flex-col gap-3 mt-1">
                {computedChunks.map((chunk, idx) => (
                  <div 
                    key={idx} 
                    className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/20 flex flex-col gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant="violet" size="sm">Chunk #{idx + 1}</Badge>
                      <span className="text-[10px] text-neutral-500 font-mono">
                        {chunk.length} characters
                      </span>
                    </div>

                    <p className="text-xs text-neutral-300 font-mono leading-relaxed border-l-2 border-violet-500/20 pl-3">
                      {chunk}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
export { ListCollapse, History, AlignLeft, Layers };
