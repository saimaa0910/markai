'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2, Plus, Search, Trash2, X, Loader2, AlertCircle, Globe, Briefcase, Users as UsersIcon,
} from 'lucide-react';
import { useCompanies, useCreateCompany, useDeleteCompany } from '../queries';
import type { CompanyCreate } from '../types';

// ─── Create Company Dialog ──────────────────────────────────────────────────

function CreateCompanyDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createMutation = useCreateCompany();
  const [form, setForm] = React.useState<CompanyCreate>({ name: '' });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { setErrors({ name: 'Company name is required' }); return; }
    try {
      await createMutation.mutateAsync(form);
      setForm({ name: '' });
      setErrors({});
      onClose();
    } catch (err: any) {
      setErrors({ _form: err?.response?.data?.detail || 'Failed to create company' });
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Building2 className="w-5 h-5 text-blue-400" /> New Company</h2>
            <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
          </div>

          {errors._form && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {errors._form}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Company Name *</label>
              <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.name ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors`}
                placeholder="Acme Corporation" />
              {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Domain</label>
                <input value={form.domain || ''} onChange={e => setForm(p => ({ ...p, domain: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                  placeholder="acme.com" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Industry</label>
                <input value={form.industry || ''} onChange={e => setForm(p => ({ ...p, industry: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
                  placeholder="Technology" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Company Size</label>
              <select value={form.size || ''} onChange={e => setForm(p => ({ ...p, size: e.target.value || null }))}
                className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors">
                <option value="">Select size...</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-1000">201-1000 employees</option>
                <option value="1000+">1000+ employees</option>
              </select>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors">Cancel</button>
              <button type="submit" disabled={createMutation.isPending}
                className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                {createMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <><Plus className="w-4 h-4" /> Create Company</>}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ─── Main Companies Page ────────────────────────────────────────────────────

export default function CRMCompaniesPage() {
  const { data: companies, isLoading, error } = useCompanies();
  const deleteMutation = useDeleteCompany();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [showCreate, setShowCreate] = React.useState(false);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);

  const filtered = React.useMemo(() => {
    if (!companies) return [];
    if (!searchQuery.trim()) return companies;
    const q = searchQuery.toLowerCase();
    return companies.filter(c => c.name.toLowerCase().includes(q) || (c.domain && c.domain.toLowerCase().includes(q)) || (c.industry && c.industry.toLowerCase().includes(q)));
  }, [companies, searchQuery]);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try { await deleteMutation.mutateAsync(id); } finally { setDeletingId(null); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Companies</h1>
          <p className="text-sm text-zinc-500 mt-1">Track and manage your organization&apos;s companies</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-blue-500/20">
          <Plus className="w-4 h-4" /> Add Company
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center"><Building2 className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Total</p><p className="text-xl font-semibold text-white">{companies?.length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center"><Globe className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">With Domain</p><p className="text-xl font-semibold text-white">{companies?.filter(c => c.domain).length ?? '—'}</p></div>
        </div>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center"><Briefcase className="w-5 h-5" /></div>
          <div><p className="text-xs text-zinc-500 uppercase tracking-wider">Industries</p><p className="text-xl font-semibold text-white">{new Set(companies?.filter(c => c.industry).map(c => c.industry)).size || '—'}</p></div>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input type="text" placeholder="Search companies..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors placeholder:text-zinc-600" />
      </div>

      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 text-blue-400 animate-spin" /><span className="ml-3 text-zinc-500 text-sm">Loading companies...</span></div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-400"><AlertCircle className="w-8 h-8 mb-3" /><p className="text-sm">Failed to load companies</p></div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
            <Building2 className="w-10 h-10 mb-3 opacity-40" /><p className="text-sm font-medium">{searchQuery ? 'No companies match' : 'No companies yet'}</p>
            {!searchQuery && <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"><Plus className="w-4 h-4" /> Add Company</button>}
          </div>
        ) : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Company</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Domain</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Industry</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Size</th>
              <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Actions</th>
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filtered.map((company, i) => (
                <motion.tr key={company.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="hover:bg-zinc-800/30 transition-colors group">
                  <td className="px-5 py-4"><div className="flex items-center gap-3"><div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-xs font-semibold">{company.name[0]}</div><span className="text-sm font-medium text-white">{company.name}</span></div></td>
                  <td className="px-5 py-4 text-sm text-zinc-400">{company.domain || '—'}</td>
                  <td className="px-5 py-4"><span className="text-sm text-zinc-400">{company.industry || '—'}</span></td>
                  <td className="px-5 py-4 text-sm text-zinc-400">{company.size || '—'}</td>
                  <td className="px-5 py-4 text-right">
                    <button onClick={() => handleDelete(company.id)} disabled={deletingId === company.id} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50">
                      {deletingId === company.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <CreateCompanyDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
