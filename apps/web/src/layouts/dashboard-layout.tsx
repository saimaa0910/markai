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
  Cpu, Database, TrendingUp, Router, SlidersHorizontal, ChevronDown, Terminal, Columns, Activity, Shield, UploadCloud, Sparkles, FileText, Code, History, Library, Server, Share2, Image, Key, User, Lock, ArrowLeft, CreditCard, Palette
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

  // Group expansion states matching the EAIMOS Information Architecture
  const [aiExpanded, setAiExpanded] = React.useState(pathname.startsWith('/dashboard/ai'));
  const [playgroundExpanded, setPlaygroundExpanded] = React.useState(
    pathname.startsWith('/dashboard/playground') || 
    pathname.startsWith('/dashboard/conversations') ||
    pathname.startsWith('/dashboard/ai/playground') ||
    pathname.startsWith('/dashboard/image-studio') ||
    pathname.startsWith('/dashboard/social-studio')
  );
  const [knowledgeExpanded, setKnowledgeExpanded] = React.useState(
    pathname.startsWith('/dashboard/knowledge') || 
    pathname.startsWith('/dashboard/files')
  );
  const isInsideSettings = pathname.startsWith('/dashboard/settings') || 
    pathname === '/dashboard/users' || 
    pathname === '/dashboard/integrations';

  const [promptsExpanded, setPromptsExpanded] = React.useState(pathname.startsWith('/dashboard/prompts'));
  const [agentsExpanded, setAgentsExpanded] = React.useState(pathname.startsWith('/dashboard/agents'));
  const [workflowsExpanded, setWorkflowsExpanded] = React.useState(pathname.startsWith('/dashboard/workflows'));
  const [settingsExpanded, setSettingsExpanded] = React.useState(true);

  const [showProfileMenu, setShowProfileMenu] = React.useState(false);
  const [isProfileHovered, setIsProfileHovered] = React.useState(false);
  const hoverTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnterProfile = () => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    setIsProfileHovered(true);
  };

  const handleMouseLeaveProfile = () => {
    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    hoverTimeoutRef.current = setTimeout(() => {
      setIsProfileHovered(false);
    }, 150);
  };

  const userInitials = React.useMemo(() => {
    if (!user) return 'U';
    if (user.full_name) {
      const parts = user.full_name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return parts[0][0].toUpperCase();
    }
    if (user.email) {
      return user.email.charAt(0).toUpperCase();
    }
    return 'U';
  }, [user]);

  const userRole = React.useMemo(() => {
    if (!user) return 'Member';
    if (user.is_superuser) return 'Super Admin';
    if (user.role) return user.role.charAt(0).toUpperCase() + user.role.slice(1);
    return 'Member';
  }, [user]);

  const userAvatarUrl = user?.metadata_json?.avatar_url || user?.metadata_json?.picture || null;

  const [notifications, setNotifications] = React.useState([
    { id: '1', category: 'AI Completed', categoryColor: 'text-violet-400', time: '2m ago', title: 'Variant A Creative generated', description: 'AI variant copy draft for "Summer Promo Ad" is complete.' },
    { id: '2', category: 'CRM Update', categoryColor: 'text-emerald-400', time: '1h ago', title: 'New high-value lead logged', description: 'Lead "Sarah Jenkins (Acme Corp)" value: $15,400.' }
  ]);

  // Protect client route
  React.useEffect(() => {
    if (!accessToken) {
      router.push('/auth/login');
    } else if (user?.deletion_requested_at) {
      router.push('/auth/restore-account');
    }
  }, [accessToken, user, router]);

  // Keyboard shortcut listener (Cmd+K and Escape)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      } else if (e.key === 'Escape') {
        setShowProfileMenu(false);
        setIsProfileHovered(false);
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

  // 1. Core Top-Level Navigation Items
  const coreNavItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, exact: true },
  ];

  // 2. AI Platform / AI Gateway Sub-items
  const aiSubItems = [
    { name: 'Providers', href: '/dashboard/ai/providers', icon: Cpu },
    { name: 'Models', href: '/dashboard/ai/models', icon: Database },
    { name: 'Health Center', href: '/dashboard/ai/health', icon: Activity },
    { name: 'Admin Console', href: '/dashboard/ai/admin', icon: Shield },
    { name: 'Usage', href: '/dashboard/ai/usage', icon: TrendingUp },
    { name: 'Analytics', href: '/dashboard/ai/analytics', icon: BarChart2 },
    { name: 'Router', href: '/dashboard/ai/router', icon: Router },
    { name: 'Security Center', href: '/dashboard/ai/security', icon: Shield },
    { name: 'Infrastructure', href: '/dashboard/ai/infrastructure', icon: Server },
    { name: 'Observability', href: '/dashboard/ai/observability', icon: Activity },
  ];

  // 3. Playground Platform Sub-items
  const playgroundSubItems = [
    { name: 'AI Workspace', href: '/dashboard/playground/workspace', icon: Sparkles },
    { name: 'AI Playground / Sandbox', href: '/dashboard/playground/sandbox', icon: Terminal },
    { name: 'Agent Sandbox', href: '/dashboard/playground/agent-sandbox', icon: Bot },
    { name: 'Conversations', href: '/dashboard/playground/conversations', icon: MessageSquare },
    { name: 'Compare Lab', href: '/dashboard/playground/compare', icon: Columns },
    { name: 'Image Studio', href: '/dashboard/playground/image-studio', icon: Image },
    { name: 'Social Studio', href: '/dashboard/playground/social-studio', icon: Share2 },
  ];

  // 4. Prompt Platform Sub-items
  const promptSubItems = [
    { name: 'Dashboard', href: '/dashboard/prompts', icon: LayoutDashboard },
    { name: 'Library', href: '/dashboard/prompts/library', icon: BookOpen },
    { name: 'Workspace Editor', href: '/dashboard/prompts/editor', icon: Code },
    { name: 'Testing Lab', href: '/dashboard/prompts/testing', icon: SlidersHorizontal },
    { name: 'Version Control', href: '/dashboard/prompts/history', icon: History },
    { name: 'Template Gallery', href: '/dashboard/prompts/templates', icon: Library },
    { name: 'Performance Stats', href: '/dashboard/prompts/analytics', icon: BarChart2 },
  ];

  // 5. Knowledge Platform Sub-items (Includes Files)
  const knowledgeSubItems = [
    { name: 'Dashboard', href: '/dashboard/knowledge', icon: LayoutDashboard },
    { name: 'Documents', href: '/dashboard/knowledge/documents', icon: FileText },
    { name: 'Files', href: '/dashboard/knowledge/files', icon: FolderOpen },
    { name: 'Collections', href: '/dashboard/knowledge/collections', icon: FolderOpen },
    { name: 'Semantic Search', href: '/dashboard/knowledge/search', icon: Search },
    { name: 'Upload Center', href: '/dashboard/knowledge/upload', icon: UploadCloud },
    { name: 'Vector Embeddings', href: '/dashboard/knowledge/embeddings', icon: Sparkles },
    { name: 'Analytics', href: '/dashboard/knowledge/analytics', icon: BarChart2 },
    { name: 'Settings', href: '/dashboard/knowledge/settings', icon: Settings },
  ];

  // 6. AI Agents Sub-items
  const agentsSubItems = [
    { name: 'Dashboard', href: '/dashboard/agents', icon: LayoutDashboard },
    { name: 'Marketplace', href: '/dashboard/agents/marketplace', icon: Library },
    { name: 'Create Agent', href: '/dashboard/agents/create', icon: Bot },
    { name: 'Templates', href: '/dashboard/agents/templates', icon: Library },
    { name: 'Runs Timeline', href: '/dashboard/agents/runs', icon: History },
    { name: 'Execution Logs', href: '/dashboard/agents/logs', icon: Activity },
    { name: 'Analytics', href: '/dashboard/agents/analytics', icon: BarChart2 },
    { name: 'Settings', href: '/dashboard/agents/settings', icon: Settings },
  ];

  // 7. Workflow Engine Sub-items
  const workflowsSubItems = [
    { name: 'Dashboard', href: '/dashboard/workflows', icon: LayoutDashboard },
    { name: 'Visual Builder', href: '/dashboard/workflows/create', icon: Sparkles },
    { name: 'Templates', href: '/dashboard/workflows/templates', icon: Library },
    { name: 'Executions History', href: '/dashboard/workflows/history', icon: History },
    { name: 'Workflow Logs', href: '/dashboard/workflows/logs', icon: Activity },
    { name: 'Settings', href: '/dashboard/workflows/settings', icon: Settings },
  ];

  // 8. Marketing & CRM Core Items
  const businessItems = [
    { name: 'Marketing Platform', href: '/dashboard/campaigns', icon: Megaphone },
    { name: 'CRM', href: '/dashboard/crm', icon: Users },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart2 },
  ];

  // 9. Settings Platform Mode Items (Shown exclusively when inside Settings)
  const settingsNavigationList = [
    { name: 'Platform Settings', href: '/dashboard/settings', icon: Settings, exact: true },
    { name: 'Account & Profile', href: '/dashboard/settings/account', icon: User },
    { name: 'Security & Passwords', href: '/dashboard/settings/security', icon: Shield },
    { name: 'Users & Teams', href: '/dashboard/settings/users', icon: Users },
    { name: 'Integrations', href: '/dashboard/settings/integrations', icon: Plug },
    { name: 'Organization', href: '/dashboard/settings/organization', icon: Building },
    { name: 'Privacy & Data', href: '/dashboard/settings/privacy', icon: Lock },
    { name: 'Billing & Subscriptions', href: '/dashboard/settings/billing', icon: CreditCard },
    { name: 'API Credentials', href: '/dashboard/settings/credentials', icon: Key },
    { name: 'Preferences', href: '/dashboard/settings/preferences', icon: Palette },
  ];

  return (
    <div className="min-h-screen h-screen bg-black flex text-white font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <aside 
        className={cn(
          "bg-neutral-950 border-r border-white/5 transition-[width] duration-300 ease-in-out flex flex-col justify-between relative z-30 shrink-0 select-none",
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
          <nav className="p-3 flex flex-col gap-0.5 overflow-y-auto max-h-[calc(100vh-190px)]">
            {isInsideSettings ? (
              /* DEDICATED SETTINGS NAVIGATION MODE (Exclusively shown when inside settings) */
              <div className="flex flex-col gap-1">
                {/* Back to Platform Dashboard */}
                <button
                  onClick={() => router.push('/dashboard')}
                  className={cn(
                    "flex items-center gap-2.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all text-neutral-400 hover:text-white hover:bg-white/5 cursor-pointer mb-2 border border-white/5 bg-white/[0.02]",
                    !sidebarOpen && "justify-center px-2"
                  )}
                  title="Back to Dashboard"
                >
                  <ArrowLeft className="w-4 h-4 text-violet-400 shrink-0" />
                  {sidebarOpen && <span>Back to Dashboard</span>}
                </button>

                <div className="px-3 py-1.5 text-[10px] font-bold text-neutral-500 uppercase tracking-widest">
                  {sidebarOpen ? 'Platform Settings' : 'SET'}
                </div>

                {settingsNavigationList.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.exact 
                    ? pathname === item.href 
                    : (pathname === item.href || 
                       (item.href === '/dashboard/settings/users' && (pathname === '/dashboard/users' || pathname.startsWith('/dashboard/settings/users'))) || 
                       (item.href === '/dashboard/settings/integrations' && (pathname === '/dashboard/integrations' || pathname.startsWith('/dashboard/settings/integrations'))) || 
                       (item.href === '/dashboard/settings/security' && pathname.startsWith('/dashboard/settings/security')) || 
                       pathname.startsWith(item.href + '/'));
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
                      title={item.name}
                    >
                      <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-violet-400" : "text-neutral-400")} />
                      {sidebarOpen && <span>{item.name}</span>}
                    </button>
                  );
                })}
              </div>
            ) : (
              /* STANDARD PLATFORM NAVIGATION MODE */
              <>
                {/* 1. Core Platform: Dashboard */}
                {coreNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
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

                {/* 2. AI Platform / AI Gateway Group */}
                <div className="flex flex-col gap-0.5 mt-1">
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
                    <Cpu className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/ai') ? "text-violet-400" : "text-neutral-400")} />
                    {sidebarOpen && (
                      <>
                        <span className="flex-1">AI Platform</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", aiExpanded && "rotate-180")} />
                      </>
                    )}
                  </button>

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

                {/* 3. Playground Group */}
                <div className="flex flex-col gap-0.5 mt-1">
                  <button
                    onClick={() => {
                      if (!sidebarOpen) router.push('/dashboard/playground/workspace');
                      else setPlaygroundExpanded(!playgroundExpanded);
                    }}
                    className={cn(
                      "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                      (pathname.startsWith('/dashboard/playground') || pathname.startsWith('/dashboard/conversations') || pathname.startsWith('/dashboard/image-studio') || pathname.startsWith('/dashboard/social-studio'))
                        ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                        : "text-neutral-400 hover:text-white hover:bg-white/5"
                    )}
                  >
                    <Terminal className={cn(
                      "w-4 h-4 shrink-0", 
                      (pathname.startsWith('/dashboard/playground') || pathname.startsWith('/dashboard/conversations') || pathname.startsWith('/dashboard/image-studio') || pathname.startsWith('/dashboard/social-studio'))
                        ? "text-violet-400" 
                        : "text-neutral-400"
                    )} />
                    {sidebarOpen && (
                      <>
                        <span className="flex-1">Playground</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", playgroundExpanded && "rotate-180")} />
                      </>
                    )}
                  </button>

                  {sidebarOpen && playgroundExpanded && (
                    <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                      {playgroundSubItems.map((sub) => {
                        const SubIcon = sub.icon;
                        const isActive = pathname === sub.href || 
                          (sub.href === '/dashboard/playground/workspace' && (pathname === '/dashboard/playground' || pathname === '/dashboard/playground/workspace')) ||
                          (sub.href === '/dashboard/playground/conversations' && (pathname === '/dashboard/conversations' || pathname === '/dashboard/playground/conversations')) ||
                          (sub.href === '/dashboard/playground/compare' && (pathname === '/dashboard/ai/compare' || pathname === '/dashboard/playground/compare')) ||
                          (sub.href === '/dashboard/playground/agent-sandbox' && (pathname === '/dashboard/agents/playground' || pathname === '/dashboard/playground/agent-sandbox')) ||
                          (sub.href === '/dashboard/playground/sandbox' && (pathname === '/dashboard/ai/playground' || pathname === '/dashboard/playground/sandbox')) ||
                          (sub.href === '/dashboard/playground/image-studio' && (pathname === '/dashboard/image-studio' || pathname === '/dashboard/playground/image-studio')) ||
                          (sub.href === '/dashboard/playground/social-studio' && (pathname === '/dashboard/social-studio' || pathname === '/dashboard/playground/social-studio'));
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

                {/* 4. Prompt Platform Group */}
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

                {/* 5. Knowledge Platform Group (Contains Files) */}
                <div className="flex flex-col gap-0.5 mt-1">
                  <button
                    onClick={() => {
                      if (!sidebarOpen) router.push('/dashboard/knowledge');
                      else setKnowledgeExpanded(!knowledgeExpanded);
                    }}
                    className={cn(
                      "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full",
                      (pathname.startsWith('/dashboard/knowledge') || pathname === '/dashboard/files')
                        ? "bg-violet-600/10 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none"
                        : "text-neutral-400 hover:text-white hover:bg-white/5"
                    )}
                  >
                    <Brain className={cn("w-4 h-4 shrink-0", (pathname.startsWith('/dashboard/knowledge') || pathname === '/dashboard/files') ? "text-violet-400" : "text-neutral-400")} />
                    {sidebarOpen && (
                      <>
                        <span className="flex-1">Knowledge Platform</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", knowledgeExpanded && "rotate-180")} />
                      </>
                    )}
                  </button>

                  {sidebarOpen && knowledgeExpanded && (
                    <div className="ml-6 flex flex-col gap-0.5 border-l border-white/5 pl-3">
                      {knowledgeSubItems.map((sub) => {
                        const SubIcon = sub.icon;
                        const isActive = pathname === sub.href || (sub.href === '/dashboard/knowledge/files' && pathname === '/dashboard/files');
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

                {/* 6. AI Agents Platform Group */}
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
                        <span className="flex-1">AI Agents</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", agentsExpanded && "rotate-180")} />
                      </>
                    )}
                  </button>

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

                {/* 7. Workflow Engine Studio Group */}
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
                    <SlidersHorizontal className={cn("w-4 h-4 shrink-0", pathname.startsWith('/dashboard/workflows') ? "text-violet-400" : "text-neutral-400")} />
                    {sidebarOpen && (
                      <>
                        <span className="flex-1">Workflow Engine</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", workflowsExpanded && "rotate-180")} />
                      </>
                    )}
                  </button>

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

                {/* 8. Marketing, CRM, Analytics */}
                {businessItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                  return (
                    <button
                      key={item.href}
                      onClick={() => router.push(item.href)}
                      className={cn(
                        "flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer w-full mt-0.5",
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
              </>
            )}

          </nav>
        </div>

        {/* Sidebar bottom status */}
        <div className="p-3 border-t border-white/5 flex items-center justify-between text-[11px] text-neutral-600 bg-neutral-950/90">
          {sidebarOpen ? (
            <>
              <span className="font-mono">EAIMOS Enterprise</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-neutral-400 font-mono">v2.4</span>
            </>
          ) : (
            <span className="mx-auto text-[9px] font-mono text-neutral-500">v2.4</span>
          )}
        </div>
      </aside>

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 h-full overflow-hidden">
        {/* Header toolbar */}
        <header className="h-16 border-b border-white/5 px-6 flex items-center justify-between bg-neutral-950/60 backdrop-blur-md relative z-20 shrink-0">
          <div className="flex items-center gap-3">
            {/* Mobile Hamburger menu */}
            <button 
              onClick={toggleSidebar}
              className="lg:hidden p-1.5 rounded-md hover:bg-white/5 text-neutral-400 hover:text-white transition-colors cursor-pointer"
            >
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
            {/* 1. Profile / Account Avatar (Top Right, Before Notification Icon) */}
            <div 
              className="relative"
              onMouseEnter={handleMouseEnterProfile}
              onMouseLeave={handleMouseLeaveProfile}
            >
              <button
                id="header-profile-button"
                type="button"
                aria-label={`Account menu for ${user?.full_name || 'User'}`}
                aria-haspopup="menu"
                aria-expanded={showProfileMenu}
                onClick={() => {
                  setShowProfileMenu((prev) => !prev);
                  setIsProfileHovered(false);
                }}
                onFocus={handleMouseEnterProfile}
                onBlur={handleMouseLeaveProfile}
                className={cn(
                  "w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xs text-violet-300 hover:border-violet-400 hover:bg-violet-600/30 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-violet-500/50 shadow-sm",
                  showProfileMenu && "ring-2 ring-violet-500/60 border-violet-400 bg-violet-600/40"
                )}
              >
                {userAvatarUrl ? (
                  <img src={userAvatarUrl} alt={user?.full_name || 'User'} className="w-full h-full rounded-full object-cover" />
                ) : (
                  <span>{userInitials}</span>
                )}
              </button>

              {/* Hover Account Information Card */}
              {isProfileHovered && !showProfileMenu && (
                <div
                  className="absolute z-50 p-2.5 rounded-xl border border-white/10 bg-neutral-900/95 backdrop-blur-xl shadow-2xl flex items-center gap-3 pointer-events-auto top-full mt-2 right-0 min-w-[210px]"
                >
                  <div className="w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xs text-violet-300 shrink-0">
                    {userAvatarUrl ? (
                      <img src={userAvatarUrl} alt={user?.full_name || 'User'} className="w-full h-full rounded-full object-cover" />
                    ) : (
                      <span>{userInitials}</span>
                    )}
                  </div>
                  <div className="flex flex-col min-w-0 pr-1 text-left">
                    <span className="text-xs font-semibold text-white truncate">{user?.full_name || 'Authenticated User'}</span>
                    <span className="text-[10px] text-neutral-400 truncate">{user?.email || 'user@eaimos.internal'}</span>
                  </div>
                </div>
              )}

              {/* Click Account Menu Popover */}
              {showProfileMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowProfileMenu(false)} />
                  <div 
                    role="menu"
                    aria-orientation="vertical"
                    className="absolute bg-neutral-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl z-50 p-1.5 flex flex-col gap-1 w-64 text-left top-full mt-2 right-0"
                  >
                    {/* Account Header */}
                    <div className="p-2.5 border-b border-white/5 flex items-center gap-3 bg-white/[0.02] rounded-lg">
                      <div className="w-9 h-9 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center font-bold text-xs text-violet-300 shrink-0">
                        {userAvatarUrl ? (
                          <img src={userAvatarUrl} alt={user?.full_name || 'User'} className="w-full h-full rounded-full object-cover" />
                        ) : (
                          <span>{userInitials}</span>
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-semibold text-white truncate">{user?.full_name || 'User Account'}</span>
                        <span className="text-[10px] text-neutral-400 truncate">{user?.email}</span>
                        <span className="text-[9px] font-medium text-violet-400 mt-0.5">{userRole}</span>
                      </div>
                    </div>

                    {/* Menu Items */}
                    <div className="flex flex-col gap-0.5 py-1">
                      <button
                        role="menuitem"
                        onClick={() => {
                          router.push('/dashboard/settings');
                          setShowProfileMenu(false);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                      >
                        <Settings className="w-4 h-4 text-neutral-400" />
                        <div className="flex-1">
                          <span className="block leading-tight">Profile & Platform Settings</span>
                          <span className="text-[9px] text-neutral-500 block leading-tight">Preferences & workspace</span>
                        </div>
                      </button>

                      <button
                        role="menuitem"
                        onClick={() => {
                          router.push('/dashboard/settings/security');
                          setShowProfileMenu(false);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                      >
                        <Shield className="w-4 h-4 text-emerald-400" />
                        <div className="flex-1">
                          <span className="block leading-tight">Security & MFA</span>
                          <span className="text-[9px] text-neutral-500 block leading-tight">Trusted devices & passwords</span>
                        </div>
                      </button>

                      <button
                        role="menuitem"
                        onClick={() => {
                          router.push('/dashboard/settings/security');
                          setShowProfileMenu(false);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                      >
                        <Key className="w-4 h-4 text-cyan-400" />
                        <div className="flex-1">
                          <span className="block leading-tight">Active Sessions</span>
                          <span className="text-[9px] text-neutral-500 block leading-tight">Manage active logins</span>
                        </div>
                      </button>

                      <button
                        role="menuitem"
                        onClick={() => {
                          router.push('/dashboard/settings/users');
                          setShowProfileMenu(false);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                      >
                        <Users className="w-4 h-4 text-amber-400" />
                        <div className="flex-1">
                          <span className="block leading-tight">Users & Teams</span>
                          <span className="text-[9px] text-neutral-500 block leading-tight">Team members & RBAC</span>
                        </div>
                      </button>

                      <button
                        role="menuitem"
                        onClick={() => {
                          router.push('/dashboard/settings/integrations');
                          setShowProfileMenu(false);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors cursor-pointer text-left font-medium"
                      >
                        <Plug className="w-4 h-4 text-violet-400" />
                        <div className="flex-1">
                          <span className="block leading-tight">Integrations</span>
                          <span className="text-[9px] text-neutral-500 block leading-tight">Connected platforms & webhooks</span>
                        </div>
                      </button>
                    </div>

                    {/* Sign Out Action */}
                    <div className="pt-1 border-t border-white/5">
                      <button
                        role="menuitem"
                        onClick={() => {
                          logout();
                          setShowProfileMenu(false);
                          router.push('/auth/login');
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors cursor-pointer text-left font-medium"
                      >
                        <LogOut className="w-4 h-4 text-rose-400" />
                        <span>Sign out</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* 2. Notification alert bell */}
            <button 
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:text-white hover:border-white/10 transition-all cursor-pointer relative"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              {notifications.length > 0 && (
                <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-violet-500" />
              )}
            </button>

            {/* 3. Theme switcher (Dark / Light mode icon) */}
            <ThemeSwitcher variant="dropdown" />
          </div>
        </header>

        {/* Scrollable workspace inner pages */}
        <main className="flex-1 min-h-0 overflow-y-auto bg-background p-6 relative dashboard-content">
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

export default DashboardLayout;
