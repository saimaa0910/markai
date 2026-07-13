'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import {
  Building2,
  Users,
  Briefcase,
  Plus,
  Loader2,
  ArrowLeft,
  Trash2,
  DollarSign,
  TrendingUp,
  Tag
} from 'lucide-react';

export default function CRMDashboard() {
  const router = useRouter();
  const { token, activeOrgId } = useAuthStore();

  const [activeTab, setActiveTab] = React.useState<'leads' | 'contacts' | 'companies'>('leads');
  const [companies, setCompanies] = React.useState<any[]>([]);
  const [contacts, setContacts] = React.useState<any[]>([]);
  const [leads, setLeads] = React.useState<any[]>([]);
  
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Form states
  const [newCompany, setNewCompany] = React.useState({ name: '', domain: '', industry: '', size: '' });
  const [newContact, setNewContact] = React.useState({ first_name: '', last_name: '', email: '', phone: '', job_title: '', company_id: '' });
  const [newLead, setNewLead] = React.useState({ title: '', status: 'NEW', value: '0.00', contact_id: '', company_id: '' });

  // Guard routing
  React.useEffect(() => {
    if (!token) {
      router.push('/auth/login');
    }
  }, [token, router]);

  const fetchCRMData = React.useCallback(async () => {
    if (!token || !activeOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': activeOrgId,
      };

      const [compsRes, contsRes, leadsRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/crm/companies/', { headers }),
        fetch('http://localhost:8000/api/v1/crm/contacts/', { headers }),
        fetch('http://localhost:8000/api/v1/crm/leads/', { headers }),
      ]);

      if (!compsRes.ok || !contsRes.ok || !leadsRes.ok) {
        throw new Error('Failed to retrieve CRM workspace data.');
      }

      const [compsData, contsData, leadsData] = await Promise.all([
        compsRes.json(),
        contsRes.json(),
        leadsRes.json(),
      ]);

      setCompanies(compsData);
      setContacts(contsData);
      setLeads(leadsData);
    } catch (err: any) {
      setError(err.message || 'An error occurred fetching data.');
    } finally {
      setLoading(false);
    }
  }, [token, activeOrgId]);

  React.useEffect(() => {
    fetchCRMData();
  }, [fetchCRMData]);

  // Actions
  const handleAddCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany.name.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/crm/companies/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify(newCompany),
      });
      if (!res.ok) throw new Error();
      setNewCompany({ name: '', domain: '', industry: '', size: '' });
      await fetchCRMData();
    } catch {
      setError('Failed to add company.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContact.first_name.trim() || !newContact.email.trim()) return;
    setSubmitting(true);
    try {
      const payload = { ...newContact, company_id: newContact.company_id || null };
      const res = await fetch('http://localhost:8000/api/v1/crm/contacts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      setNewContact({ first_name: '', last_name: '', email: '', phone: '', job_title: '', company_id: '' });
      await fetchCRMData();
    } catch {
      setError('Failed to add contact.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLead.title.trim()) return;
    setSubmitting(true);
    try {
      const payload = {
        ...newLead,
        value: parseFloat(newLead.value) || 0.0,
        contact_id: newLead.contact_id || null,
        company_id: newLead.company_id || null,
      };
      const res = await fetch('http://localhost:8000/api/v1/crm/leads/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      setNewLead({ title: '', status: 'NEW', value: '0.00', contact_id: '', company_id: '' });
      await fetchCRMData();
    } catch {
      setError('Failed to add lead.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteItem = async (type: 'companies' | 'contacts' | 'leads', id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/crm/${type}/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
      });
      if (!res.ok) throw new Error();
      await fetchCRMData();
    } catch {
      setError(`Failed to delete ${type.slice(0, -1)}.`);
    }
  };

  // Pipeline metrics
  const totalPipelineValue = leads.reduce((acc, lead) => acc + (parseFloat(lead.value) || 0), 0);
  const activeLeadsCount = leads.filter((l) => l.status !== 'LOST').length;

  return (
    <div className="min-h-screen bg-black text-white relative">
      {/* Background glow */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Navigation back */}
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors mb-6 text-sm font-semibold cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">CRM Workspace</h1>
            <p className="text-neutral-400 mt-1">Nurture leads, log customer activities and track revenue pipelines.</p>
          </div>

          {/* Quick Metrics */}
          <div className="flex gap-4">
            <Card className="py-3 px-5 flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-semibold">Pipeline Value</p>
                <p className="text-lg font-bold">${totalPipelineValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
            <Card className="py-3 px-5 flex items-center gap-3">
              <Tag className="w-5 h-5 text-violet-400" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-semibold">Active Leads</p>
                <p className="text-lg font-bold">{activeLeadsCount}</p>
              </div>
            </Card>
          </div>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {/* Workspace Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Main List Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-white/10 gap-4">
              {[
                { id: 'leads', label: 'Leads', icon: Briefcase },
                { id: 'contacts', label: 'Contacts', icon: Users },
                { id: 'companies', label: 'Companies', icon: Building2 },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
                      activeTab === tab.id
                        ? 'border-violet-500 text-violet-400'
                        : 'border-transparent text-neutral-400 hover:text-white'
                    }`}
                  >
                    <Icon className="w-4 h-4" /> {tab.label}
                  </button>
                );
              })}
            </div>

            {loading ? (
              <div className="py-20 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
              </div>
            ) : (
              <div className="space-y-3">
                {/* LEADS LIST */}
                {activeTab === 'leads' && (
                  leads.length === 0 ? (
                    <p className="text-neutral-500 text-sm text-center py-12">No sales leads tracked yet.</p>
                  ) : (
                    leads.map((lead) => (
                      <Card key={lead.id} className="flex justify-between items-center glass p-4">
                        <div>
                          <h4 className="font-bold text-base">{lead.title}</h4>
                          <div className="flex gap-4 mt-1 text-xs text-neutral-400">
                            <span>Status: <strong className="text-violet-300">{lead.status}</strong></span>
                            <span>Value: <strong>${parseFloat(lead.value).toFixed(2)}</strong></span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteItem('leads', lead.id)}
                          className="p-2 rounded text-neutral-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </Card>
                    ))
                  )
                )}

                {/* CONTACTS LIST */}
                {activeTab === 'contacts' && (
                  contacts.length === 0 ? (
                    <p className="text-neutral-500 text-sm text-center py-12">No contacts logged yet.</p>
                  ) : (
                    contacts.map((contact) => (
                      <Card key={contact.id} className="flex justify-between items-center glass p-4">
                        <div>
                          <h4 className="font-bold text-base">{contact.first_name} {contact.last_name}</h4>
                          <p className="text-xs text-neutral-400 mt-1">{contact.job_title || 'Contact'} • {contact.email}</p>
                        </div>
                        <button
                          onClick={() => handleDeleteItem('contacts', contact.id)}
                          className="p-2 rounded text-neutral-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </Card>
                    ))
                  )
                )}

                {/* COMPANIES LIST */}
                {activeTab === 'companies' && (
                  companies.length === 0 ? (
                    <p className="text-neutral-500 text-sm text-center py-12">No companies linked yet.</p>
                  ) : (
                    companies.map((comp) => (
                      <Card key={comp.id} className="flex justify-between items-center glass p-4">
                        <div>
                          <h4 className="font-bold text-base">{comp.name}</h4>
                          <p className="text-xs text-neutral-400 mt-1">{comp.industry || 'Industry'} • {comp.domain || 'no domain'}</p>
                        </div>
                        <button
                          onClick={() => handleDeleteItem('companies', comp.id)}
                          className="p-2 rounded text-neutral-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </Card>
                    ))
                  )
                )}
              </div>
            )}
          </div>

          {/* Creation Forms Area */}
          <div>
            <Card className="glass p-6">
              <h3 className="font-bold text-lg mb-6">Create New Record</h3>
              
              {activeTab === 'companies' && (
                <form onSubmit={handleAddCompany} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Company Name</label>
                    <input
                      type="text"
                      required
                      value={newCompany.name}
                      onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                      placeholder="Acme Corp"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Domain</label>
                    <input
                      type="text"
                      value={newCompany.domain}
                      onChange={(e) => setNewCompany({ ...newCompany, domain: e.target.value })}
                      placeholder="acme.com"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Industry</label>
                    <input
                      type="text"
                      value={newCompany.industry}
                      onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                      placeholder="Technology"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-2.5 rounded bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm cursor-pointer disabled:opacity-50"
                  >
                    Add Company
                  </button>
                </form>
              )}

              {activeTab === 'contacts' && (
                <form onSubmit={handleAddContact} className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">First Name</label>
                      <input
                        type="text"
                        required
                        value={newContact.first_name}
                        onChange={(e) => setNewContact({ ...newContact, first_name: e.target.value })}
                        placeholder="Alice"
                        className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Last Name</label>
                      <input
                        type="text"
                        required
                        value={newContact.last_name}
                        onChange={(e) => setNewContact({ ...newContact, last_name: e.target.value })}
                        placeholder="Smith"
                        className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Email Address</label>
                    <input
                      type="email"
                      required
                      value={newContact.email}
                      onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                      placeholder="alice@company.com"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Company Link</label>
                    <select
                      value={newContact.company_id}
                      onChange={(e) => setNewContact({ ...newContact, company_id: e.target.value })}
                      className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-sm text-white focus:border-violet-500 focus:outline-none"
                    >
                      <option value="">No Company</option>
                      {companies.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-2.5 rounded bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm cursor-pointer disabled:opacity-50"
                  >
                    Add Contact
                  </button>
                </form>
              )}

              {activeTab === 'leads' && (
                <form onSubmit={handleAddLead} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Lead Name / Title</label>
                    <input
                      type="text"
                      required
                      value={newLead.title}
                      onChange={(e) => setNewLead({ ...newLead, title: e.target.value })}
                      placeholder="Enterprise SaaS License"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Pipeline Value ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newLead.value}
                        onChange={(e) => setNewLead({ ...newLead, value: e.target.value })}
                        placeholder="5000.00"
                        className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Initial Status</label>
                      <select
                        value={newLead.status}
                        onChange={(e) => setNewLead({ ...newLead, status: e.target.value })}
                        className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-sm text-white focus:border-violet-500 focus:outline-none"
                      >
                        <option value="NEW">New</option>
                        <option value="CONTACTED">Contacted</option>
                        <option value="QUALIFIED">Qualified</option>
                        <option value="LOST">Lost</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Primary Contact</label>
                    <select
                      value={newLead.contact_id}
                      onChange={(e) => setNewLead({ ...newLead, contact_id: e.target.value })}
                      className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-sm text-white focus:border-violet-500 focus:outline-none"
                    >
                      <option value="">Select Contact...</option>
                      {contacts.map((c) => (
                        <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-2.5 rounded bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm cursor-pointer disabled:opacity-50"
                  >
                    Create Lead
                  </button>
                </form>
              )}
            </Card>
          </div>

        </div>

      </div>
    </div>
  );
}
