'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Users, Building2, TrendingUp, Activity as ActivityIcon } from 'lucide-react';
import CRMContactsPage from './contacts';
import CRMCompaniesPage from './companies';
import CRMLeadsPage from './leads';

type Tab = 'contacts' | 'companies' | 'leads';

export default function CRMDashboard() {
  const [activeTab, setActiveTab] = React.useState<Tab>('contacts');

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'contacts', label: 'Contacts', icon: Users },
    { id: 'companies', label: 'Companies', icon: Building2 },
    { id: 'leads', label: 'Leads & Opportunities', icon: TrendingUp },
  ];

  return (
    <div className="space-y-6">
      {/* Module Navigation Tabs */}
      <div className="flex border-b border-zinc-800 space-x-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors relative ${
                isActive
                  ? 'border-violet-500 text-white'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200 hover:border-zinc-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {isActive && (
                <motion.div
                  layoutId="activeTabUnderline"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-violet-500"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="pt-2">
        {activeTab === 'contacts' && <CRMContactsPage />}
        {activeTab === 'companies' && <CRMCompaniesPage />}
        {activeTab === 'leads' && <CRMLeadsPage />}
      </div>
    </div>
  );
}
