'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { useUIStore } from '@/store/ui';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import { 
  LayoutDashboard, Users, Megaphone, Bot, Settings, Search, 
  Bell, ChevronLeft, ChevronRight, Menu, LogOut, Building, Check, X,
  Brain, BookOpen, MessageSquare, BarChart2, Plug, FolderOpen,
  Cpu, Database, TrendingUp, Router, SlidersHorizontal, ChevronDown, Terminal, Columns, Activity, Shield, UploadCloud, Sparkles, FileText, Code, History, Library, Server
} from 'lucide-react';
import { cn } from '@eaimos/shared';
import { Button } from '@/components/ui/button';
import { CommandPalette } from '@/components/ui/command-palette';
import { BrandLogo } from '@/components/ui/brand-logo';
import { ThemeSwitcher } from '@/components/ui/theme-switcher';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, user, activeOrg, organizations, logout, setActiveOrg } = useAuthStore();
  const { sidebarOpen, toggleSidebar, commandPaletteOpen, setCommandPaletteOpen, notificationsOpen, setNotificationsOpen } = useUIStore();
  const [showOrgDropdown, setShowOrgDropdown] = React.useState(false);
  const [aiExpanded, setAiExpanded] = React.useState(pathname.startsWith('/dashboard/ai'));
  const [knowledgeExpanded, setKnowledgeExpanded] = React.useState(pathname.startsWith('/dashboard/knowledge'));
  const [promptsExpanded, setPromptsExpanded] = React.useState(pathname.startsWith('/dashboard/prompts'));
  const [agentsExpanded, setAgentsExpanded] = React.useState(pathname.startsWith('/dashboard/agents'));
  const [workflowsExpanded, setWorkflowsExpanded] = React.useState(pathname.startsWith('/dashboard/workflows'));
  const [showProfileMenu, setShowProfileMenu] = React.useState(false);
  const [notifications, setNotifications] = React.useState([
    { id: '1', category: 'AI Completed', categoryColor: 'text-violet-400', time: '2m ago', title: 'Variant A Creative generated', description: 'AI variant copy draft for "Summer Promo Ad" is complete.' },
    { id: '2', category: 'CRM Update', categoryColor: 'text-emerald-400', time: '1h ago', title: 'New high-value lead logged', description: 'Lead "Sarah Jenkins (Acme Corp)" value: $15,400.' }
  ]);

  // Protect client route
  React.useEffect(() => {
    if (!accessToken) {
      router.push('/auth/login');
    }
  }, [accessToken, router]);

  // Command palette hotkey handler (Cmd+K)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  if (!accessToken) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500" />
      </div>
    );
  }

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, exact: true },
    { name: 'CRM Module', href: '/dashboard/crm', icon: Users },
    { name: 'Campaigns', href: '/dashboard/campaigns', icon: Megaphone },
    { name: 'Conversations', href: '/dashboard/conversations', icon: MessageSquare },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart2 },
    { name: 'Integrations', href: '/dashboard/integrations', icon: Plug },
    { name: 'Users & Teams', href: '/dashboard/users', icon: Users },
    { name: 'Files', href: '/dashboard/files', icon: FolderOpen },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ];

  const aiSubItems = [
    { name: 'Providers', href: '/dashboard/ai/providers', icon: Cpu },
    { name: 'Models', href: '/dashboard/ai/models', icon: Database },
    { name: 'Playground', href: '/dashboard/ai/playground', icon: Terminal },
    { name: 'Compare Lab', href: '/dashboard/ai/compare', icon: Columns },
    { name: 'Health Center', href: '/dashboard/ai/health', icon: Activity },
    { name: 'Admin Console', href: '/dashboard/ai/admin', icon: Shield },
    { name: 'Usage', href: '/dashboard/ai/usage', icon: TrendingUp },
    { name: 'Analytics', href: '/dashboard/ai/analytics', icon: BarChart2 },
    { name: 'Router', href: '/dashboard/ai/router', icon: Router },
    { name: 'Security Center', href: '/dashboard/ai/security', icon: Shield },
    { name: 'Infrastructure', href: '/dashboard/ai/infrastructure', icon: Server },
    { name: 'Observability', href: '/dashboard/ai/observability', icon: Activity },
    { name: 'Settings', href: '/dashboard/ai/settings', icon: SlidersHorizontal },
  ];

  const knowledgeSubItems = [
    { name: 'Dashboard', href: '/dashboard/knowledge', icon: LayoutDashboard },
    { name: 'Documents', href: '/dashboard/knowledge/documents', icon: FileText },
    { name: 'Collections', href: '/dashboard/knowledge/collections', icon: FolderOpen },
    { name: 'Semantic Search', href: '/dashboard/knowledge/search', icon: Search },
    { name: 'Upload Center', href: '/dashboard/knowledge/upload', icon: UploadCloud },
    { name: 'Vector Embeddings', href: '/dashboard/knowledge/embeddings', icon: Sparkles },
    { name: 'Analytics', href: '/dashboard/knowledge/analytics', icon: BarChart2 },
    { name: 'Settings', href: '/dashboard/knowledge/settings', icon: Settings },
  ];

  const promptSubItems = [
    { name: 'Dashboard', href: '/dashboard/prompts', icon: LayoutDashboard },
    { name: 'Library', href: '/dashboard/prompts/library', icon: BookOpen },
    { name: 'Workspace Editor', href: '/dashboard/prompts/editor', icon: Code },
    { name: 'Testing Lab', href: '/dashboard/prompts/testing', icon: SlidersHorizontal },
    { name: 'Version Control', href: '/dashboard/prompts/history', icon: History },
    { name: 'Template Gallery', href: '/dashboard/prompts/templates', icon: Library },
    { name: 'Performance Stats', href: '/dashboard/prompts/analytics', icon: BarChart2 },
  ];

  const agentsSubItems = [
    { name: 'Dashboard', href: '/dashboard/agents', icon: LayoutDashboard },
    { name: 'Marketplace', href: '/dashboard/agents/marketplace', icon: Library },
    { name: 'Create Agent', href: '/dashboard/agents/create', icon: Bot },
    { name: 'Playground', href: '/dashboard/agents/playground', icon: Terminal },
    { name: 'Templates', href: '/dashboard/agents/templates', icon: Library },
    { name: 'Runs Timeline', href: '/dashboard/agents/runs', icon: History },
    { name: 'Execution Logs', href: '/dashboard/agents/logs', icon: Activity },
    { name: 'Analytics', href: '/dashboard/agents/analytics', icon: BarChart2 },
    { name: 'Settings', href: '/dashboard/agents/settings', icon: Settings },
  ];

  const workflowsSubItems = [
    { name: 'Dashboard', href: '/dashboard/workflows', icon: LayoutDashboard },
    { name: 'Visual Builder', href: '/dashboard/workflows/create', icon: Sparkles },
    { name: 'Templates', href: '/dashboard/workflows/templates', icon: Library },
    { name: 'Executions History', href: '/dashboard/workflows/history', icon: History },
    { name: 'Workflow Logs', href: '/dashboard/workflows/logs', icon: Activity },
    { name: 'Settings', href: '/dashboard/workflows/settings', icon: Settings },
  ];
  return (
    <div className="min-h-screen bg-black flex text-white font-sans">
      {/* Sidebar Navigation */}
      <aside 
        className={cn(
          "bg-neutral-950 border-r border-white/5 transition-all duration-300 flex flex-col justify-between relative z-30 shrink-0",
          sidebarOpen ? "w-64" : "w-16"
        )}
      >
        {/* Toggle Button */}
        <button 
          onClick={toggleSidebar}
          className="absolute -right-3 top-6 w-6 h-6 rounded-full border border-white/10 bg-neutral-900 flex items-center justify-center text-neutral-400 hover:text-white hover:border-violet-500 transition-all cursor-pointer"
        >
          {sidebarOpen ? <ChevronLeft className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>

        <div>
          {/* Header/Brand info */}
          <div className={cn("flex items-center gap-2 h-16 border-b border-white/5", sidebarOpen ? "px-4" : "justify-center px-0")}>
            <BrandLogo
              size="sm"
              showText={sidebarOpen}
              onClick={() => router.push('/dashboard')}
            />
          </div>

          {/* Org Switcher */}
          <div className="p-3 border-b border-white/5 relative">
            <button
              onClick={() => sidebarOpen && setShowOrgDropdown(!showOrgDropdown)}
              className={cn(
                "w-full flex items-center justify-between rounded-lg bg-neutral-900 border border-white/5 text-sm font-medium hover:bg-neutral-800 hover:border-white/10 transition-all cursor-pointer",
                sidebarOpen ? "px-3 py-2" : "p-2 justify-center"
              )}
            >
              <div className="flex items-center gap-2">
                <Building className="w-4 h-4 text-violet-400 shrink-0" />
                {sidebarOpen && (
                  <span className="truncate max-w-[130px]">
                    {activeOrg?.name || 'Create Org'}
                  </span>
                )}
              </div>
              {sidebarOpen && <span className="text-[10px] text-neutral-500">▼</span>}
            </button>

            {/* Org Switcher Dropdown */}
            {showOrgDropdown && sidebarOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowOrgDropdown(false)} />
                <div className="absolute left-3 right-3 mt-1.5 p-1 bg-neutral-900 border border-white/10 rounded-lg shadow-xl z-20 flex flex-col gap-0.5">
                  <span className="text-[10px] text-neutral-500 font-semibold uppercase px-2 py-1 select-none">Switch Tenant</span>
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => {
                        setActiveOrg(org);
                        setShowOrgDropdown(false);
                      }}
                      className="w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left"
                    >
                      <span className="truncate">{org.name}</span>
                      {activeOrg?.id === org.id && <Check className="w-3.5 h-3.5 text-violet-400" />}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Main Navigation Links */}
          <nav className="p-3 flex flex-col gap-0.5 overflow-y-auto">
            {/* AI Platform Group */}
            <div className="flex flex-col gap-0.5">
              <button
                onClick={() => {
                  if (!sidebarOpen) router.push('/dashboard/ai/providers');
                  else setAiExpanded(!aiExpanded);
                }}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                  pathname.startsWith('/dashboard/ai')
                    ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Bot className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/ai') ? "text-violet-400" : "text-neutral-400")} />
                {sidebarOpen && (
                  <>
                    <span className="flex-1">AI Platform</span>
                    <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", aiExpanded && "rotate-180")} />
                  </>
                )}
              </button>

              {/* AI Sub-items */}
              {sidebarOpen && aiExpanded && (
                <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                  {aiSubItems.map((sub) => {
                    const SubIcon = sub.icon;
                    const isActive = pathname === sub.href;
                    return (
                      <button
                        key={sub.href}
                        onClick={() => router.push(sub.href)}
                        className={cn(
                          "flex items-center gap-2.5 py-1.5 px-2 rounded-md text-xs transition-all text-left cursor-pointer w-full",
                          isActive
                            ? "bg-violet-600/10 text-violet-400 font-semibold"
                            : "text-neutral-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <SubIcon className="w-3.5 h-3.5 shrink-0" />
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Agents Platform Group */}
            <div className="flex flex-col gap-0.5 mt-1">
              <button
                onClick={() => {
                  if (!sidebarOpen) router.push('/dashboard/agents');
                  else setAgentsExpanded(!agentsExpanded);
                }}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                  pathname.startsWith('/dashboard/agents')
                    ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Bot className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/agents') ? "text-violet-400" : "text-neutral-400")} />
                {sidebarOpen && (
                  <>
                    <span className="flex-1">Agents Platform</span>
                    <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", agentsExpanded && "rotate-180")} />
                  </>
                )}
              </button>

              {/* Agents Sub-items */}
              {sidebarOpen && agentsExpanded && (
                <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                  {agentsSubItems.map((sub) => {
                    const SubIcon = sub.icon;
                    const isActive = pathname === sub.href;
                    return (
                      <button
                        key={sub.href}
                        onClick={() => router.push(sub.href)}
                        className={cn(
                          "flex items-center gap-2.5 py-1.5 px-2 rounded-md text-xs transition-all text-left cursor-pointer w-full",
                          isActive
                            ? "bg-violet-600/10 text-violet-400 font-semibold"
                            : "text-neutral-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <SubIcon className="w-3.5 h-3.5 shrink-0" />
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Workflow Studio Group */}
            <div className="flex flex-col gap-0.5 mt-1">
              <button
                onClick={() => {
                  if (!sidebarOpen) router.push('/dashboard/workflows');
                  else setWorkflowsExpanded(!workflowsExpanded);
                }}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                  pathname.startsWith('/dashboard/workflows')
                    ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Activity className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/workflows') ? "text-violet-400" : "text-neutral-400")} />
                {sidebarOpen && (
                  <>
                    <span className="flex-1">Workflow Studio</span>
                    <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", workflowsExpanded && "rotate-180")} />
                  </>
                )}
              </button>

              {/* Workflows Sub-items */}
              {sidebarOpen && workflowsExpanded && (
                <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                  {workflowsSubItems.map((sub) => {
                    const SubIcon = sub.icon;
                    const isActive = pathname === sub.href;
                    return (
                      <button
                        key={sub.href}
                        onClick={() => router.push(sub.href)}
                        className={cn(
                          "flex items-center gap-2.5 py-1.5 px-2 rounded-md text-xs transition-all text-left cursor-pointer w-full",
                          isActive
                            ? "bg-violet-600/10 text-violet-400 font-semibold"
                            : "text-neutral-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <SubIcon className="w-3.5 h-3.5 shrink-0" />
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Knowledge Platform Group */}
            <div className="flex flex-col gap-0.5 mt-1">
              <button
                onClick={() => {
                  if (!sidebarOpen) router.push('/dashboard/knowledge');
                  else setKnowledgeExpanded(!knowledgeExpanded);
                }}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                  pathname.startsWith('/dashboard/knowledge')
                    ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Brain className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/knowledge') ? "text-violet-400" : "text-neutral-400")} />
                {sidebarOpen && (
                  <>
                    <span className="flex-1">Knowledge Platform</span>
                    <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", knowledgeExpanded && "rotate-180")} />
                  </>
                )}
              </button>

              {/* Knowledge Sub-items */}
              {sidebarOpen && knowledgeExpanded && (
                <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                  {knowledgeSubItems.map((sub) => {
                    const SubIcon = sub.icon;
                    const isActive = pathname === sub.href;
                    return (
                      <button
                        key={sub.href}
                        onClick={() => router.push(sub.href)}
                        className={cn(
                          "flex items-center gap-2.5 py-1.5 px-2 rounded-md text-xs transition-all text-left cursor-pointer w-full",
                          isActive
                            ? "bg-violet-600/10 text-violet-400 font-semibold"
                            : "text-neutral-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <SubIcon className="w-3.5 h-3.5 shrink-0" />
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Prompt Platform Group */}
            <div className="flex flex-col gap-0.5 mt-1">
              <button
                onClick={() => {
                  if (!sidebarOpen) router.push('/dashboard/prompts');
                  else setPromptsExpanded(!promptsExpanded);
                }}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                  pathname.startsWith('/dashboard/prompts')
                    ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                )}
              >
                <BookOpen className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/prompts') ? "text-violet-400" : "text-neutral-400")} />
                {sidebarOpen && (
                  <>
                    <span className="flex-1">Prompt Platform</span>
                    <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", promptsExpanded && "rotate-180")} />
                  </>
                )}
              </button>

              {/* Prompt Sub-items */}
              {sidebarOpen && promptsExpanded && (
                <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                  {promptSubItems.map((sub) => {
                    const SubIcon = sub.icon;
                    const isActive = pathname === sub.href;
                    return (
                      <button
                        key={sub.href}
                        onClick={() => router.push(sub.href)}
                        className={cn(
                          "flex items-center gap-2.5 py-1.5 px-2 rounded-md text-xs transition-all text-left cursor-pointer w-full",
                          isActive
                            ? "bg-violet-600/10 text-violet-400 font-semibold"
                            : "text-neutral-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <SubIcon className="w-3.5 h-3.5 shrink-0" />
                        {sub.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Other nav items */}
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = (item as any).exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                    isActive
                      ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                      : "text-neutral-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-violet-400" : "text-neutral-400")} />
                  {sidebarOpen && <span>{item.name}</span>}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User profile / Logout panel */}
        <div className="p-3 border-t border-white/5 flex flex-col gap-2 bg-neutral-950 relative">
          <div 
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className={cn(
              "flex items-center gap-3 rounded-lg hover:bg-white/5 cursor-pointer transition-colors p-2",
              !sidebarOpen && "justify-center p-1"
            )}
          >
            <div className="w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xs text-violet-300 shrink-0">
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            {sidebarOpen && (
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold truncate text-white">{user?.full_name}</span>
                <span className="text-[10px] text-neutral-500 truncate">{user?.email}</span>
              </div>
            )}
          </div>

          {/* Profile Menu Popover */}
          {showProfileMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowProfileMenu(false)} />
              <div className={cn(
                "absolute bg-neutral-900 border border-white/10 rounded-lg shadow-xl z-50 p-1 flex flex-col gap-0.5 min-w-[180px]",
                sidebarOpen ? "bottom-14 left-3 right-3" : "bottom-14 left-14"
              )}>
                <button
                  onClick={() => {
                    router.push('/dashboard/settings');
                    setShowProfileMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                >
                  <Settings className="w-3.5 h-3.5 text-neutral-400" />
                  <span>Profile Settings</span>
                </button>
                <button
                  onClick={() => {
                    logout();
                    setShowProfileMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors cursor-pointer text-left font-medium border-t border-white/5 mt-1 pt-1.5"
                >
                  <LogOut className="w-3.5 h-3.5 text-rose-400" />
                  <span>Log out</span>
                </button>
              </div>
            </>
          )}
        </div>
      </aside>

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-screen">
        {/* Header toolbar */}
        <header className="h-16 border-b border-white/5 px-6 flex items-center justify-between bg-neutral-950/60 backdrop-blur-md relative z-20 shrink-0">
          <div className="flex items-center gap-3">
            {/* Mobile Hamburger menu */}
            <button className="lg:hidden p-1.5 rounded-md hover:bg-white/5 text-neutral-400 hover:text-white transition-colors cursor-pointer">
              <Menu className="w-5 h-5" />
            </button>

            {/* Quick search input (Triggers Command palette) */}
            <div 
              onClick={() => setCommandPaletteOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:border-white/10 hover:text-neutral-300 transition-all text-xs cursor-pointer w-64 select-none"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search dashboard...</span>
              <kbd className="ml-auto bg-neutral-950 border border-white/10 rounded px-1 text-[9px] font-mono">⌘K</kbd>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Theme switcher */}
            <ThemeSwitcher variant="dropdown" />
            {/* Notification alert bell */}
            <button 
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:text-white hover:border-white/10 transition-all cursor-pointer relative"
            >
              <Bell className="w-4 h-4" />
              {notifications.length > 0 && (
                <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-violet-500" />
              )}
            </button>
          </div>
        </header>

        {/* Scrollable workspace inner pages */}
        <main className="flex-1 overflow-y-auto bg-background p-6 relative dashboard-content">
          <Breadcrumbs />
          <div className="mt-4">
            {children}
          </div>
        </main>
      </div>

      {/* 1. COMMAND PALETTE MODAL (Ctrl+K) */}
      <CommandPalette />

      {/* -------------------------------------------------- */}
      {/* 2. NOTIFICATIONS CENTER SIDEBAR / DRAWER */}
      {/* -------------------------------------------------- */}
      {notificationsOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs" onClick={() => setNotificationsOpen(false)} />
          <motion.div 
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            className="fixed top-0 right-0 bottom-0 w-80 bg-neutral-950 border-l border-white/10 shadow-2xl z-50 p-6 flex flex-col gap-6 text-white"
          >
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-violet-400" />
                <h3 className="font-bold">Notifications</h3>
              </div>
              <button 
                onClick={() => setNotificationsOpen(false)}
                className="p-1 rounded-md text-neutral-500 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto flex flex-col gap-3">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-4 gap-2 text-neutral-500">
                  <Bell className="w-8 h-8 opacity-20" />
                  <span className="text-xs">No new notifications</span>
                </div>
              ) : (
                notifications.map((n) => (
                  <div key={n.id} className="p-3.5 rounded-lg border border-white/5 bg-neutral-900/40 hover:border-violet-500/20 transition-all relative group">
                    <div className="flex justify-between items-center mb-1">
                      <span className={`text-[10px] font-semibold ${n.categoryColor} uppercase`}>{n.category}</span>
                      <span className="text-[9px] text-neutral-500">{n.time}</span>
                    </div>
                    <h4 className="text-xs font-semibold pr-4">{n.title}</h4>
                    <p className="text-[11px] text-neutral-400 mt-1">{n.description}</p>
                    <button 
                      onClick={() => setNotifications(notifications.filter((x) => x.id !== n.id))}
                      className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 text-[10px] text-neutral-500 hover:text-white transition-opacity cursor-pointer"
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
            
            <div className="border-t border-white/5 pt-4">
              <Button 
                variant="ghost" 
                size="sm" 
                disabled={notifications.length === 0}
                onClick={() => setNotifications([])}
                className="w-full text-xs text-neutral-400 hover:text-white"
              >
                Clear all notifications
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
