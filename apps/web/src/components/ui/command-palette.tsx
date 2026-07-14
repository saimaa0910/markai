'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Search, FileText, Users, Building, Terminal, Megaphone, LogOut, ArrowRight, Star, Brain, MessageSquare, FolderOpen } from 'lucide-react';
import { useUIStore } from '@/store/ui';
import { useAuthStore, Organization, UserProfile } from '@/store/auth';
import { Dialog } from '@/components/ui/dialog';
import { apiClient } from '@/services/api-client';

interface SearchItem {
  id: string;
  name: string;
  category: 'Pages' | 'Leads' | 'Contacts' | 'Companies' | 'Prompts' | 'Conversations' | 'Knowledge' | 'Files' | 'Quick Actions';
  subtitle?: string;
  action: () => void;
}

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const { activeOrg, logout } = useAuthStore();
  const [query, setQuery] = React.useState('');
  const [selectedIndex, setSelectedIndex] = React.useState(0);

  // Queries for dynamic data
  const { data: leads = [] } = useQuery<any[]>({
    queryKey: ['leads', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/leads/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: contacts = [] } = useQuery<any[]>({
    queryKey: ['contacts', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/contacts/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: companies = [] } = useQuery<any[]>({
    queryKey: ['companies', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/crm/companies/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: prompts = [] } = useQuery<any[]>({
    queryKey: ['prompts', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: conversations = [] } = useQuery<any[]>({
    queryKey: ['conversations', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/conversations/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: documents = [] } = useQuery<any[]>({
    queryKey: ['kb-documents', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/knowledge/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const { data: files = [] } = useQuery<any[]>({
    queryKey: ['files', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/files/');
      return res.data || [];
    },
    enabled: commandPaletteOpen && !!activeOrg,
  });

  const items = React.useMemo(() => {
    const searchItems: SearchItem[] = [];

    // Static Navigation Pages
    const pages = [
      { name: 'Workspace Hub / Dashboard', path: '/dashboard' },
      { name: 'CRM Pipeline (Leads, Contacts)', path: '/dashboard/crm' },
      { name: 'Campaigns Center', path: '/dashboard/campaigns' },
      { name: 'AI Chat playground', path: '/dashboard/ai/chat' },
      { name: 'AI Providers Monitor', path: '/dashboard/ai/providers' },
      { name: 'AI Model Registry', path: '/dashboard/ai/models' },
      { name: 'AI Playground Sandbox', path: '/dashboard/ai/playground' },
      { name: 'AI Model Comparison Lab', path: '/dashboard/ai/compare' },
      { name: 'AI Provider Health Center', path: '/dashboard/ai/health' },
      { name: 'AI Platform Admin Console', path: '/dashboard/ai/admin' },
      { name: 'AI Token Usage & Costs', path: '/dashboard/ai/usage' },
      { name: 'AI Latency Analytics', path: '/dashboard/ai/analytics' },
      { name: 'AI Gateway Router', path: '/dashboard/ai/router' },
      { name: 'AI Provider Settings', path: '/dashboard/ai/settings' },
      { name: 'Knowledge Base Ingestion', path: '/dashboard/knowledge' },
      { name: 'Prompt Library Templates', path: '/dashboard/prompts' },
      { name: 'AI Conversation History', path: '/dashboard/conversations' },
      { name: 'Executive Analytics Hub', path: '/dashboard/analytics' },
      { name: 'Integration Connections', path: '/dashboard/integrations' },
      { name: 'Team Member Management', path: '/dashboard/users' },
      { name: 'File Storage Assets', path: '/dashboard/files' },
      { name: 'Settings', path: '/dashboard/settings' },
    ];

    pages.forEach((p) => {
      searchItems.push({
        id: `page-${p.path}`,
        name: p.name,
        category: 'Pages',
        subtitle: 'Navigation Link',
        action: () => {
          router.push(p.path);
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Leads
    leads.forEach((l) => {
      searchItems.push({
        id: `lead-${l.id}`,
        name: l.title,
        category: 'Leads',
        subtitle: `Value: $${parseFloat(l.value || '0').toFixed(2)} | Status: ${l.status}`,
        action: () => {
          router.push('/dashboard/crm');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Contacts
    contacts.forEach((c) => {
      searchItems.push({
        id: `contact-${c.id}`,
        name: `${c.first_name} ${c.last_name}`,
        category: 'Contacts',
        subtitle: `${c.job_title || 'Contact'} | ${c.email}`,
        action: () => {
          router.push('/dashboard/crm');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Companies
    companies.forEach((co) => {
      searchItems.push({
        id: `company-${co.id}`,
        name: co.name,
        category: 'Companies',
        subtitle: `${co.industry || 'Enterprise'} | ${co.domain || 'No website'}`,
        action: () => {
          router.push('/dashboard/crm');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Prompts
    prompts.forEach((pr) => {
      searchItems.push({
        id: `prompt-${pr.id}`,
        name: pr.name,
        category: 'Prompts',
        subtitle: `Prompt template version: v${pr.version}`,
        action: () => {
          router.push('/dashboard/prompts');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Conversations
    conversations.forEach((c) => {
      searchItems.push({
        id: `conv-${c.id}`,
        name: c.title,
        category: 'Conversations',
        subtitle: `AI Conversation session`,
        action: () => {
          router.push('/dashboard/conversations');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Documents
    documents.forEach((d) => {
      searchItems.push({
        id: `doc-${d.id}`,
        name: d.name,
        category: 'Knowledge',
        subtitle: `Vectorized document | status: ${d.status}`,
        action: () => {
          router.push('/dashboard/knowledge');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Dynamic Files
    files.forEach((f) => {
      searchItems.push({
        id: `file-${f.id}`,
        name: f.filename,
        category: 'Files',
        subtitle: `Stored asset | size: ${(f.file_size / 1024).toFixed(1)} KB`,
        action: () => {
          router.push('/dashboard/files');
          setCommandPaletteOpen(false);
        },
      });
    });

    // Quick Actions
    const quickActions = [
      {
        name: 'Create Campaign',
        icon: Megaphone,
        action: () => {
          router.push('/dashboard/campaigns');
          setCommandPaletteOpen(false);
        },
      },
      {
        name: 'Log Out Session',
        icon: LogOut,
        action: () => {
          logout();
          setCommandPaletteOpen(false);
        },
      },
    ];

    quickActions.forEach((qa, idx) => {
      searchItems.push({
        id: `qa-${idx}`,
        name: qa.name,
        category: 'Quick Actions',
        subtitle: 'System command action',
        action: qa.action,
      });
    });

    return searchItems;
  }, [leads, contacts, companies, prompts, conversations, documents, files, router, logout, setCommandPaletteOpen]);

  const filteredItems = React.useMemo(() => {
    if (!query) return items;
    const cleanQuery = query.toLowerCase();
    return items.filter(
      (item) =>
        item.name.toLowerCase().includes(cleanQuery) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(cleanQuery)) ||
        item.category.toLowerCase().includes(cleanQuery)
    );
  }, [items, query]);

  // Reset selected item index when query changes
  React.useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Handle Keyboard Navigation for Accessibility
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!commandPaletteOpen || filteredItems.length === 0) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filteredItems.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % filteredItems.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        filteredItems[selectedIndex]?.action();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, filteredItems, selectedIndex]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Pages':
        return <ArrowRight className="w-4 h-4 text-violet-400" />;
      case 'Leads':
        return <Star className="w-4 h-4 text-amber-400" />;
      case 'Contacts':
        return <Users className="w-4 h-4 text-emerald-400" />;
      case 'Companies':
        return <Building className="w-4 h-4 text-sky-400" />;
      case 'Prompts':
        return <Terminal className="w-4 h-4 text-indigo-400" />;
      case 'Conversations':
        return <MessageSquare className="w-4 h-4 text-violet-400" />;
      case 'Knowledge':
        return <Brain className="w-4 h-4 text-pink-400" />;
      case 'Files':
        return <FolderOpen className="w-4 h-4 text-teal-400" />;
      default:
        return <FileText className="w-4 h-4 text-neutral-400" />;
    }
  };

  return (
    <Dialog
      isOpen={commandPaletteOpen}
      onClose={() => setCommandPaletteOpen(false)}
      title="Search & Quick Actions"
      description="Search leads, contacts, campaigns, prompts, or trigger system actions."
      className="max-w-lg p-0 bg-neutral-950 border-white/10"
    >
      <div className="p-4 border-b border-white/5 flex items-center gap-3">
        <Search className="w-5 h-5 text-neutral-500" />
        <input
          type="text"
          placeholder="Search leads, campaigns, prompts, settings..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-transparent border-0 outline-none text-white text-sm placeholder-neutral-500 focus:ring-0 focus:outline-none"
          autoFocus
        />
      </div>

      <div className="p-2 max-h-[50vh] overflow-y-auto flex flex-col gap-0.5">
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center text-xs text-neutral-500">
            No matching actions or resources found.
          </div>
        ) : (
          filteredItems.map((item, index) => {
            const isSelected = index === selectedIndex;
            return (
              <button
                key={item.id}
                onClick={item.action}
                className={`w-full px-3 py-2 rounded-lg text-sm transition-all text-left flex items-center gap-3 cursor-pointer ${
                  isSelected ? 'bg-violet-600/10 text-violet-400 border border-violet-500/20' : 'text-neutral-300 hover:text-white hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className="shrink-0">{getCategoryIcon(item.category)}</div>
                <div className="flex flex-col truncate">
                  <span className="font-medium truncate">{item.name}</span>
                  {item.subtitle && (
                    <span className="text-[10px] text-neutral-500 truncate">{item.subtitle}</span>
                  )}
                </div>
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  <span className="text-[9px] bg-neutral-900 border border-white/5 text-neutral-500 px-1.5 py-0.5 rounded uppercase font-semibold">
                    {item.category}
                  </span>
                  {isSelected && <span className="text-[10px] text-violet-400 font-bold">⏎</span>}
                </div>
              </button>
            );
          })
        )}
      </div>
    </Dialog>
  );
}
