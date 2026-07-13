'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import {
  LogOut,
  Building2,
  Plus,
  User,
  Shield,
  Loader2,
  LayoutDashboard,
  Check
} from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const { token, user, activeOrgId, setActiveOrgId, logout } = useAuthStore();
  const [organizations, setOrganizations] = React.useState<any[]>([]);
  const [loadingOrgs, setLoadingOrgs] = React.useState(true);
  const [creatingOrg, setCreatingOrg] = React.useState(false);
  const [newOrgName, setNewOrgName] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);

  // Authenticate check
  React.useEffect(() => {
    if (!token) {
      router.push('/auth/login');
    }
  }, [token, router]);

  // Fetch organizations
  const fetchOrgs = React.useCallback(async () => {
    if (!token) return;
    setLoadingOrgs(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/organizations/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      if (res.ok) {
        setOrganizations(data);
        if (data.length > 0 && !activeOrgId) {
          setActiveOrgId(data[0].id);
        }
      }
    } catch {
      // Handle silently or show toast
    } finally {
      setLoadingOrgs(false);
    }
  }, [token, activeOrgId, setActiveOrgId]);

  React.useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setCreatingOrg(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/organizations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newOrgName }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create organization');

      setNewOrgName('');
      await fetchOrgs();
      setActiveOrgId(data.id);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setCreatingOrg(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  const activeOrg = organizations.find((o) => o.id === activeOrgId);

  if (!token || !user) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col lg:flex-row">
      {/* Sidebar */}
      <aside className="w-full lg:w-64 border-b lg:border-b-0 lg:border-r border-white/10 bg-zinc-950 p-6 flex flex-col justify-between">
        <div>
          {/* Logo / Header */}
          <div className="flex items-center gap-2 mb-8">
            <LayoutDashboard className="w-6 h-6 text-violet-500" />
            <span className="font-bold tracking-wider text-sm uppercase">EAIMOS Platform</span>
          </div>

          {/* Org Selector */}
          <div className="mb-8">
            <label className="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Active Organization</label>
            {loadingOrgs ? (
              <div className="flex items-center gap-2 text-sm text-neutral-400">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading Orgs...
              </div>
            ) : (
              <div className="space-y-1">
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => setActiveOrgId(org.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-sm transition-colors cursor-pointer ${
                      activeOrgId === org.id
                        ? 'bg-violet-600/20 text-violet-300 border border-violet-500/30'
                        : 'hover:bg-white/5 text-neutral-400 border border-transparent'
                    }`}
                  >
                    <span className="truncate">{org.name}</span>
                    {activeOrgId === org.id && <Check className="w-4 h-4 text-violet-400 shrink-0 ml-2" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Create Org Form */}
          <form onSubmit={handleCreateOrg} className="border-t border-white/5 pt-4">
            <label className="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">New Organization</label>
            {error && <p className="text-xs text-rose-400 mb-2">{error}</p>}
            <div className="flex gap-2">
              <input
                type="text"
                value={newOrgName}
                onChange={(e) => setNewOrgName(e.target.value)}
                placeholder="Name..."
                className="flex-1 min-w-0 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={creatingOrg}
                className="p-2 rounded bg-violet-600 hover:bg-violet-700 text-white transition-colors cursor-pointer disabled:opacity-50 shrink-0"
              >
                {creatingOrg ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              </button>
            </div>
          </form>
        </div>

        {/* Footer profile info & logout */}
        <div className="border-t border-white/5 pt-4 mt-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-full bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 font-semibold text-sm">
              {user.full_name[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">{user.full_name}</p>
              <p className="text-xs text-neutral-400 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-neutral-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors cursor-pointer text-left font-medium"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Workspace Panel */}
      <main className="flex-1 p-8 lg:p-12 relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[160px] pointer-events-none" />

        <div className="max-w-4xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold tracking-tight">Organization Workspace</h1>
            <p className="text-neutral-400 mt-1">Manage marketing resources and AI systems</p>
          </div>

          {/* Active Org Context */}
          {activeOrg ? (
            <div className="space-y-6">
              <Card className="glass flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Building2 className="w-6 h-6 text-violet-400" />
                    <h2 className="text-xl font-bold">{activeOrg.name}</h2>
                  </div>
                  <p className="text-sm text-neutral-400">Slug: <span className="font-mono text-violet-300">{activeOrg.slug}</span></p>
                  <p className="text-xs text-neutral-500 mt-1">ID: {activeOrg.id}</p>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-300 text-xs font-semibold">
                  <Shield className="w-3.5 h-3.5" /> Workspace Owner
                </div>
              </Card>

              {/* Grid content placeholders */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="flex flex-col gap-3">
                  <h3 className="font-bold text-lg">AI Assistants</h3>
                  <p className="text-sm text-neutral-400">Launch marketing prompts, copy generation models and dynamic AI Chat agents.</p>
                  <button
                    onClick={() => router.push('/dashboard/ai')}
                    className="self-start mt-2 px-4 py-2 rounded-lg bg-neutral-900 border border-white/10 hover:border-violet-500/30 text-sm font-semibold transition-all cursor-pointer"
                  >
                    Configure AI Gateway
                  </button>
                </Card>

                <Card className="flex flex-col gap-3">
                  <h3 className="font-bold text-lg">CRM Pipeline</h3>
                  <p className="text-sm text-neutral-400">Integrate contacts, schedule email triggers, and qualify marketing leads.</p>
                  <button
                    onClick={() => router.push('/dashboard/crm')}
                    className="self-start mt-2 px-4 py-2 rounded-lg bg-neutral-900 border border-white/10 hover:border-violet-500/30 text-sm font-semibold transition-all cursor-pointer"
                  >
                    Open CRM Contacts
                  </button>
                </Card>

                <Card className="flex flex-col gap-3">
                  <h3 className="font-bold text-lg">AI Content Generator</h3>
                  <p className="text-sm text-neutral-400">Generate creative copywriting variants, emails, and run A/B ratings tests.</p>
                  <button
                    onClick={() => router.push('/dashboard/generator')}
                    className="self-start mt-2 px-4 py-2 rounded-lg bg-neutral-900 border border-white/10 hover:border-violet-500/30 text-sm font-semibold transition-all cursor-pointer"
                  >
                    Open Content Generator
                  </button>
                </Card>
              </div>
            </div>
          ) : (
            <Card className="glass text-center py-12">
              <Building2 className="w-12 h-12 text-neutral-500 mx-auto mb-4" />
              <h2 className="text-lg font-bold">No active organization</h2>
              <p className="text-neutral-400 text-sm max-w-sm mx-auto mt-2">
                Create a new organization in the sidebar to configure your workspace.
              </p>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
