'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Megaphone, Plus, Play, Trash2, X, Loader2, AlertCircle, Search, BarChart2, Split, CheckCircle2, Clock, PauseCircle, Send, DollarSign,
} from 'lucide-react';
import { useCampaigns, useCreateCampaign, useDeleteCampaign, useExecuteCampaign } from '../queries';
import type { CampaignCreate, CampaignChannel, CampaignStatus } from '../types';

const CHANNEL_ICONS: Record<CampaignChannel, string> = {
  EMAIL: '📧 Email',
  SMS: '📱 SMS',
  SOCIAL_AD: '📣 Social Ad',
  BLOG: '📝 Blog',
  WEBHOOK: '⚡ Webhook',
};

const STATUS_BADGES: Record<CampaignStatus, { bg: string; text: string }> = {
  DRAFT: { bg: 'bg-zinc-800', text: 'text-zinc-400' },
  SCHEDULED: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
  RUNNING: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
  COMPLETED: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
  PAUSED: { bg: 'bg-purple-500/10', text: 'text-purple-400' },
  FAILED: { bg: 'bg-red-500/10', text: 'text-red-400' },
};

function CreateCampaignDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createMutation = useCreateCampaign();
  const [form, setForm] = React.useState<CampaignCreate>({
    title: '',
    description: '',
    budget: 500,
    channel: 'EMAIL',
    template: {
      title: 'Default Variant Template',
      subject: 'Special Offer inside!',
      content_a: 'Get 20% off your next purchase using code SUMMER20.',
      content_b: 'Exclusive discount inside! Save 20% on all plans.',
    },
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { setErrors({ title: 'Campaign title is required' }); return; }
    if (!form.template.content_a.trim()) { setErrors({ content_a: 'Variant A content is required' }); return; }

    try {
      await createMutation.mutateAsync(form);
      onClose();
    } catch (err: any) {
      setErrors({ _form: err?.response?.data?.detail || 'Failed to create campaign' });
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-2xl p-6 shadow-2xl overflow-y-auto max-h-[90vh]" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Megaphone className="w-5 h-5 text-fuchsia-400" /> New Campaign & A/B Creative Builder</h2>
            <button onClick={onClose} className="text-zinc-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>

          {errors._form && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {errors._form}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Campaign Title *</label>
                <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
                  className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.title ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50`}
                  placeholder="Q3 Summer Launch Campaign" />
                {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Channel</label>
                <select value={form.channel} onChange={e => setForm(p => ({ ...p, channel: e.target.value as CampaignChannel }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50">
                  <option value="EMAIL">Email Campaign</option>
                  <option value="SMS">SMS Notification</option>
                  <option value="SOCIAL_AD">Social Media Ad</option>
                  <option value="BLOG">Blog Promotion</option>
                  <option value="WEBHOOK">Outbound Webhook</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Budget ($)</label>
                <input type="number" value={form.budget || 0} onChange={e => setForm(p => ({ ...p, budget: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Subject / Headline</label>
                <input value={form.template.subject || ''} onChange={e => setForm(p => ({ ...p, template: { ...p.template, subject: e.target.value } }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50"
                  placeholder="Don't miss our summer sale" />
              </div>
            </div>

            {/* A/B Test Creative Copy */}
            <div className="border border-zinc-800 rounded-xl p-4 bg-zinc-950/40 space-y-3">
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5"><Split className="w-4 h-4 text-fuchsia-400" /> A/B Creative Variants</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Variant A Copy *</label>
                  <textarea rows={3} value={form.template.content_a} onChange={e => setForm(p => ({ ...p, template: { ...p.template, content_a: e.target.value } }))}
                    className="w-full p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-xs focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Variant B Copy (Optional)</label>
                  <textarea rows={3} value={form.template.content_b || ''} onChange={e => setForm(p => ({ ...p, template: { ...p.template, content_b: e.target.value } }))}
                    className="w-full p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-xs focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50" />
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium">Cancel</button>
              <button type="submit" disabled={createMutation.isPending}
                className="flex-1 px-4 py-2.5 bg-fuchsia-600 hover:bg-fuchsia-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2">
                {createMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <><Plus className="w-4 h-4" /> Create Campaign</>}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function CampaignPlatformPage() {
  const { data: campaigns, isLoading, error } = useCampaigns();
  const deleteMutation = useDeleteCampaign();
  const executeMutation = useExecuteCampaign();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [showCreate, setShowCreate] = React.useState(false);
  const [executingId, setExecutingId] = React.useState<string | null>(null);

  const filteredCampaigns = React.useMemo(() => {
    if (!campaigns) return [];
    if (!searchQuery.trim()) return campaigns;
    return campaigns.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [campaigns, searchQuery]);

  const handleExecute = async (id: string) => {
    setExecutingId(id);
    try { await executeMutation.mutateAsync(id); } finally { setExecutingId(null); }
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Campaign Platform</h1>
          <p className="text-sm text-zinc-500 mt-1">Multi-channel campaign execution & A/B analytics testing engine</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-fuchsia-600 hover:bg-fuchsia-500 text-white rounded-lg text-sm font-medium flex items-center gap-2 shadow-lg shadow-fuchsia-500/20">
          <Plus className="w-4 h-4" /> Create Campaign
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center"><Megaphone className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Total Campaigns</p><p className="text-xl font-semibold text-white">{campaigns?.length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><Play className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Active Running</p><p className="text-xl font-semibold text-white">{campaigns?.filter(c => c.status === 'RUNNING' || c.status === 'COMPLETED').length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center"><Split className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">A/B Tested</p><p className="text-xl font-semibold text-white">{campaigns?.filter(c => c.template?.content_b).length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center"><DollarSign className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Attributed Revenue</p><p className="text-xl font-semibold text-white">${campaigns?.reduce((acc, c) => acc + (c.analytics?.revenue || 0), 0).toLocaleString()}</p></div>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input type="text" placeholder="Search campaigns..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50" />
      </div>

      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 text-fuchsia-400 animate-spin" /><span className="ml-3 text-zinc-500 text-sm">Loading campaigns...</span></div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-400"><AlertCircle className="w-8 h-8 mb-3" /><p className="text-sm">Failed to load campaigns</p></div>
        ) : filteredCampaigns.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
            <Megaphone className="w-10 h-10 mb-3 opacity-40" /><p className="text-sm font-medium">No campaigns found</p>
            {!searchQuery && <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-fuchsia-600 text-white rounded-lg text-sm font-medium"><Plus className="w-4 h-4 inline mr-1" /> Create Campaign</button>}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Campaign Title</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Channel</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">A/B Analytics</th>
                <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredCampaigns.map((c, i) => {
                const badge = STATUS_BADGES[c.status] || STATUS_BADGES.DRAFT;
                return (
                  <motion.tr key={c.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="hover:bg-zinc-800/30 transition-colors group">
                    <td className="px-5 py-4"><span className="text-sm font-medium text-white block">{c.title}</span><span className="text-xs text-zinc-500">Budget: ${c.budget}</span></td>
                    <td className="px-5 py-4 text-sm text-zinc-300">{CHANNEL_ICONS[c.channel] || c.channel}</td>
                    <td className="px-5 py-4"><span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${badge.bg} ${badge.text}`}>{c.status}</span></td>
                    <td className="px-5 py-4 text-xs text-zinc-400">
                      {c.analytics ? (
                        <span>A: {c.analytics.clicks_a} clicks | B: {c.analytics.clicks_b} clicks</span>
                      ) : (
                        <span className="text-zinc-600">No data</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-right flex items-center justify-end gap-2">
                      <button onClick={() => handleExecute(c.id)} disabled={executingId === c.id} className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 text-xs font-medium flex items-center gap-1">
                        {executingId === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />} Execute
                      </button>
                      <button onClick={() => handleDelete(c.id)} className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10"><Trash2 className="w-4 h-4" /></button>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <CreateCampaignDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
