'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  Search, Globe, TrendingUp, AlertTriangle, CheckCircle2, RefreshCw, Plus, Loader2, ArrowUpRight, BarChart2, ShieldCheck,
} from 'lucide-react';
import { useSEOOverview, useAddKeyword, useRunAudit } from '../queries';

export default function SEOPage() {
  const { data: seoData, isLoading } = useSEOOverview();
  const addKeywordMutation = useAddKeyword();
  const runAuditMutation = useRunAudit();

  const [keywordInput, setKeywordInput] = React.useState('');

  const mockKeywords = React.useMemo(() => {
    if (seoData?.keywords && seoData.keywords.length > 0) return seoData.keywords;
    return [
      { id: '1', keyword: 'ai marketing software', search_volume: 18100, difficulty: 64, current_rank: 4, intent: 'COMMERCIAL' as const, cpc: 12.50 },
      { id: '2', keyword: 'enterprise rag platform', search_volume: 8400, difficulty: 52, current_rank: 2, intent: 'TRANSACTIONAL' as const, cpc: 18.20 },
      { id: '3', keyword: 'autonomous marketing agents', search_volume: 14200, difficulty: 71, current_rank: 8, intent: 'INFORMATIONAL' as const, cpc: 9.80 },
      { id: '4', keyword: 'multi tenant prompt gateway', search_volume: 3600, difficulty: 41, current_rank: 1, intent: 'COMMERCIAL' as const, cpc: 15.00 },
    ];
  }, [seoData]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keywordInput.trim()) return;
    try {
      await addKeywordMutation.mutateAsync(keywordInput);
      setKeywordInput('');
    } catch (e) {
      console.error('Add keyword error', e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-cyan-400" /> SEO & SERP Rank Intelligence
          </h1>
          <p className="text-sm text-zinc-500 mt-1">SERP rank tracking, automated technical site audit, and keyword cluster analysis</p>
        </div>
        <button onClick={() => runAuditMutation.mutate('viptant.ai')} disabled={runAuditMutation.isPending}
          className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-cyan-500/20">
          {runAuditMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Run Site Audit
        </button>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><ShieldCheck className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Health Score</p><p className="text-xl font-semibold text-white">{seoData?.health_score ?? 94} / 100</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center"><Search className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Tracked Keywords</p><p className="text-xl font-semibold text-white">{mockKeywords.length}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center"><TrendingUp className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Top 10 Rankings</p><p className="text-xl font-semibold text-white">{mockKeywords.filter(k => k.current_rank <= 10).length}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center"><BarChart2 className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Monthly Traffic</p><p className="text-xl font-semibold text-white">{(seoData?.organic_traffic ?? 45200).toLocaleString()}</p></div>
        </div>
      </div>

      {/* Add Keyword Input Bar */}
      <form onSubmit={handleAdd} className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input type="text" placeholder="Enter keyword to track SERP rank..." value={keywordInput} onChange={e => setKeywordInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50" />
        </div>
        <button type="submit" disabled={addKeywordMutation.isPending}
          className="px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 border border-zinc-700">
          <Plus className="w-4 h-4 text-cyan-400" /> Track Keyword
        </button>
      </form>

      {/* Keywords Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Keyword Phrase</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Search Volume</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">SERP Rank</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Difficulty</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">CPC ($)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {mockKeywords.map((kw, i) => (
              <motion.tr key={kw.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }} className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-5 py-4"><span className="text-sm font-medium text-white block">{kw.keyword}</span><span className="text-[10px] text-cyan-400 font-mono">{kw.intent}</span></td>
                <td className="px-5 py-4 text-sm text-zinc-300">{kw.search_volume.toLocaleString()} / mo</td>
                <td className="px-5 py-4"><span className={`px-2.5 py-1 text-xs font-bold rounded-full ${kw.current_rank <= 3 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-blue-500/10 text-blue-400'}`}>#{kw.current_rank}</span></td>
                <td className="px-5 py-4 text-sm text-zinc-400">{kw.difficulty} / 100</td>
                <td className="px-5 py-4 text-sm font-semibold text-emerald-400">${kw.cpc.toFixed(2)}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
