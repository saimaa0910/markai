'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Building2, TrendingUp, Phone, Mail, Plus, Search, Trash2,
  ChevronDown, X, Loader2, UserPlus, AlertCircle, Filter,
} from 'lucide-react';
import { useContacts, useCreateContact, useDeleteContact, useCompanies } from '../queries';
import type { Contact, ContactCreate } from '../types';

// ─── Stat Card ──────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number | string; color: string }) {
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xs text-zinc-500 uppercase tracking-wider">{label}</p>
        <p className="text-xl font-semibold text-white">{value}</p>
      </div>
    </div>
  );
}

// ─── Contact Create Dialog ──────────────────────────────────────────────────

function CreateContactDialog({ open, onClose, companies }: { open: boolean; onClose: () => void; companies: { id: string; name: string }[] }) {
  const createMutation = useCreateContact();
  const [form, setForm] = React.useState<ContactCreate>({ first_name: '', last_name: '', email: '' });
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.first_name.trim()) e.first_name = 'First name is required';
    if (!form.last_name.trim()) e.last_name = 'Last name is required';
    if (!form.email.trim()) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Invalid email format';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    try {
      await createMutation.mutateAsync(form);
      setForm({ first_name: '', last_name: '', email: '' });
      setErrors({});
      onClose();
    } catch (err: any) {
      setErrors({ _form: err?.response?.data?.detail || 'Failed to create contact' });
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} transition={{ type: 'spring', damping: 25 }}
          className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><UserPlus className="w-5 h-5 text-violet-400" /> New Contact</h2>
            <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
          </div>

          {errors._form && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {errors._form}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">First Name *</label>
                <input value={form.first_name} onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))}
                  className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.first_name ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors`}
                  placeholder="Jane" />
                {errors.first_name && <p className="text-red-400 text-xs mt-1">{errors.first_name}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Last Name *</label>
                <input value={form.last_name} onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))}
                  className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.last_name ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors`}
                  placeholder="Doe" />
                {errors.last_name && <p className="text-red-400 text-xs mt-1">{errors.last_name}</p>}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Email *</label>
              <input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                className={`w-full px-3 py-2.5 bg-zinc-800 border ${errors.email ? 'border-red-500' : 'border-zinc-700'} rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors`}
                placeholder="jane@acme.com" />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Phone</label>
                <input value={form.phone || ''} onChange={e => setForm(p => ({ ...p, phone: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors"
                  placeholder="+1 (555) 000-0000" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Job Title</label>
                <input value={form.job_title || ''} onChange={e => setForm(p => ({ ...p, job_title: e.target.value || null }))}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors"
                  placeholder="VP of Marketing" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">Company</label>
              <select value={form.company_id || ''} onChange={e => setForm(p => ({ ...p, company_id: e.target.value || null }))}
                className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors">
                <option value="">No company</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors">Cancel</button>
              <button type="submit" disabled={createMutation.isPending}
                className="flex-1 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                {createMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <><Plus className="w-4 h-4" /> Create Contact</>}
              </button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ─── Main CRM Contacts Page ─────────────────────────────────────────────────

export default function CRMContactsPage() {
  const { data: contacts, isLoading, error } = useContacts();
  const { data: companies } = useCompanies();
  const deleteMutation = useDeleteContact();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [showCreateDialog, setShowCreateDialog] = React.useState(false);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);

  // Client-side search filter
  const filteredContacts = React.useMemo(() => {
    if (!contacts) return [];
    if (!searchQuery.trim()) return contacts;
    const q = searchQuery.toLowerCase();
    return contacts.filter(c =>
      c.first_name.toLowerCase().includes(q) ||
      c.last_name.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      (c.job_title && c.job_title.toLowerCase().includes(q))
    );
  }, [contacts, searchQuery]);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">CRM Contacts</h1>
          <p className="text-sm text-zinc-500 mt-1">Manage your organization&apos;s contact database</p>
        </div>
        <button onClick={() => setShowCreateDialog(true)}
          className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-violet-500/20">
          <Plus className="w-4 h-4" /> Add Contact
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Total Contacts" value={contacts?.length ?? '—'} color="bg-violet-500/20 text-violet-400" />
        <StatCard icon={Building2} label="Companies" value={companies?.length ?? '—'} color="bg-blue-500/20 text-blue-400" />
        <StatCard icon={Mail} label="With Email" value={contacts?.filter(c => c.email).length ?? '—'} color="bg-emerald-500/20 text-emerald-400" />
        <StatCard icon={Phone} label="With Phone" value={contacts?.filter(c => c.phone).length ?? '—'} color="bg-amber-500/20 text-amber-400" />
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input type="text" placeholder="Search contacts by name, email, or title..."
            value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-colors placeholder:text-zinc-600" />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <button className="px-3 py-2.5 bg-zinc-900/60 border border-zinc-800 rounded-lg text-zinc-400 hover:text-white text-sm flex items-center gap-2 transition-colors">
          <Filter className="w-4 h-4" /> Filters
        </button>
      </div>

      {/* Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
            <span className="ml-3 text-zinc-500 text-sm">Loading contacts...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-400">
            <AlertCircle className="w-8 h-8 mb-3" />
            <p className="text-sm font-medium">Failed to load contacts</p>
            <p className="text-xs text-zinc-600 mt-1">{(error as Error).message}</p>
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
            <Users className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm font-medium">{searchQuery ? 'No contacts match your search' : 'No contacts yet'}</p>
            <p className="text-xs text-zinc-600 mt-1">{searchQuery ? 'Try adjusting your filters' : 'Create your first contact to get started'}</p>
            {!searchQuery && (
              <button onClick={() => setShowCreateDialog(true)}
                className="mt-4 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                <Plus className="w-4 h-4" /> Add Contact
              </button>
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Name</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Email</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Phone</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Title</th>
                <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredContacts.map((contact, i) => (
                <motion.tr key={contact.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
                  className="hover:bg-zinc-800/30 transition-colors group">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white text-xs font-semibold">
                        {contact.first_name[0]}{contact.last_name[0]}
                      </div>
                      <span className="text-sm font-medium text-white">{contact.first_name} {contact.last_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-sm text-zinc-400">{contact.email}</td>
                  <td className="px-5 py-4 text-sm text-zinc-400">{contact.phone || '—'}</td>
                  <td className="px-5 py-4 text-sm text-zinc-400">{contact.job_title || '—'}</td>
                  <td className="px-5 py-4 text-right">
                    <button onClick={() => handleDelete(contact.id)} disabled={deletingId === contact.id}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50">
                      {deletingId === contact.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      {filteredContacts.length > 0 && (
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>Showing {filteredContacts.length} of {contacts?.length ?? 0} contacts</span>
        </div>
      )}

      {/* Create Dialog */}
      <CreateContactDialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} companies={companies?.map(c => ({ id: c.id, name: c.name })) ?? []} />
    </div>
  );
}
