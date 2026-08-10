'use client';

import { useState } from 'react';
import { Tabs } from '@/components/ui/tabs';
import { SessionsList } from './components/SessionsList';
import { TrustedDevices } from './components/TrustedDevices';
import { MFARecovery } from './components/MFARecovery';
import { AuditLogs } from './components/AuditLogs';

export default function SecuritySettingsPage() {
  const [activeTab, setActiveTab] = useState('sessions');

  const tabs = [
    { id: 'sessions', label: 'Active Sessions', icon: '🔐' },
    { id: 'devices', label: 'Trusted Devices', icon: '📱' },
    { id: 'mfa', label: 'MFA Recovery', icon: '🔑' },
    { id: 'audit', label: 'Activity Log', icon: '📋' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Security Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your sessions, trusted devices, and security settings
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex space-x-4 border-b">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {activeTab === 'sessions' && <SessionsList />}
          {activeTab === 'devices' && <TrustedDevices />}
          {activeTab === 'mfa' && <MFARecovery />}
          {activeTab === 'audit' && <AuditLogs />}
        </div>
      </Tabs>
    </div>
  );
}
