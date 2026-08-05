'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  Bell, Mail, MessageSquare, Shield, CheckCircle2, Check, Send, AlertTriangle, Info, Clock, Loader2, Sparkles, Filter,
} from 'lucide-react';
import { useNotificationsList, useMarkNotificationRead, useMarkAllNotificationsRead, useSendNotification } from '../queries';
import type { NotificationChannel, NotificationPriority } from '../types';

const PRIORITY_BADGES: Record<NotificationPriority, { bg: string; text: string }> = {
  LOW: { bg: 'bg-zinc-800', text: 'text-zinc-400' },
  MEDIUM: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
  HIGH: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
  URGENT: { bg: 'bg-red-500/10', text: 'text-red-400' },
};

export default function NotificationsPage() {
  const { data: notifications, isLoading, error } = useNotificationsList();
  const markReadMutation = useMarkNotificationRead();
  const markAllReadMutation = useMarkAllNotificationsRead();

  const [channelFilter, setChannelFilter] = React.useState<string>('ALL');

  const mockList = React.useMemo(() => {
    if (notifications && notifications.length > 0) return notifications;
    return [
      { id: '1', title: 'AI Agent Creative Draft Ready', message: 'Agent "Social Copywriter" generated 3 new variants for your approval.', channel: 'IN_APP' as NotificationChannel, priority: 'HIGH' as NotificationPriority, is_read: false, created_at: new Date().toISOString() },
      { id: '2', title: 'High Value Lead Logged', message: 'Sarah Jenkins (Acme Corp) was added to CRM with estimated value of $15,400.', channel: 'EMAIL' as NotificationChannel, priority: 'MEDIUM' as NotificationPriority, is_read: false, created_at: new Date(Date.now() - 3600000).toISOString() },
      { id: '3', title: 'Vector Knowledge Index Completed', message: 'Document "Q3 Strategy Architecture.pdf" successfully processed (14 chunks embedded).', channel: 'IN_APP' as NotificationChannel, priority: 'LOW' as NotificationPriority, is_read: true, created_at: new Date(Date.now() - 86400000).toISOString() },
    ];
  }, [notifications]);

  const filtered = React.useMemo(() => {
    if (channelFilter === 'ALL') return mockList;
    return mockList.filter(n => n.channel === channelFilter);
  }, [mockList, channelFilter]);

  const unreadCount = mockList.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-amber-400" /> Notifications & Dispatch Center
          </h1>
          <p className="text-sm text-zinc-500 mt-1">Real-time alert log across Email, SMS, Webhook, and In-App channels</p>
        </div>
        <button onClick={() => markAllReadMutation.mutate()} disabled={unreadCount === 0 || markAllReadMutation.isPending}
          className="px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 border border-zinc-700">
          <Check className="w-4 h-4 text-emerald-400" /> Mark All as Read
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-3">
        <div className="flex bg-zinc-900 border border-zinc-800 p-1 rounded-lg">
          {['ALL', 'IN_APP', 'EMAIL', 'SMS', 'PUSH'].map(ch => (
            <button key={ch} onClick={() => setChannelFilter(ch)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${channelFilter === ch ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>
              {ch.replace('_', ' ')}
            </button>
          ))}
        </div>
        {unreadCount > 0 && (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            {unreadCount} Unread Alerts
          </span>
        )}
      </div>

      {/* Notifications Feed */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 bg-zinc-900/60 border border-zinc-800 rounded-xl">
            <Loader2 className="w-6 h-6 text-amber-400 animate-spin" /><span className="ml-3 text-zinc-500 text-sm">Loading alerts...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-500">
            <Bell className="w-10 h-10 mb-3 opacity-40" /><p className="text-sm font-medium">No notifications in this channel</p>
          </div>
        ) : (
          filtered.map((item, i) => {
            const priorityBadge = PRIORITY_BADGES[item.priority] || PRIORITY_BADGES.LOW;
            return (
              <motion.div key={item.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                className={`bg-zinc-900/60 border ${item.is_read ? 'border-zinc-800/80 opacity-75' : 'border-amber-500/30 bg-amber-500/[0.02]'} rounded-xl p-5 flex items-start justify-between gap-4 group transition-colors`}>
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${item.is_read ? 'bg-zinc-800 text-zinc-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    <Bell className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase ${priorityBadge.bg} ${priorityBadge.text}`}>{item.priority}</span>
                      <span className="text-[10px] font-mono text-zinc-500 uppercase px-2 py-0.5 rounded bg-zinc-800">{item.channel}</span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">{item.message}</p>
                    <span className="text-[11px] text-zinc-600 mt-2 block flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>

                {!item.is_read && (
                  <button onClick={() => markReadMutation.mutate(item.id)} className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs font-medium transition-colors shrink-0">
                    Mark Read
                  </button>
                )}
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
