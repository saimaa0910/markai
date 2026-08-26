'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { Card } from '@eaimos/ui';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { ThemeSwitcher } from '@/components/ui/theme-switcher';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Palette, Globe, Clock, Bell, Mail, Sliders, CheckCircle2, Moon, Sun } from 'lucide-react';

const LANGUAGES = [
  { value: 'en', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' },
  { value: 'ja', label: '日本語' },
  { value: 'zh', label: '中文' },
];

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo', 'Asia/Singapore', 'Australia/Sydney',
];

export default function PreferencesSettingsPage() {
  const { user } = useAuthStore();

  const { data: userProfile, refetch: refetchProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const res = await apiClient.get('/users/me');
      return res.data;
    },
  });

  const [language, setLanguage] = React.useState('en');
  const [timezone, setTimezone] = React.useState('UTC');
  const [notifyEmail, setNotifyEmail] = React.useState(true);
  const [notifyInApp, setNotifyInApp] = React.useState(true);
  const [notifySecurityAlerts, setNotifySecurityAlerts] = React.useState(true);
  const [notifyWeeklyDigest, setNotifyWeeklyDigest] = React.useState(false);
  const [compactDensity, setCompactDensity] = React.useState(false);
  const [codeEditorTheme, setCodeEditorTheme] = React.useState('dark-plus');

  React.useEffect(() => {
    if (userProfile?.preferences) {
      const p = userProfile.preferences;
      setLanguage(p.language || 'en');
      setTimezone(p.timezone || 'UTC');
      setNotifyEmail(p.notify_email !== false);
      setNotifyInApp(p.notify_in_app !== false);
      setNotifySecurityAlerts(p.notify_security_alerts !== false);
      setNotifyWeeklyDigest(p.notify_weekly_digest === true);
      setCompactDensity(p.compact_density === true);
      setCodeEditorTheme(p.code_editor_theme || 'dark-plus');
    }
  }, [userProfile]);

  const updatePreferencesMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch('/users/me/preferences', {
        language,
        timezone,
        notify_email: notifyEmail,
        notify_in_app: notifyInApp,
        notify_security_alerts: notifySecurityAlerts,
        notify_weekly_digest: notifyWeeklyDigest,
        compact_density: compactDensity,
        code_editor_theme: codeEditorTheme,
      });
    },
    onSuccess: () => {
      refetchProfile();
      toast.success('Preferences Saved', 'Your user preferences have been updated.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.response?.data?.detail || err.message);
    }
  });

  return (
    <div className="space-y-6 max-w-4xl pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          User Preferences <Palette className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-2">
          Personalize your appearance theme, notification delivery, language, and workspace formatting.
        </p>
      </div>

      {/* 1. Appearance */}
      <Card className="glass p-6 border-white/5 space-y-4">
        <div className="flex items-center gap-2">
          <Palette className="w-4 h-4 text-violet-400" />
          <h2 className="text-base font-bold text-white">Appearance & Theme</h2>
        </div>
        <p className="text-xs text-neutral-400">
          Select your visual theme interface and display density.
        </p>

        <div className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg">
          <div>
            <span className="text-xs font-semibold text-white block">Theme Mode</span>
            <span className="text-[11px] text-neutral-400">Dark mode is optimized for high-contrast enterprise work</span>
          </div>
          <ThemeSwitcher variant="dropdown" />
        </div>

        <div className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg">
          <div>
            <span className="text-xs font-semibold text-white block">Compact Density</span>
            <span className="text-[11px] text-neutral-400">Reduce table row padding and whitespace</span>
          </div>
          <input
            type="checkbox"
            checked={compactDensity}
            onChange={(e) => setCompactDensity(e.target.checked)}
            className="w-4 h-4 rounded border-white/20 bg-neutral-900 text-violet-600 focus:ring-violet-500 cursor-pointer"
          />
        </div>
      </Card>

      {/* 2. Language & Timezone */}
      <Card className="glass p-6 border-white/5 space-y-4">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-violet-400" />
          <h2 className="text-base font-bold text-white">Language & Time Zone</h2>
        </div>
        <p className="text-xs text-neutral-400">
          Configure localization formats for timestamps, dates, and number outputs.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-neutral-300 mb-1">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500 cursor-pointer"
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-neutral-300 mb-1">Time Zone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full bg-neutral-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-violet-500 cursor-pointer"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* 3. Notification Preferences */}
      <Card className="glass p-6 border-white/5 space-y-4">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-violet-400" />
          <h2 className="text-base font-bold text-white">Notifications & Alerts</h2>
        </div>
        <p className="text-xs text-neutral-400">
          Choose where and when you receive automated updates.
        </p>

        <div className="space-y-3">
          <label className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg cursor-pointer">
            <div>
              <span className="text-xs font-semibold text-white block">Email Notifications</span>
              <span className="text-[11px] text-neutral-400">Receive campaign updates, agent completions, and export links</span>
            </div>
            <input
              type="checkbox"
              checked={notifyEmail}
              onChange={(e) => setNotifyEmail(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-neutral-900 text-violet-600 focus:ring-violet-500"
            />
          </label>

          <label className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg cursor-pointer">
            <div>
              <span className="text-xs font-semibold text-white block">In-App Notification Center</span>
              <span className="text-[11px] text-neutral-400">Show floating bell drawer alerts and push toasts</span>
            </div>
            <input
              type="checkbox"
              checked={notifyInApp}
              onChange={(e) => setNotifyInApp(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-neutral-900 text-violet-600 focus:ring-violet-500"
            />
          </label>

          <label className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg cursor-pointer">
            <div>
              <span className="text-xs font-semibold text-white block">Security & Login Alerts</span>
              <span className="text-[11px] text-neutral-400">Immediate email notifications for new device logins</span>
            </div>
            <input
              type="checkbox"
              checked={notifySecurityAlerts}
              onChange={(e) => setNotifySecurityAlerts(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-neutral-900 text-violet-600 focus:ring-violet-500"
            />
          </label>

          <label className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg cursor-pointer">
            <div>
              <span className="text-xs font-semibold text-white block">Weekly Summary Digest</span>
              <span className="text-[11px] text-neutral-400">Aggregated AI token consumption and ROI digest</span>
            </div>
            <input
              type="checkbox"
              checked={notifyWeeklyDigest}
              onChange={(e) => setNotifyWeeklyDigest(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-neutral-900 text-violet-600 focus:ring-violet-500"
            />
          </label>
        </div>
      </Card>

      {/* Save Button */}
      <div className="pt-2">
        <Button
          variant="violet"
          onClick={() => updatePreferencesMutation.mutate()}
          isLoading={updatePreferencesMutation.isPending}
          className="px-6 py-2 text-xs font-semibold"
        >
          Save All Preferences
        </Button>
      </div>
    </div>
  );
}
