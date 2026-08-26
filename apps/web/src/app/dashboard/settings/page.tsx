'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import { 
  Settings, Globe, Sliders, Cpu, Shield, User, CreditCard, Key, 
  Radio, Palette, Building, Users, Lock, CheckCircle2, SlidersHorizontal, 
  Clock, Database, ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';

export default function SettingsDashboard() {
  const router = useRouter();
  const { activeOrg, user: currentUser } = useAuthStore();
  const [activeTab, setActiveTab] = React.useState<'general' | 'localization' | 'regional' | 'system' | 'defaults'>('general');

  // --- Profile / Org Queries ---
  const { data: userProfile, refetch: refetchProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const res = await apiClient.get('/users/me');
      return res.data;
    },
  });

  // --- 1. General Config States ---
  const [platformName, setPlatformName] = React.useState('EAIMOS Enterprise');
  const [landingPage, setLandingPage] = React.useState('/dashboard');
  const [defaultDashboard, setDefaultDashboard] = React.useState('core');
  const [enableMaintenanceMode, setEnableMaintenanceMode] = React.useState(false);

  // --- 2. Localization States ---
  const [language, setLanguage] = React.useState('en');
  const [timezone, setTimezone] = React.useState('UTC');
  const [dateFormat, setDateFormat] = React.useState('YYYY-MM-DD');
  const [numberFormat, setNumberFormat] = React.useState('en-US');

  // --- 3. Regional States ---
  const [countryRegion, setCountryRegion] = React.useState('US');
  const [currency, setCurrency] = React.useState('USD');

  // --- 4. System Behavior States ---
  const [defaultPagination, setDefaultPagination] = React.useState('25');
  const [autoRefreshInterval, setAutoRefreshInterval] = React.useState('30s');
  const [sessionTimeoutMinutes, setSessionTimeoutMinutes] = React.useState('60');
  const [defaultViewPreference, setDefaultViewPreference] = React.useState('grid');

  // --- 5. Platform Defaults States ---
  const [defaultAIProvider, setDefaultAIProvider] = React.useState('openai');
  const [defaultAIModel, setDefaultAIModel] = React.useState('gpt-4o');
  const [defaultNotificationBehavior, setDefaultNotificationBehavior] = React.useState('all');

  React.useEffect(() => {
    if (userProfile?.preferences) {
      const p = userProfile.preferences;
      if (p.language) setLanguage(p.language);
      if (p.timezone) setTimezone(p.timezone);
      if (p.date_format) setDateFormat(p.date_format);
      if (p.currency) setCurrency(p.currency);
      if (p.default_pagination) setDefaultPagination(String(p.default_pagination));
      if (p.default_model) setDefaultAIModel(p.default_model);
      if (p.default_provider) setDefaultAIProvider(p.default_provider);
    }
  }, [userProfile]);

  const saveSettingsMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch('/users/me/preferences', {
        platform_name: platformName,
        landing_page: landingPage,
        default_dashboard: defaultDashboard,
        language,
        timezone,
        date_format: dateFormat,
        number_format: numberFormat,
        country_region: countryRegion,
        currency,
        default_pagination: parseInt(defaultPagination) || 25,
        auto_refresh: autoRefreshInterval,
        session_timeout: parseInt(sessionTimeoutMinutes) || 60,
        default_view: defaultViewPreference,
        default_provider: defaultAIProvider,
        default_model: defaultAIModel,
        notification_behavior: defaultNotificationBehavior,
      });
    },
    onSuccess: () => {
      refetchProfile();
      toast.success('Platform Settings Saved', 'Configuration successfully applied across workspace.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.response?.data?.detail || err.message);
    }
  });

  const platformTabs = [
    { id: 'general', label: 'General', icon: Settings, desc: 'Platform Name, Default Landing Page, General Config' },
    { id: 'localization', label: 'Localization', icon: Globe, desc: 'Language, Timezone, Date & Number Formats' },
    { id: 'regional', label: 'Regional Settings', icon: Building, desc: 'Country/Region, Currency, Regional Defaults' },
    { id: 'system', label: 'System Behavior', icon: Sliders, desc: 'Pagination, Session Preferences, Auto Refresh' },
    { id: 'defaults', label: 'Platform Defaults', icon: Cpu, desc: 'Default AI Model, Provider, Notification Rules' },
  ];

  const quickNavCards = [
    { label: 'Account & Profile', path: '/dashboard/settings/account', icon: User, desc: 'Profile identity, email verification, account lifecycle' },
    { label: 'Security & Passwords', path: '/dashboard/settings/security', icon: Shield, desc: 'Password change, active sessions, trusted devices & MFA' },
    { label: 'Users & Teams', path: '/dashboard/settings/users', icon: Users, desc: 'Tenant members, RBAC roles, invitations' },
    { label: 'Integrations', path: '/dashboard/settings/integrations', icon: Radio, desc: 'Connected apps, webhooks, OAuth credentials' },
    { label: 'Organization', path: '/dashboard/settings/organization', icon: Building, desc: 'Workspace profile, slug, archive controls' },
    { label: 'Privacy & Data', path: '/dashboard/settings/privacy', icon: Lock, desc: 'GDPR exports, retention policy, data management' },
    { label: 'Billing & Subscriptions', path: '/dashboard/settings/billing', icon: CreditCard, desc: 'Enterprise plans, usage quotas, invoice history' },
    { label: 'API Credentials', path: '/dashboard/settings/credentials', icon: Key, desc: 'Scoped API tokens, IP allowlists, access keys' },
    { label: 'Preferences', path: '/dashboard/settings/preferences', icon: Palette, desc: 'Theme switcher, notification delivery rules' },
  ];

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Settings Console <Settings className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-1">
          Configure tenant profiles, check account activity, manage security, organization configuration and platform settings.
        </p>
      </header>

      {/* Main Grid: Platform Settings Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        
        {/* Left Sub-Tab Navigation for Platform Settings */}
        <Card className="glass p-3 border-white/5 flex flex-col gap-1">
          <div className="px-3 py-2 text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
            Platform Settings
          </div>
          {platformTabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  isActive 
                    ? 'bg-violet-600/15 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none' 
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <div className="flex flex-col min-w-0">
                  <span className="truncate">{tab.label}</span>
                </div>
              </button>
            );
          })}
        </Card>

        {/* Right Content Panels */}
        <div className="lg:col-span-3 space-y-6">

          {/* 1. GENERAL */}
          {activeTab === 'general' && (
            <Card className="glass p-6 border-white/5 space-y-6">
              <div>
                <h3 className="font-bold text-base text-white">General Platform Configuration</h3>
                <p className="text-xs text-neutral-400 mt-1">Configure workspace title, default navigation entry, and core behaviors.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                <Input
                  label="Platform Name"
                  value={platformName}
                  onChange={(e) => setPlatformName(e.target.value)}
                  placeholder="EAIMOS Enterprise"
                />

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Landing Page</label>
                  <select
                    value={landingPage}
                    onChange={(e) => setLandingPage(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="/dashboard">Core Dashboard (/dashboard)</option>
                    <option value="/dashboard/ai/providers">AI Platform (/dashboard/ai/providers)</option>
                    <option value="/dashboard/playground/workspace">Playground (/dashboard/playground/workspace)</option>
                    <option value="/dashboard/prompts">Prompt Platform (/dashboard/prompts)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Dashboard View</label>
                  <select
                    value={defaultDashboard}
                    onChange={(e) => setDefaultDashboard(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="core">Core Platform Analytics</option>
                    <option value="ai">AI Gateway & Health Observability</option>
                    <option value="agents">Agent Studio Operations</option>
                  </select>
                </div>
              </div>
            </Card>
          )}

          {/* 2. LOCALIZATION */}
          {activeTab === 'localization' && (
            <Card className="glass p-6 border-white/5 space-y-6">
              <div>
                <h3 className="font-bold text-base text-white">Localization & Formatting</h3>
                <p className="text-xs text-neutral-400 mt-1">Set system-wide display language, timezone offsets, and numeric conventions.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="en">English (US)</option>
                    <option value="en-GB">English (UK)</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                    <option value="ja">日本語</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Time Zone</label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="UTC">UTC (Universal Coordinated Time)</option>
                    <option value="America/New_York">America/New_York (EST/EDT)</option>
                    <option value="America/Los_Angeles">America/Los_Angeles (PST/PDT)</option>
                    <option value="Europe/London">Europe/London (GMT/BST)</option>
                    <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Date Format</label>
                  <select
                    value={dateFormat}
                    onChange={(e) => setDateFormat(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="YYYY-MM-DD">YYYY-MM-DD (ISO 8601)</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY (US Standard)</option>
                    <option value="DD/MM/YYYY">DD/MM/YYYY (European)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Number Format</label>
                  <select
                    value={numberFormat}
                    onChange={(e) => setNumberFormat(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="en-US">1,234,567.89 (Standard)</option>
                    <option value="de-DE">1.234.567,89 (European)</option>
                    <option value="fr-FR">1 234 567,89 (Space Delimited)</option>
                  </select>
                </div>
              </div>
            </Card>
          )}

          {/* 3. REGIONAL SETTINGS */}
          {activeTab === 'regional' && (
            <Card className="glass p-6 border-white/5 space-y-6">
              <div>
                <h3 className="font-bold text-base text-white">Regional Settings</h3>
                <p className="text-xs text-neutral-400 mt-1">Configure compliance regions, data sovereignty, and primary currency.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Country / Region</label>
                  <select
                    value={countryRegion}
                    onChange={(e) => setCountryRegion(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="US">United States (US)</option>
                    <option value="EU">European Union (EU - GDPR Compliant)</option>
                    <option value="UK">United Kingdom (UK)</option>
                    <option value="CA">Canada (CA)</option>
                    <option value="APAC">Asia-Pacific (APAC)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Currency</label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="JPY">JPY (¥)</option>
                  </select>
                </div>
              </div>
            </Card>
          )}

          {/* 4. SYSTEM BEHAVIOR */}
          {activeTab === 'system' && (
            <Card className="glass p-6 border-white/5 space-y-6">
              <div>
                <h3 className="font-bold text-base text-white">System Behavior</h3>
                <p className="text-xs text-neutral-400 mt-1">Fine-tune pagination sizes, session timeouts, and dashboard auto-polling intervals.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Table Pagination</label>
                  <select
                    value={defaultPagination}
                    onChange={(e) => setDefaultPagination(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="10">10 items per page</option>
                    <option value="25">25 items per page (Recommended)</option>
                    <option value="50">50 items per page</option>
                    <option value="100">100 items per page</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Live Auto-Refresh Interval</label>
                  <select
                    value={autoRefreshInterval}
                    onChange={(e) => setAutoRefreshInterval(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="10s">Every 10 seconds</option>
                    <option value="30s">Every 30 seconds (Standard)</option>
                    <option value="60s">Every 60 seconds</option>
                    <option value="off">Disabled (Manual refresh only)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Idle Session Inactivity Timeout</label>
                  <select
                    value={sessionTimeoutMinutes}
                    onChange={(e) => setSessionTimeoutMinutes(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="15">15 Minutes</option>
                    <option value="30">30 Minutes</option>
                    <option value="60">60 Minutes</option>
                    <option value="480">8 Hours</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default View Preference</label>
                  <select
                    value={defaultViewPreference}
                    onChange={(e) => setDefaultViewPreference(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="grid">Grid Card View</option>
                    <option value="table">Tabular List View</option>
                  </select>
                </div>
              </div>
            </Card>
          )}

          {/* 5. PLATFORM DEFAULTS */}
          {activeTab === 'defaults' && (
            <Card className="glass p-6 border-white/5 space-y-6">
              <div>
                <h3 className="font-bold text-base text-white">Platform Defaults & Routing</h3>
                <p className="text-xs text-neutral-400 mt-1">Set workspace-wide default LLM foundation models and provider failovers.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default AI Provider</label>
                  <select
                    value={defaultAIProvider}
                    onChange={(e) => setDefaultAIProvider(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="groq">Groq LPU</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Foundation Model</label>
                  <select
                    value={defaultAIModel}
                    onChange={(e) => setDefaultAIModel(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="gpt-4o">GPT-4o (Omni)</option>
                    <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                    <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Default Notification Behavior</label>
                  <select
                    value={defaultNotificationBehavior}
                    onChange={(e) => setDefaultNotificationBehavior(e.target.value)}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="all">All Alerts (Push + Email)</option>
                    <option value="security-only">Security & Critical Events Only</option>
                    <option value="digest">Daily Consolidated Digest</option>
                  </select>
                </div>
              </div>
            </Card>
          )}

          {/* Save Settings Action */}
          <div className="pt-2">
            <Button
              variant="violet"
              onClick={() => saveSettingsMutation.mutate()}
              isLoading={saveSettingsMutation.isPending}
              className="px-6 py-2.5 text-xs font-semibold"
            >
              Save Platform Configuration
            </Button>
          </div>

        </div>
      </div>

      {/* Settings Module Navigation Category Cards */}
      <div className="pt-6 border-t border-white/5 space-y-4">
        <h2 className="text-base font-bold text-white">Settings Platform Directory</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickNavCards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.path}
                onClick={() => router.push(card.path)}
                className="glass p-4 rounded-xl border border-white/5 hover:border-violet-500/30 hover:bg-violet-600/[0.03] transition-all cursor-pointer group flex flex-col justify-between gap-3"
              >
                <div className="flex items-start justify-between">
                  <div className="w-8 h-8 rounded-lg bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 group-hover:scale-105 transition-transform">
                    <Icon className="w-4 h-4" />
                  </div>
                  <ArrowRight className="w-4 h-4 text-neutral-600 group-hover:text-violet-400 transition-colors" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                    {card.label}
                  </h3>
                  <p className="text-[11px] text-neutral-400 mt-1 leading-snug">
                    {card.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
