'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import { 
  Building2, Users, Briefcase, Plus, Trash2, TrendingUp, Tag, 
  Search, ArrowUpDown, ChevronLeft, ChevronRight, Activity, Calendar, Eye, Phone, Mail
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/services/api-client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export default function CRMDashboard() {
  const queryClient = useQueryClient();
  const { activeOrg } = useAuthStore();
  const [activeTab, setActiveTab] = React.useState<'leads' | 'contacts' | 'companies'>('leads');
  const [leadsViewMode, setLeadsViewMode] = React.useState<'list' | 'kanban'>('kanban');
  
  // Dialog detailed view triggers
  const [selectedLeadId, setSelectedLeadId] = React.useState<string | null>(null);
  const [showAddActivity, setShowAddActivity] = React.useState(false);

  // Sorting and filtering states
  const [searchTerm, setSearchTerm] = React.useState('');
  const [sortField, setSortField] = React.useState<string>('title');
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('asc');

  // Form payload hooks
  const [newCompany, setNewCompany] = React.useState({ name: '', domain: '', industry: '', size: '' });
  const [newContact, setNewContact] = React.useState({ first_name: '', last_name: '', email: '', phone: '', job_title: '', company_id: '' });
  const [newLead, setNewLead] = React.useState({ title: '', status: 'NEW', value: '0.00', contact_id: '', company_id: '' });
  const [newActivity, setNewActivity] = React.useState({ type: 'CALL', description: '' });

  // ----------------------------------------------------
  // React Query Servers Hooks
  // ----------------------------------------------------
  const { data: companies = [], isLoading: loadingCompanies } = useQuery({
    queryKey: ['companies', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/companies/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: contacts = [], isLoading: loadingContacts } = useQuery({
    queryKey: ['contacts', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/contacts/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: leads = [], isLoading: loadingLeads } = useQuery({
    queryKey: ['leads', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/leads/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  // Selected Lead detailed meta
  const selectedLead = leads.find((l: any) => l.id === selectedLeadId);

  // Queries for activities
  const { data: activities = [], refetch: refetchActivities } = useQuery({
    queryKey: ['activities', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/activities/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const filteredLeadActivities = activities.filter((act: any) => act.lead_id === selectedLeadId);

  // ----------------------------------------------------
  // Mutations Hooks
  // ----------------------------------------------------
  const createCompanyMutation = useMutation({
    mutationFn: (data: typeof newCompany) => apiClient.post('/crm/companies/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setNewCompany({ name: '', domain: '', industry: '', size: '' });
      toast.success('Company Added', 'The company record has been successfully logged.');
    },
    onError: () => toast.error('Error', 'Failed to create company record.')
  });

  const createContactMutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/crm/contacts/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setNewContact({ first_name: '', last_name: '', email: '', phone: '', job_title: '', company_id: '' });
      toast.success('Contact Added', 'The contact card has been successfully logged.');
    },
    onError: () => toast.error('Error', 'Failed to create contact card.')
  });

  const createLeadMutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/crm/leads/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setNewLead({ title: '', status: 'NEW', value: '0.00', contact_id: '', company_id: '' });
      toast.success('Lead Logged', 'A new lead has been added to the sales pipeline.');
    },
    onError: () => toast.error('Error', 'Failed to create lead workspace.')
  });

  const createActivityMutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/crm/activities/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      setNewActivity({ type: 'CALL', description: '' });
      setShowAddActivity(false);
      toast.success('Activity Logged', 'The touchpoint has been added to the lead timeline.');
    },
    onError: () => toast.error('Error', 'Failed to log CRM activity.')
  });

  const deleteRecordMutation = useMutation({
    mutationFn: ({ type, id }: { type: string; id: string }) => apiClient.delete(`/crm/${type}/${id}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [variables.type] });
      toast.success('Record Deleted', 'The record was removed from the active tenant.');
    },
    onError: () => toast.error('Error', 'Failed to delete the selected record.')
  });

  const updateLeadStatusMutation = useMutation({
    mutationFn: (data: { id: string; status: string }) => apiClient.patch(`/crm/leads/${data.id}`, { status: data.status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success('Lead Status Updated', 'Lead status has been updated successfully.');
    },
    onError: () => toast.error('Error', 'Failed to update lead status.')
  });

  // Action handlers
  const handleAddCompany = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany.name.trim()) return;
    createCompanyMutation.mutate(newCompany);
  };

  const handleAddContact = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContact.first_name.trim() || !newContact.email.trim()) return;
    createContactMutation.mutate({
      ...newContact,
      company_id: newContact.company_id || null
    });
  };

  const handleAddLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLead.title.trim()) return;
    createLeadMutation.mutate({
      ...newLead,
      value: parseFloat(newLead.value) || 0.00,
      contact_id: newLead.contact_id || null,
      company_id: newLead.company_id || null
    });
  };

  const handleAddActivity = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActivity.description.trim() || !selectedLeadId) return;
    createActivityMutation.mutate({
      ...newActivity,
      lead_id: selectedLeadId,
      organization_id: activeOrg?.id
    });
  };

  // Pipeline metrics
  const totalPipelineValue = leads.reduce((acc: number, lead: any) => acc + (parseFloat(lead.value) || 0), 0);
  const activeLeadsCount = leads.filter((l: any) => l.status !== 'LOST' && l.status !== 'lost').length;

  // Sorting & filtering logic
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getSortedAndFilteredData = () => {
    let items = [];
    if (activeTab === 'leads') items = [...leads];
    else if (activeTab === 'contacts') items = [...contacts];
    else items = [...companies];

    // Filter
    items = items.filter((item: any) => {
      const query = searchTerm.toLowerCase();
      if (activeTab === 'leads') {
        return item.title.toLowerCase().includes(query) || (item.status && item.status.toLowerCase().includes(query));
      } else if (activeTab === 'contacts') {
        return item.first_name.toLowerCase().includes(query) || item.last_name.toLowerCase().includes(query) || item.email.toLowerCase().includes(query);
      } else {
        return item.name.toLowerCase().includes(query) || (item.industry && item.industry.toLowerCase().includes(query));
      }
    });

    // Sort
    items.sort((a: any, b: any) => {
      let valA = a[sortField] || '';
      let valB = b[sortField] || '';
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return items;
  };

  const displayedItems = getSortedAndFilteredData();
  const loading = loadingCompanies || loadingContacts || loadingLeads;

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData('text/plain', id);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, status: string) => {
    e.preventDefault();
    const leadId = e.dataTransfer.getData('text/plain');
    if (leadId) {
      updateLeadStatusMutation.mutate({ id: leadId, status });
    }
  };

  const leadsByStatus = React.useMemo(() => {
    const groups: Record<string, any[]> = { NEW: [], CONTACTED: [], QUALIFIED: [], LOST: [] };
    if (activeTab === 'leads') {
      displayedItems.forEach((lead: any) => {
        const s = String(lead.status).toUpperCase();
        if (groups[s]) {
          groups[s].push(lead);
        } else {
          groups.NEW.push(lead);
        }
      });
    }
    return groups;
  }, [activeTab, displayedItems]);

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      {/* Header and KPI display */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">CRM Module</h1>
          <p className="text-neutral-400 mt-1">Manage leads pipeline, build contacts lists, and schedule activity items.</p>
        </div>

        <div className="flex gap-4">
          <Card className="py-3 px-5 flex items-center gap-3 border-white/5 bg-neutral-900/40 backdrop-blur-md">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-semibold">Total pipeline value</p>
              <p className="text-lg font-bold text-white">${totalPipelineValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </Card>
          <Card className="py-3 px-5 flex items-center gap-3 border-white/5 bg-neutral-900/40 backdrop-blur-md">
            <Tag className="w-5 h-5 text-violet-400" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-semibold">Active Leads</p>
              <p className="text-lg font-bold text-white">{activeLeadsCount}</p>
            </div>
          </Card>
        </div>
      </header>

      {/* Main CRM interface */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
        
        {/* Left Column: Data table list view */}
        <div className="xl:col-span-2 space-y-6">
          {/* Tab Selector */}
          <div className="flex border-b border-white/5 gap-6">
            {[
              { id: 'leads', label: 'Leads Pipeline', icon: Briefcase },
              { id: 'contacts', label: 'Contacts', icon: Users },
              { id: 'companies', label: 'Companies', icon: Building2 },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id as any);
                    setSortField(tab.id === 'leads' ? 'title' : tab.id === 'contacts' ? 'first_name' : 'name');
                  }}
                  className={`flex items-center gap-2 pb-3 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
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

          {/* Filtering, searching header */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <Input
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm h-9"
                leftIcon={<Search className="w-3.5 h-3.5" />}
              />
              {activeTab === 'leads' && (
                <div className="flex rounded-lg bg-neutral-900 border border-white/5 p-1 text-xs shrink-0 h-9 items-center">
                  <button
                    type="button"
                    onClick={() => setLeadsViewMode('list')}
                    className={`px-3 py-1 rounded font-semibold transition-all cursor-pointer h-7 flex items-center ${
                      leadsViewMode === 'list' ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
                    }`}
                  >
                    List
                  </button>
                  <button
                    type="button"
                    onClick={() => setLeadsViewMode('kanban')}
                    className={`px-3 py-1 rounded font-semibold transition-all cursor-pointer h-7 flex items-center ${
                      leadsViewMode === 'kanban' ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
                    }`}
                  >
                    Kanban
                  </button>
                </div>
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSort(activeTab === 'leads' ? 'title' : activeTab === 'contacts' ? 'first_name' : 'name')}
              className="gap-2 h-9 text-xs"
            >
              <ArrowUpDown className="w-3.5 h-3.5" /> Sort Alphabetically ({sortOrder.toUpperCase()})
            </Button>
          </div>

          {/* Table display list */}
          {loading ? (
            <div className="flex flex-col gap-3 py-10">
              <div className="h-10 bg-neutral-900 animate-pulse rounded" />
              <div className="h-12 bg-neutral-900/60 animate-pulse rounded" />
              <div className="h-12 bg-neutral-900/60 animate-pulse rounded" />
            </div>
          ) : displayedItems.length === 0 ? (
            <Card className="text-center py-16 border-white/5 bg-neutral-900/10">
              <Users className="w-12 h-12 text-neutral-500 mx-auto mb-4" />
              <h3 className="text-base font-bold text-white">No CRM records found</h3>
              <p className="text-xs text-neutral-400 max-w-xs mx-auto mt-2">
                Use the creation panel on the right to start tracking CRM accounts inside this organization.
              </p>
            </Card>
          ) : (
            <div className="flex flex-col gap-3">
              {activeTab === 'leads' && leadsViewMode === 'kanban' && (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 overflow-x-auto pb-4">
                  {(['NEW', 'CONTACTED', 'QUALIFIED', 'LOST'] as const).map((status) => {
                    const statusLeads = leadsByStatus[status] || [];
                    const columnColors = {
                      NEW: 'border-neutral-800 bg-neutral-900/10',
                      CONTACTED: 'border-amber-500/20 bg-amber-500/2',
                      QUALIFIED: 'border-sky-500/20 bg-sky-500/2',
                      LOST: 'border-rose-500/20 bg-rose-500/2',
                    }[status];
                    const badgeVariants = {
                      NEW: 'neutral',
                      CONTACTED: 'amber',
                      QUALIFIED: 'sky',
                      LOST: 'rose',
                    }[status] as any;

                    return (
                      <div
                        key={status}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, status)}
                        className={`rounded-xl border p-4 flex flex-col gap-3 min-h-[350px] transition-colors ${columnColors}`}
                      >
                        {/* Column Header */}
                        <div className="flex items-center justify-between border-b border-white/5 pb-2">
                          <span className="text-xs font-bold text-white tracking-wider flex items-center gap-1.5">
                            <Badge variant={badgeVariants} dot size="sm">
                              {status}
                            </Badge>
                          </span>
                          <span className="text-[10px] text-neutral-500 font-bold bg-neutral-900 px-1.5 py-0.5 rounded">
                            {statusLeads.length}
                          </span>
                        </div>

                        {/* Leads Cards */}
                        <div className="flex flex-col gap-2.5 overflow-y-auto max-h-[480px]">
                          {statusLeads.map((lead: any) => (
                            <div
                              key={lead.id}
                              draggable
                              onDragStart={(e) => handleDragStart(e, lead.id)}
                              className="p-3 rounded-lg border border-white/5 bg-neutral-950/60 hover:border-violet-500/30 hover:bg-neutral-950 transition-all cursor-grab active:cursor-grabbing flex flex-col gap-2 group relative"
                            >
                              <div>
                                <h5 className="font-bold text-xs text-white line-clamp-1">{lead.title}</h5>
                                <p className="text-[10px] text-emerald-400 font-semibold mt-1">
                                  ${parseFloat(lead.value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </p>
                              </div>

                              <div className="flex items-center justify-between pt-1 border-t border-white/5">
                                <span className="text-[8px] text-neutral-600 font-semibold">DRAG TO MOVE</span>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <button
                                    onClick={() => setSelectedLeadId(lead.id)}
                                    className="p-1 hover:text-white text-neutral-500 transition-colors"
                                    type="button"
                                    title="View Details"
                                  >
                                    <Eye className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    onClick={() => deleteRecordMutation.mutate({ type: 'leads', id: lead.id })}
                                    className="p-1 hover:text-rose-400 text-neutral-500 transition-colors"
                                    type="button"
                                    title="Delete Lead"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}

                          {statusLeads.length === 0 && (
                            <div className="py-8 text-center text-[10px] text-neutral-600 border border-dashed border-white/5 rounded-lg">
                              Drag leads here
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {activeTab === 'leads' && leadsViewMode === 'list' && displayedItems.map((lead: any) => (
                <Card key={lead.id} className="flex justify-between items-center glass p-4 hover:border-violet-500/20 transition-all">
                  <div>
                    <h4 className="font-bold text-sm text-white flex items-center gap-2">
                      {lead.title}
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-violet-500/10 border border-violet-500/20 text-violet-300">
                        {lead.status}
                      </span>
                    </h4>
                    <p className="text-[11px] text-neutral-400 mt-1">
                      Expected pipeline value: <strong className="text-emerald-400">${parseFloat(lead.value).toFixed(2)}</strong>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setSelectedLeadId(lead.id)}
                      className="p-2 h-8 w-8 text-neutral-400 hover:text-white"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => deleteRecordMutation.mutate({ type: 'leads', id: lead.id })}
                      className="p-2 h-8 w-8 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}

              {activeTab === 'contacts' && displayedItems.map((contact: any) => (
                <Card key={contact.id} className="flex justify-between items-center glass p-4 hover:border-violet-500/20 transition-all">
                  <div>
                    <h4 className="font-bold text-sm text-white">{contact.first_name} {contact.last_name}</h4>
                    <p className="text-[11px] text-neutral-400 mt-1">
                      {contact.job_title || 'Marketing Contact'} • {contact.email} {contact.phone && `• ${contact.phone}`}
                    </p>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => deleteRecordMutation.mutate({ type: 'contacts', id: contact.id })}
                    className="p-2 h-8 w-8 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </Card>
              ))}

              {activeTab === 'companies' && displayedItems.map((comp: any) => (
                <Card key={comp.id} className="flex justify-between items-center glass p-4 hover:border-violet-500/20 transition-all">
                  <div>
                    <h4 className="font-bold text-sm text-white">{comp.name}</h4>
                    <p className="text-[11px] text-neutral-400 mt-1">
                      {comp.industry || 'Industry unspecified'} • {comp.domain || 'no domain'} {comp.size && `• ${comp.size} employees`}
                    </p>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => deleteRecordMutation.mutate({ type: 'companies', id: comp.id })}
                    className="p-2 h-8 w-8 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Dynamic registration forms */}
        <div className="space-y-6">
          <Card className="glass p-5 border-white/5">
            <h3 className="font-bold text-base text-white mb-4">
              Create New {activeTab === 'leads' ? 'Lead' : activeTab === 'contacts' ? 'Contact' : 'Company'}
            </h3>

            {activeTab === 'leads' && (
              <form onSubmit={handleAddLead} className="flex flex-col gap-3.5">
                <Input
                  label="Lead Title / Purpose"
                  placeholder="Enterprise SaaS Deal"
                  required
                  value={newLead.title}
                  onChange={(e) => setNewLead({ ...newLead, title: e.target.value })}
                />

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Contract Value ($)"
                    type="number"
                    step="0.01"
                    placeholder="12000.00"
                    value={newLead.value}
                    onChange={(e) => setNewLead({ ...newLead, value: e.target.value })}
                  />

                  <Select
                    label="Lead Status"
                    options={[
                      { label: 'New', value: 'NEW' },
                      { label: 'Contacted', value: 'CONTACTED' },
                      { label: 'Qualified', value: 'QUALIFIED' },
                      { label: 'Lost', value: 'LOST' }
                    ]}
                    value={newLead.status}
                    onChange={(e) => setNewLead({ ...newLead, status: e.target.value })}
                  />
                </div>

                <Select
                  label="Associated Customer Contact"
                  options={[
                    { label: 'None / Select contact...', value: '' },
                    ...contacts.map((c: any) => ({ label: `${c.first_name} ${c.last_name}`, value: c.id }))
                  ]}
                  value={newLead.contact_id}
                  onChange={(e) => setNewLead({ ...newLead, contact_id: e.target.value })}
                />

                <Select
                  label="Associated Company"
                  options={[
                    { label: 'None / Select company...', value: '' },
                    ...companies.map((c: any) => ({ label: c.name, value: c.id }))
                  ]}
                  value={newLead.company_id}
                  onChange={(e) => setNewLead({ ...newLead, company_id: e.target.value })}
                />

                <Button type="submit" variant="violet" isLoading={createLeadMutation.isPending} className="w-full mt-2">
                  Create Lead Record
                </Button>
              </form>
            )}

            {activeTab === 'contacts' && (
              <form onSubmit={handleAddContact} className="flex flex-col gap-3.5">
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="First Name"
                    placeholder="Jane"
                    required
                    value={newContact.first_name}
                    onChange={(e) => setNewContact({ ...newContact, first_name: e.target.value })}
                  />
                  <Input
                    label="Last Name"
                    placeholder="Doe"
                    required
                    value={newContact.last_name}
                    onChange={(e) => setNewContact({ ...newContact, last_name: e.target.value })}
                  />
                </div>

                <Input
                  label="Email Address"
                  type="email"
                  placeholder="jane.doe@acme.com"
                  required
                  value={newContact.email}
                  onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                />

                <Input
                  label="Phone Number"
                  placeholder="+1 (555) 019-2834"
                  value={newContact.phone}
                  onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                />

                <Input
                  label="Job Title"
                  placeholder="VP of Growth"
                  value={newContact.job_title}
                  onChange={(e) => setNewContact({ ...newContact, job_title: e.target.value })}
                />

                <Select
                  label="Link to Company"
                  options={[
                    { label: 'No Company Link', value: '' },
                    ...companies.map((c: any) => ({ label: c.name, value: c.id }))
                  ]}
                  value={newContact.company_id}
                  onChange={(e) => setNewContact({ ...newContact, company_id: e.target.value })}
                />

                <Button type="submit" variant="violet" isLoading={createContactMutation.isPending} className="w-full mt-2">
                  Create Contact card
                </Button>
              </form>
            )}

            {activeTab === 'companies' && (
              <form onSubmit={handleAddCompany} className="flex flex-col gap-3.5">
                <Input
                  label="Company Name"
                  placeholder="Acme Corp"
                  required
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                />

                <Input
                  label="Web Domain"
                  placeholder="acme.com"
                  value={newCompany.domain}
                  onChange={(e) => setNewCompany({ ...newCompany, domain: e.target.value })}
                />

                <Input
                  label="Industry Vertical"
                  placeholder="Enterprise Software"
                  value={newCompany.industry}
                  onChange={(e) => setNewCompany({ ...newCompany, industry: e.target.value })}
                />

                <Select
                  label="Employee Size Range"
                  options={[
                    { label: 'Select range...', value: '' },
                    { label: '1 - 10 employees', value: '1-10' },
                    { label: '11 - 50 employees', value: '11-50' },
                    { label: '51 - 250 employees', value: '51-250' },
                    { label: '251+ employees', value: '251+' }
                  ]}
                  value={newCompany.size}
                  onChange={(e) => setNewCompany({ ...newCompany, size: e.target.value })}
                />

                <Button type="submit" variant="violet" isLoading={createCompanyMutation.isPending} className="w-full mt-2">
                  Create Company record
                </Button>
              </form>
            )}
          </Card>
        </div>
      </div>

      {/* -------------------------------------------------- */}
      {/* LEAD DETAILS TIMELINE DIALOG */}
      {/* -------------------------------------------------- */}
      <Dialog
        isOpen={!!selectedLeadId}
        onClose={() => {
          setSelectedLeadId(null);
          setShowAddActivity(false);
        }}
        title={selectedLead?.title || 'Lead Details'}
        description={`Sales status tracking and activities log.`}
        className="max-w-2xl bg-neutral-950"
      >
        {selectedLead && (
          <div className="flex flex-col gap-6 mt-2">
            {/* Metadata Summary */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl border border-white/5 bg-neutral-900/40">
              <div className="flex flex-col">
                <span className="text-[10px] text-neutral-500 font-semibold uppercase">Contract value</span>
                <span className="text-lg font-bold text-emerald-400">${parseFloat(selectedLead.value).toFixed(2)}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] text-neutral-500 font-semibold uppercase">Lifecycle Stage</span>
                <span className="text-sm font-bold text-violet-400">{selectedLead.status}</span>
              </div>
            </div>

            {/* Timeline Activities Feed */}
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-violet-400" /> Touchpoint History ({filteredLeadActivities.length})
                </h4>
                
                {!showAddActivity && (
                  <Button variant="outline" size="sm" onClick={() => setShowAddActivity(true)} className="h-7 text-xs">
                    Log Activity
                  </Button>
                )}
              </div>

              {/* Log Activity Inline form */}
              {showAddActivity && (
                <form onSubmit={handleAddActivity} className="p-4 rounded-lg border border-white/10 bg-neutral-900 flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-neutral-300">New Touchpoint Detail</span>
                    <button 
                      type="button"
                      onClick={() => setShowAddActivity(false)}
                      className="text-xs text-neutral-400 hover:text-white"
                    >
                      Cancel
                    </button>
                  </div>
                  <Select
                    options={[
                      { label: 'Log Call', value: 'CALL' },
                      { label: 'Log Email', value: 'EMAIL' },
                      { label: 'Log Meeting', value: 'MEETING' },
                      { label: 'Note log', value: 'NOTE' }
                    ]}
                    value={newActivity.type}
                    onChange={(e) => setNewActivity({ ...newActivity, type: e.target.value })}
                  />
                  <Input
                    placeholder="Discussed pricing plan options..."
                    required
                    value={newActivity.description}
                    onChange={(e) => setNewActivity({ ...newActivity, description: e.target.value })}
                  />
                  <Button type="submit" variant="violet" size="sm" isLoading={createActivityMutation.isPending} className="self-end h-8">
                    Log Activity
                  </Button>
                </form>
              )}

              {/* Activities feed timeline */}
              {filteredLeadActivities.length === 0 ? (
                <p className="text-xs text-neutral-500 py-6 text-center">No interactions logged on this lead yet.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {filteredLeadActivities.map((act: any) => (
                    <div key={act.id} className="p-3 rounded bg-neutral-900 border border-white/5 text-left">
                      <div className="flex justify-between items-center text-[10px] text-neutral-500 mb-1">
                        <span className="font-bold text-violet-400 uppercase">{act.type}</span>
                        <span>{new Date(act.created_at || '').toLocaleDateString()}</span>
                      </div>
                      <p className="text-xs text-neutral-200">{act.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
