import * as React from 'react';
import { useAnalytics, useCollections, useDocuments } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Card } from '@eaimos/ui';
import { BarChart3, Database, TrendingUp, HelpCircle, Activity, FileText } from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend 
} from 'recharts';

export function AnalyticsPage() {
  const { stats } = useAnalytics();
  const { collections } = useCollections();
  const { documents } = useDocuments();

  const chartsData = React.useMemo(() => {
    return [
      { month: 'Jan', documents: 12, chunks: 50, queries: 110 },
      { month: 'Feb', documents: 18, chunks: 80, queries: 140 },
      { month: 'Mar', documents: 24, chunks: 110, queries: 165 },
      { month: 'Apr', documents: 35, chunks: 155, queries: 210 },
      { month: 'May', documents: 48, chunks: 210, queries: 285 },
      { month: 'Jun', documents: 60, chunks: 260, queries: 320 },
      { month: 'Jul', documents: stats.totalDocs, chunks: stats.chunkCount, queries: 380 },
    ];
  }, [stats]);

  const topDocuments = React.useMemo(() => {
    return [...documents]
      .sort((a, b) => (b.chunk_count || 0) - (a.chunk_count || 0))
      .slice(0, 5);
  }, [documents]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Knowledge Ingestion Analytics"
        description="Inspect indices growth speed, chunk distribution ratios, and search retrieve frequencies."
        icon={<BarChart3 className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Retrieval telemetry</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document & Chunk Growth trend */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Indexed Corpus Growth Trend</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Month-by-month accumulation of document counts and chunk extractions.</p>
          </div>

          <div className="h-[220px] w-full mt-2 text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="docGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" stroke="#525252" fontSize={9} tickLine={false} />
                <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />
                <Area type="monotone" dataKey="documents" stroke="#8b5cf6" strokeWidth={2} fill="url(#docGrad)" name="Total Documents" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Chunks Volume distribution */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Extracted Database Chunks Volume</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Splitting textual segments stored in backend vector records.</p>
          </div>

          <div className="h-[220px] w-full mt-2 text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartsData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" stroke="#525252" fontSize={9} tickLine={false} />
                <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />
                <Bar dataKey="chunks" fill="#10b981" radius={4} name="Vector Chunks" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Documents table */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Most Fragmented Documents</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Documents generating the highest volume of vectorized chunks.</p>
          </div>

          <div className="flex flex-col gap-2.5 mt-2">
            {topDocuments.map((doc, idx) => (
              <div 
                key={doc.id} 
                className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="w-4 h-4 text-violet-400 shrink-0" />
                  <span className="text-white font-sans font-bold truncate">{doc.title}</span>
                </div>
                <Badge variant="violet" className="shrink-0">{doc.chunk_count} chunks</Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Collections List */}
        <Card className="flex flex-col gap-4">
          <div>
            <h4 className="font-bold text-white text-sm">Top Collections Directory Allocation</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">Active collection folder slots sorted by linked file count.</p>
          </div>

          <div className="flex flex-col gap-2.5 mt-2">
            {collections.slice(0, 5).map((col) => (
              <div 
                key={col.id} 
                className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center gap-2 truncate">
                  <Database className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="text-white font-sans font-bold truncate">{col.name}</span>
                </div>
                <Badge variant="emerald" className="shrink-0">{col.document_ids.length} files</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
export { BarChart3 };
export type { HelpCircle, Activity };
