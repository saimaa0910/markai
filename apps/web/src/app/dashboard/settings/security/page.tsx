'use client';

import * as React from 'react';
import { SessionsList } from './components/SessionsList';
import { TrustedDevices } from './components/TrustedDevices';
import { MFARecovery } from './components/MFARecovery';
import { AuditLogs } from './components/AuditLogs';
import { Card } from '@eaimos/ui';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useMutation } from '@tanstack/react-query';
import { Shield, Key, Lock, Laptop, Smartphone, FileText, CheckCircle2 } from 'lucide-react';

export default function SecuritySettingsPage() {
  const [activeTab, setActiveTab] = React.useState<'password' | 'sessions' | 'devices' | 'mfa' | 'audit'>('password');

  // Password mutation
  const [oldPassword, setOldPassword] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');

  const changePasswordMutation = useMutation({
    mutationFn: async () => {
      if (newPassword !== confirmPassword) {
        throw new Error('New passwords do not match');
      }
      if (newPassword.length < 8) {
        throw new Error('Password must be at least 8 characters long');
      }
      return apiClient.post(`/auth/password-change?old_password=${encodeURIComponent(oldPassword)}&new_password=${encodeURIComponent(newPassword)}`);
    },
    onSuccess: () => {
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Password Updated', 'Your security password has been changed successfully.');
    },
    onError: (err: any) => {
      toast.error('Password Change Failed', err.response?.data?.detail || err.message);
    }
  });

  const tabs = [
    { id: 'password', label: 'Password & Credentials', icon: Lock },
    { id: 'sessions', label: 'Active Sessions', icon: Key },
    { id: 'devices', label: 'Trusted Devices', icon: Laptop },
    { id: 'mfa', label: 'MFA Recovery Codes', icon: Shield },
    { id: 'audit', label: 'Security Activity Log', icon: FileText },
  ];

  return (
    <div className="space-y-6 max-w-4xl pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          Security & Passwords <Shield className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-2">
          Manage your login password, active authentication sessions, trusted hardware, and multi-factor recovery codes.
        </p>
      </div>

      {/* Tabs Switcher */}
      <div className="flex gap-2 border-b border-white/10 pb-2 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-violet-600/20 text-violet-300 border border-violet-500/30'
                  : 'text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-violet-400' : 'text-neutral-500'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="mt-6">
        {activeTab === 'password' && (
          <div className="flex flex-col gap-6">
            <Card className="glass p-6 border-white/5 flex flex-col gap-6">
              <div>
                <h3 className="font-bold text-base text-white flex items-center gap-2">
                  <Lock className="w-4 h-4 text-violet-400" /> Change Password
                </h3>
                <p className="text-xs text-neutral-400 mt-1">
                  Ensure your new password uses at least 8 characters with a combination of uppercase, numbers, and special symbols.
                </p>
              </div>

              <div className="flex flex-col gap-4 max-w-md">
                <Input
                  label="Current Password"
                  type="password"
                  placeholder="••••••••"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                />

                <Input
                  label="New Password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />

                <Input
                  label="Confirm New Password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />

                <Button 
                  variant="violet"
                  onClick={() => changePasswordMutation.mutate()}
                  isLoading={changePasswordMutation.isPending}
                  disabled={!oldPassword || !newPassword || !confirmPassword}
                  className="self-start mt-2 px-5 py-2 text-xs"
                >
                  Update Password
                </Button>
              </div>
            </Card>

            <Card className="glass p-6 border-white/5">
              <h3 className="font-bold text-base text-white mb-1">Two-Factor Authentication (2FA)</h3>
              <p className="text-xs text-neutral-400 mb-4">
                Add an extra layer of protection to your EAIMOS account during sign in.
              </p>
              <div className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                <div className="flex items-center gap-2 text-xs text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>MFA / Recovery protection enabled</span>
                </div>
                <Button 
                  variant="outline" 
                  onClick={() => setActiveTab('mfa')}
                  className="text-xs border-white/10"
                >
                  Manage Recovery Codes
                </Button>
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'sessions' && <SessionsList />}
        {activeTab === 'devices' && <TrustedDevices />}
        {activeTab === 'mfa' && <MFARecovery />}
        {activeTab === 'audit' && <AuditLogs />}
      </div>
    </div>
  );
}
