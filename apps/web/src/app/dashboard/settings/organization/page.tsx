'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { toast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Building2, Globe, Clock, Palette, Cpu, Image, Save, Archive,
  AlertTriangle, Users, ArrowRight, Shield,
} from 'lucide-react';

const AI_PROVIDERS = ['', 'openai', 'anthropic', 'groq', 'gemini', 'perplexity'];
const IMAGE_PROVIDERS = ['', 'openai', 'stability', 'replicate', 'fal'];
const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo', 'Asia/Singapore', 'Australia/Sydney',
];
const INDUSTRIES = [
  '', 'Technology', 'Marketing', 'Healthcare', 'Finance', 'Education', 'Retail', 'Media', 'Legal', 'Other'
];

interface OrgSettings {
  name: string;
  logo_url: string;
  website: string;
  industry: string;
  timezone: string;
  locale: string;
  language: string;
  theme_color: string;
  billing_email: string;
  default_ai_provider: string;
  default_image_provider: string;
  default_ai_model: string;
}

export default function OrganizationSettingsPage() {
  const { accessToken, activeOrg, setActiveOrg } = useAuthStore();
  const [saving, setSaving] = React.useState(false);
  const [transferEmail, setTransferEmail] = React.useState('');
  const [showTransferConfirm, setShowTransferConfirm] = React.useState(false);

  const [settings, setSettings] = React.useState<OrgSettings>({
    name: activeOrg?.name || '',
    logo_url: '',
    website: '',
    industry: '',
    timezone: 'UTC',
    locale: 'en-US',
    language: 'en',
    theme_color: '#6d28d9',
    billing_email: '',
    default_ai_provider: '',
    default_image_provider: '',
    default_ai_model: '',
  });

  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'X-Organization-Id': activeOrg?.id || '',
  };

  // Load org settings
  React.useEffect(() => {
    if (!activeOrg?.id) return;
    apiClient.get(`/organizations/${activeOrg.id}/settings`, { headers })
      .then(res => {
        setSettings(s => ({ ...s, ...res.data }));
      })
      .catch(() => {
        // Settings endpoint may return 404 before first update — use org data as fallback
        if (activeOrg) {
          setSettings(s => ({ ...s, name: activeOrg.name || '' }));
        }
      });
  }, [activeOrg?.id]);

  const handleSave = async () => {
    if (!activeOrg?.id) return;
    setSaving(true);
    try {
      const res = await apiClient.patch(`/organizations/${activeOrg.id}/settings`, settings, { headers });
      toast.success('Settings Saved', 'Organization settings updated successfully.');
      if (res.data.name && setActiveOrg) {
        setActiveOrg({ ...activeOrg, name: res.data.name });
      }
    } catch (err: any) {
      toast.error('Error', err.response?.data?.detail || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!activeOrg?.id || !confirm(`Archive "${activeOrg.name}"? It will be hidden from the org switcher.`)) return;
    try {
      await apiClient.post(`/organizations/${activeOrg.id}/archive`, {}, { headers });
      toast.info('Archived', `"${activeOrg.name}" has been archived.`);
    } catch {
      toast.error('Error', 'Failed to archive organization.');
    }
  };

  const update = (key: keyof OrgSettings, value: string) =>
    setSettings(s => ({ ...s, [key]: value }));

  return (
    <div className="flex flex-col gap-8 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Building2 className="w-6 h-6 text-violet-400" />
          Organization Settings
        </h1>
        <p className="text-neutral-400 text-sm mt-1">
          Configure branding, defaults, and preferences for <span className="text-white font-medium">{activeOrg?.name}</span>
        </p>
      </div>

      {/* Basic Info */}
      <section className="flex flex-col gap-5">
        <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-white/10">
          <Building2 className="w-4 h-4 text-violet-400" />
          Basic Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <Input
              label="Organization Name"
              value={settings.name}
              onChange={e => update('name', e.target.value)}
              placeholder="Acme Corporation"
              leftIcon={<Building2 className="w-4 h-4" />}
            />
          </div>
          <Input
            label="Website"
            value={settings.website}
            onChange={e => update('website', e.target.value)}
            placeholder="https://company.com"
            leftIcon={<Globe className="w-4 h-4" />}
          />
          <Input
            label="Billing Email"
            type="email"
            value={settings.billing_email}
            onChange={e => update('billing_email', e.target.value)}
            placeholder="billing@company.com"
          />
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400">Industry</label>
            <select
              value={settings.industry}
              onChange={e => update('industry', e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 transition-colors"
            >
              {INDUSTRIES.map(i => (
                <option key={i} value={i} className="bg-neutral-900">{i || 'Select Industry'}</option>
              ))}
            </select>
          </div>
          <Input
            label="Logo URL"
            value={settings.logo_url}
            onChange={e => update('logo_url', e.target.value)}
            placeholder="https://cdn.company.com/logo.png"
          />
        </div>
      </section>

      {/* Branding */}
      <section className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-white/10">
          <Palette className="w-4 h-4 text-violet-400" />
          Branding & Localization
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400 flex items-center gap-2">
              <Palette className="w-3.5 h-3.5" />
              Brand Color
            </label>
            <div className="flex gap-3 items-center">
              <input
                type="color"
                value={settings.theme_color}
                onChange={e => update('theme_color', e.target.value)}
                className="w-10 h-10 rounded-lg cursor-pointer bg-transparent border-0 p-0"
              />
              <Input
                value={settings.theme_color}
                onChange={e => update('theme_color', e.target.value)}
                placeholder="#6d28d9"
                className="flex-1 font-mono"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              Timezone
            </label>
            <select
              value={settings.timezone}
              onChange={e => update('timezone', e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 transition-colors"
            >
              {TIMEZONES.map(tz => (
                <option key={tz} value={tz} className="bg-neutral-900">{tz}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400">Language</label>
            <select
              value={settings.language}
              onChange={e => update('language', e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 transition-colors"
            >
              <option value="en" className="bg-neutral-900">English</option>
              <option value="es" className="bg-neutral-900">Spanish</option>
              <option value="fr" className="bg-neutral-900">French</option>
              <option value="de" className="bg-neutral-900">German</option>
              <option value="pt" className="bg-neutral-900">Portuguese</option>
              <option value="ja" className="bg-neutral-900">Japanese</option>
              <option value="zh" className="bg-neutral-900">Chinese</option>
            </select>
          </div>
        </div>
      </section>

      {/* AI Defaults */}
      <section className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-white/10">
          <Cpu className="w-4 h-4 text-violet-400" />
          AI Defaults
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5" />
              Default AI Provider
            </label>
            <select
              value={settings.default_ai_provider}
              onChange={e => update('default_ai_provider', e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 transition-colors capitalize"
            >
              {AI_PROVIDERS.map(p => (
                <option key={p} value={p} className="bg-neutral-900 capitalize">
                  {p || 'System Default'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400 flex items-center gap-2">
              <Image className="w-3.5 h-3.5" />
              Default Image Provider
            </label>
            <select
              value={settings.default_image_provider}
              onChange={e => update('default_image_provider', e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 transition-colors capitalize"
            >
              {IMAGE_PROVIDERS.map(p => (
                <option key={p} value={p} className="bg-neutral-900 capitalize">
                  {p || 'System Default'}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <Input
              label="Default AI Model (e.g. gpt-4o, claude-3-5-sonnet)"
              value={settings.default_ai_model}
              onChange={e => update('default_ai_model', e.target.value)}
              placeholder="Leave empty to use provider default"
            />
          </div>
        </div>
      </section>

      {/* Save Button */}
      <Button
        id="save-org-settings-btn"
        variant="violet"
        isLoading={saving}
        onClick={handleSave}
        className="w-fit flex items-center gap-2"
      >
        <Save className="w-4 h-4" />
        Save Changes
      </Button>

      {/* Danger Zone */}
      <section className="flex flex-col gap-4 pt-4 border-t border-rose-500/20">
        <h2 className="text-sm font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          Danger Zone
        </h2>

        <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between gap-4">
          <div>
            <p className="text-white text-sm font-medium">Archive Organization</p>
            <p className="text-neutral-500 text-xs mt-0.5">
              Hide this organization from the switcher. Data is preserved.
            </p>
          </div>
          <Button
            className="border-rose-500/30 text-rose-400 hover:bg-rose-500/10 shrink-0"
            onClick={handleArchive}
          >
            <Archive className="w-4 h-4 mr-1.5" />
            Archive
          </Button>
        </div>

        <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between gap-4">
          <div>
            <p className="text-white text-sm font-medium">Transfer Ownership</p>
            <p className="text-neutral-500 text-xs mt-0.5">
              Transfer this organization to another admin or member.
            </p>
          </div>
          <Button
            className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 shrink-0"
            onClick={() => setShowTransferConfirm(v => !v)}
          >
            <ArrowRight className="w-4 h-4 mr-1.5" />
            Transfer
          </Button>
        </div>
      </section>
    </div>
  );
}
