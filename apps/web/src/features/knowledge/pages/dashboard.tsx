import * as React from 'react';
import { useDocuments, useCollections, useEmbeddings, useAnalytics } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { 
  FileText, FolderOpen, Database, TrendingUp, Search, 
  Upload, Sparkles, Activity, Clock, Server, ArrowRight 
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip 
} from 'recharts';
import { motion } from 'framer-motion';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-white/10 rounded-lg p-2.5 shadow-xl text-xs font-mono">
      <p className="text-neutral-500 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span style={{ color: p.color }}>●</span>
          <span className="text-neutral-300">{p.name}:</span>
          <span className="font-bold text-white">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export function DashboardPage() {
  const { documents, isLoading: loadingDocs } = useDocuments();
  const { collections } = useCollections();
  const { stats: embedStats } = useEmbeddings();
  const { stats: analyticStats } = useAnalytics();

  // Simulated chart data
  const chartsData = React.useMemo(() => {
    // Generate daily upload logs
    const mockStorage = [
      { date: 'Jul 05', storage: 120, queries: 40 },
      { date: 'Jul 06', storage: 150, queries: 55 },
      { date: 'Jul 07', storage: 210, queries: 75 },
      { date: 'Jul 08', storage: 240, queries: 60 },
      { date: 'Jul 09', storage: 310, queries: 95 },
      { date: 'Jul 10', storage: 400, queries: 110 },
      { date: 'Jul 11', storage: 440, queries: 80 },
      { date: 'Jul 12', storage: 490, queries: 130 },
      { date: 'Jul 13', storage: 550, queries: 145 },
      { date: 'Jul 14', storage: 620, queries: 160 },
    ];
    return mockStorage;
  }, []);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Header section */}
      <PageHeader
        title="Knowledge Base Dashboard"
        description="Unified cognitive document portal featuring semantic vector indexing, collection folders, and chunking analytics."
        icon={<Database className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Enterprise RAG</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <a href="/dashboard/knowledge/search">
              <Button variant="outline" size="sm" className="h-8 text-[11px] border-white/5 bg-neutral-900/50 hover:bg-neutral-900">
                <Search className="w-3.5 h-3.5 mr-1" />
                Query Workspace
              </Button>
            </a>
            <a href="/dashboard/knowledge/upload">
              <Button variant="violet" size="sm" className="h-8 text-[11px]">
                <Upload className="w-3.5 h-3.5 mr-1" />
                Upload Document
              </Button>
            </a>
          </div>
        }
      />

      {/* KPI Stats counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Documents"
          value={embedStats.totalDocs}
          icon={<FileText className="w-4 h-4 text-violet-400" />}
          description="Inference document counts"
          isLoading={loadingDocs}
        />
        <StatCard
          title="Vector Embeddings"
          value={embedStats.vectorCount}
          icon={<Sparkles className="w-4 h-4 text-emerald-400" />}
          iconColor="text-emerald-400"
          description="Chunks stored in pgvector"
          isLoading={loadingDocs}
        />
        <StatCard
          title="Storage Allocated"
          value={`${analyticStats.totalStorageKb} KB`}
          icon={<Server className="w-4 h-4 text-sky-400" />}
          description="Physical disk space used"
          isLoading={loadingDocs}
        />
        <StatCard
          title="Indexed Ratio"
          value={`${embedStats.progressPercent}%`}
          icon={<Activity className="w-4 h-4 text-amber-400" />}
          description="Successful chunk conversions"
          isLoading={loadingDocs}
        />
      </div>

      {/* Grid layouts for charts and listings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CHARTS CONTAINER (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Storage Growth chart */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Workspace Storage Growth (KB)</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Accumulation of raw file sizes indexed in the database.</p>
            </div>

            <div className="h-[200px] w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="storageGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="storage" stroke="#8b5cf6" strokeWidth={2} fill="url(#storageGrad)" name="Storage (KB)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Search Query Volume chart */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Semantic Retrieval Activity</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Daily query counts hitting vector similarity check nodes.</p>
            </div>

            <div className="h-[200px] w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="queries" fill="#10b981" radius={4} name="Vector Queries" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* LISTINGS CONTAINER (Right 1 column) */}
        <div className="flex flex-col gap-6">
          
          {/* Active Collections */}
          <Card className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-sm">Library Collections</h4>
                <p className="text-[11px] text-neutral-500 mt-0.5">Directory folder groups</p>
              </div>
              <a href="/dashboard/knowledge/collections" className="text-[10px] text-violet-400 font-semibold flex items-center hover:underline">
                View All <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </a>
            </div>

            <div className="flex flex-col gap-3 mt-1">
              {collections.map((col) => (
                <a 
                  key={col.id} 
                  href={`/dashboard/knowledge/collections/${col.id}`}
                  className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/20 hover:border-violet-500/20 transition-all flex items-start gap-3 group"
                >
                  <FolderOpen className="w-4 h-4 text-violet-400 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-white">{col.name}</span>
                    <span className="text-[10px] text-neutral-500 mt-0.5">{col.description || 'No description'}</span>
                  </div>
                </a>
              ))}
            </div>
          </Card>

          {/* Recent Uploads */}
          <Card className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-sm">Recent Uploads</h4>
                <p className="text-[11px] text-neutral-500 mt-0.5">Newly indexed documents</p>
              </div>
              <a href="/dashboard/knowledge/documents" className="text-[10px] text-violet-400 font-semibold flex items-center hover:underline">
                View All <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </a>
            </div>

            <div className="flex flex-col gap-3 mt-1">
              {documents.slice(0, 4).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
                    <span className="text-neutral-300 truncate font-semibold">{doc.title}</span>
                  </div>
                  <Badge variant="emerald" className="font-mono text-[9px] uppercase shrink-0">
                    {doc.file_type}
                  </Badge>
                </div>
              ))}

              {documents.length === 0 && (
                <div className="py-8 flex flex-col items-center justify-center text-center text-neutral-600">
                  <FileText className="w-6 h-6 mb-1" />
                  <span className="text-xs font-medium">No documents yet</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
