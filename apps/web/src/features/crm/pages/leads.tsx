'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, Plus, Search, Trash2, X, Loader2, AlertCircle, DollarSign, UserCheck, Filter, Edit3,
} from 'lucide-react';
import { useLeads, useCreateLead, useUpdateLead, useDeleteLead, useContacts, useCompanies } from '../queries';
import type { LeadCreate, LeadStatus } from '../types';

const LEAD_STATUS_COLORS: Record<LeadStatus, { bg: string; text: string; border: string }> = {
  NEW: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  CONTACTED: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
  QUALIFIED: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30' },
  PROPOSAL: { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/30' },
  NEGOTIATION: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  WON: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  LOST: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
};

function CreateLeadDialog({ open, onClose, contacts, companies }: { open: boolean; onClose: () => void; contacts: { id: string; name: string }[]; companies: { id: string; name: string }[] }) {
  const createMutation = useCreateLead();
  const [form, setForm] = React.useState<LeadCreate>({ title: '', value: 0, status: 'NEW' });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { setErrors({ title: 'Lead title is required' }); return; }
    try {
      await createMutation.mutateAsync(form);
      setForm({ title: '', value: 0, status: 'NEW' });
      setErrors({});
      onClose();
    } catch (err: any) {
      setErrors({ _form: err?.response?.data?.detail || 'Failed to create lead' });
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><TrendingUp className="w-5 h-5 text-emerald-400" /> New Lead / Opportunity</h2>
            <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
          </div>

          {errors._form && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {errors._form}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Lead Title *</label>
              <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
                className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.title ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors`}
                placeholder="Enterprise Software Renewal" />
              {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Estimated Value ($)</label>
                <input type="number" value={form.value || 0} onChange={e => setForm(p => ({ ...p, value: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors"
                  placeholder="10000" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Initial Status</label>
                <select value={form.status || 'NEW'} onChange={e => setForm(p => ({ ...p, status: e.target.value as LeadStatus }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors">
                  <option value="NEW">New</option>
                  <option value="CONTACTED">Contacted</option>
                  <option value="QUALIFIED">Qualified</option>
                  <option value="PROPOSAL">Proposal</option>
                  <option value="NEGOTIATION">Negotiation</option>
                  <option value="WON">Won</option>
                  <option value="LOST">Lost</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Primary Contact</label>
                <select value={form.contact_id || ''} onChange={e => setForm(p => ({ ...p, contact_id: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors">
                  <option value="">Select contact...</option>
                  {contacts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Company</label>
                <select value={form.company_id || ''} onChange={e => setForm(p => ({ ...p, company_id: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors">
                  <option value="">Select company...</option>
                  {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors">Cancel</button>
              <button type="submit" disabled={createMutation.isPending}
                className="flex-1 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                {createMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <><Plus className="w-4 h-4" /> Create Lead</>}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function CRMLeadsPage() {
  const { data: leads, isLoading, error } = useLeads();
  const { data: contacts } = useContacts();
  const { data: companies } = useCompanies();
  const updateMutation = useUpdateLead();
  const deleteMutation = useDeleteLead();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('ALL');
  const [showCreate, setShowCreate] = React.useState(false);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);

  const filteredLeads = React.useMemo(() => {
    if (!leads) return [];
    return leads.filter(l => {
      const matchesSearch = l.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'ALL' || l.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [leads, searchQuery, statusFilter]);

  const totalValue = React.useMemo(() => {
    return (leads || []).reduce((acc, l) => acc + (l.value || 0), 0);
  }, [leads]);

  const handleStatusChange = async (leadId: string, newStatus: LeadStatus) => {
    try {
      await updateMutation.mutateAsync({ id: leadId, data: { status: newStatus } });
    } catch (e) {
      console.error('Failed to update lead status', e);
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try { await deleteMutation.mutateAsync(id); } finally { setDeletingId(null); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Leads & Opportunities</h1>
          <p className="text-sm text-zinc-500 mt-1">Track pipeline progress and potential deal value</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-emerald-500/20">
          <Plus className="w-4 h-4" /> Add Lead
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><TrendingUp className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Total Leads</p><p className="text-xl font-semibold text-white">{leads?.length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center"><DollarSign className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Pipeline Value</p><p className="text-xl font-semibold text-white">${totalValue.toLocaleString()}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center"><UserCheck className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Won Deals</p><p className="text-xl font-semibold text-white">{leads?.filter(l => l.status === 'WON').length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center"><Filter className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">In Qualification</p><p className="text-xl font-semibold text-white">{leads?.filter(l => l.status === 'QUALIFIED' || l.status === 'PROPOSAL').length ?? '—'}</p></div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input type="text" placeholder="Search leads by title..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors placeholder:text-zinc-600" />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-zinc-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
          <option value="ALL">All Statuses</option>
          <option value="NEW">New</option>
          <option value="CONTACTED">Contacted</option>
          <option value="QUALIFIED">Qualified</option>
          <option value="PROPOSAL">Proposal</option>
          <option value="NEGOTIATION">Negotiation</option>
          <option value="WON">Won</option>
          <option value="LOST">Lost</option>
        </select>
      </div>

      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 text-emerald-400 animate-spin" /><span className="ml-3 text-zinc-500 text-sm">Loading leads...</span></div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-400"><AlertCircle className="w-8 h-8 mb-3" /><p className="text-sm font-medium">Failed to load leads</p></div>
        ) : filteredLeads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
            <TrendingUp className="w-10 h-10 mb-3 opacity-40" /><p className="text-sm font-medium">No leads found</p>
            {!searchQuery && <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium"><Plus className="w-4 h-4 inline mr-1" /> Add Lead</button>}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Opportunity</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Value</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Status Stage</th>
                <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredLeads.map((lead, i) => {
                const colors = LEAD_STATUS_COLORS[lead.status] || LEAD_STATUS_COLORS.NEW;
                return (
                  <motion.tr key={lead.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="hover:bg-zinc-800/30 transition-colors group">
                    <td className="px-5 py-4"><span className="text-sm font-medium text-white">{lead.title}</span></td>
                    <td className="px-5 py-4 text-sm font-semibold text-emerald-400">${(lead.value || 0).toLocaleString()}</td>
                    <td className="px-5 py-4">
                      <select value={lead.status} onChange={e => handleStatusChange(lead.id, e.target.value as LeadStatus)}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${colors.bg} ${colors.text} ${colors.border} focus:outline-none cursor-pointer`}>
                        <option value="NEW">NEW</option>
                        <option value="CONTACTED">CONTACTED</option>
                        <option value="QUALIFIED">QUALIFIED</option>
                        <option value="PROPOSAL">PROPOSAL</option>
                        <option value="NEGOTIATION">NEGOTIATION</option>
                        <option value="WON">WON</option>
                        <option value="LOST">LOST</option>
                      </select>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button onClick={() => handleDelete(lead.id)} disabled={deletingId === lead.id} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                        {deletingId === lead.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </button>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <CreateLeadDialog open={showCreate} onClose={() => setShowCreate(false)}
        contacts={contacts?.map(c => ({ id: c.id, name: `${c.first_name} ${c.last_name}` })) ?? []}
        companies={companies?.map(c => ({ id: c.id, name: c.name })) ?? []} />
    </div>
  );
}
