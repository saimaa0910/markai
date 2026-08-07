'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { toast } from '@/components/ui/toast';
import {
  Activity, Search, Filter, AlertTriangle, Shield, Info,
  ChevronLeft, ChevronRight, Clock, User, Eye,
} from 'lucide-react';

interface AuditLog {
  id: string;
  action: string;
  actor_email: string | null;
  actor_ip: string | null;
  entity_type: string;
  entity_id: string | null;
  description: string | null;
  risk_level: string;
  created_at: string;
}

const RISK_STYLES: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  medium: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  high: 'text-rose-400 bg-rose-400/10 border-rose-400/20',
  critical: 'text-rose-300 bg-rose-600/20 border-rose-400/30',
};

const RISK_ICONS: Record<string, React.ReactNode> = {
  low: <Info className="w-3 h-3" />,
  medium: <AlertTriangle className="w-3 h-3" />,
  high: <AlertTriangle className="w-3 h-3" />,
  critical: <Shield className="w-3 h-3" />,
};

function formatAction(action: string) {
  return action.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(diff / 86400000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  if (h < 24) return `${h}h ago`;
  return `${d}d ago`;
}

const PAGE_SIZE = 25;

export default function AuditLogPage() {
  const { accessToken, activeOrg } = useAuthStore();
  const [logs, setLogs] = React.useState<AuditLog[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [total, setTotal] = React.useState(0);
  const [page, setPage] = React.useState(0);
  const [search, setSearch] = React.useState('');
  const [riskFilter, setRiskFilter] = React.useState('');
  const [stats, setStats] = React.useState<any>(null);
  const [expandedLog, setExpandedLog] = React.useState<string | null>(null);

  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'X-Organization-Id': activeOrg?.id || '',
  };

  const fetchLogs = React.useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { skip: page * PAGE_SIZE, limit: PAGE_SIZE };
      if (search) params.action = search;
      if (riskFilter) params.risk_level = riskFilter;

      const res = await apiClient.get('/audit/logs', { headers, params });
      setLogs(res.data || []);
    } catch {
      toast.error('Error', 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrg, page, search, riskFilter]);

  const fetchStats = React.useCallback(async () => {
    try {
      const res = await apiClient.get('/audit/stats', { headers });
      setStats(res.data);
    } catch {}
  }, [accessToken, activeOrg]);

  React.useEffect(() => {
    fetchLogs();
    fetchStats();
  }, [fetchLogs, fetchStats]);

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Activity className="w-6 h-6 text-violet-400" />
          Audit Log
        </h1>
        <p className="text-neutral-400 text-sm mt-1">
          Track all security events and system actions in <span className="text-white font-medium">{activeOrg?.name}</span>
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Events', value: stats.total, color: 'text-white' },
            { label: 'High Risk (24h)', value: stats.recent_high_risk, color: 'text-rose-400' },
            { label: 'Low Risk', value: stats.by_risk?.low || 0, color: 'text-emerald-400' },
            { label: 'Critical', value: stats.by_risk?.critical || 0, color: 'text-rose-300' },
          ].map(s => (
            <div key={s.label} className="p-4 rounded-xl bg-white/[0.03] border border-white/10">
              <p className="text-neutral-500 text-xs mb-1">{s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value ?? 0}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 pointer-events-none" />
          <input
            type="text"
            placeholder="Search actions..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0); }}
            className="w-full pl-9 pr-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white
                       placeholder:text-neutral-600 focus:outline-none focus:border-violet-500/50 transition-colors"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 pointer-events-none" />
          <select
            value={riskFilter}
            onChange={e => { setRiskFilter(e.target.value); setPage(0); }}
            className="pl-9 pr-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white
                       focus:outline-none focus:border-violet-500/50 transition-colors appearance-none min-w-[140px]"
          >
            <option value="" className="bg-neutral-900">All Risk Levels</option>
            <option value="low" className="bg-neutral-900">Low</option>
            <option value="medium" className="bg-neutral-900">Medium</option>
            <option value="high" className="bg-neutral-900">High</option>
            <option value="critical" className="bg-neutral-900">Critical</option>
          </select>
        </div>
        <button
          onClick={() => { fetchLogs(); fetchStats(); }}
          className="px-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-sm text-neutral-400
                     hover:text-white hover:border-white/20 transition-all flex items-center gap-2"
        >
          <Activity className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Log Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="rounded-xl border border-white/10 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.02]">
                <th className="text-left px-4 py-3 text-neutral-400 font-medium">Event</th>
                <th className="text-left px-4 py-3 text-neutral-400 font-medium hidden md:table-cell">Actor</th>
                <th className="text-left px-4 py-3 text-neutral-400 font-medium">Risk</th>
                <th className="text-left px-4 py-3 text-neutral-400 font-medium hidden lg:table-cell">Time</th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map(log => (
                <React.Fragment key={log.id}>
                  <tr
                    className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="text-white font-medium text-sm">{formatAction(log.action)}</span>
                        {log.description && (
                          <p className="text-neutral-500 text-xs mt-0.5 truncate max-w-[300px]">{log.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <div className="flex items-center gap-2">
                        <User className="w-3.5 h-3.5 text-neutral-600" />
                        <span className="text-neutral-400 text-xs">{log.actor_email || 'System'}</span>
                      </div>
                      {log.actor_ip && (
                        <p className="text-neutral-600 text-xs mt-0.5">{log.actor_ip}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border ${RISK_STYLES[log.risk_level] || RISK_STYLES.low}`}>
                        {RISK_ICONS[log.risk_level]}
                        {log.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <div className="flex items-center gap-1.5 text-neutral-500 text-xs">
                        <Clock className="w-3.5 h-3.5" />
                        {timeAgo(log.created_at)}
                      </div>
                      <p className="text-neutral-700 text-xs mt-0.5">
                        {new Date(log.created_at).toLocaleDateString()}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <Eye className={`w-4 h-4 transition-colors ${expandedLog === log.id ? 'text-violet-400' : 'text-neutral-700'}`} />
                    </td>
                  </tr>
                  {expandedLog === log.id && (
                    <tr className="bg-violet-500/5">
                      <td colSpan={5} className="px-4 py-3">
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <span className="text-neutral-500">Event ID:</span>
                            <span className="text-neutral-300 ml-2 font-mono">{log.id}</span>
                          </div>
                          <div>
                            <span className="text-neutral-500">Entity:</span>
                            <span className="text-neutral-300 ml-2">
                              {log.entity_type} {log.entity_id ? `(${log.entity_id.slice(0, 8)}...)` : ''}
                            </span>
                          </div>
                          <div>
                            <span className="text-neutral-500">Timestamp:</span>
                            <span className="text-neutral-300 ml-2">
                              {new Date(log.created_at).toLocaleString()}
                            </span>
                          </div>
                          {log.actor_ip && (
                            <div>
                              <span className="text-neutral-500">IP Address:</span>
                              <span className="text-neutral-300 ml-2 font-mono">{log.actor_ip}</span>
                            </div>
                          )}
                          {log.description && (
                            <div className="col-span-2">
                              <span className="text-neutral-500">Details:</span>
                              <span className="text-neutral-300 ml-2">{log.description}</span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center">
                    <Activity className="w-8 h-8 mx-auto mb-3 text-neutral-700" />
                    <p className="text-neutral-500 text-sm">No audit logs found</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {logs.length > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
              <p className="text-neutral-500 text-xs">
                Page {page + 1} · {PAGE_SIZE} per page
              </p>
              <div className="flex gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={logs.length < PAGE_SIZE}
                  onClick={() => setPage(p => p + 1)}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
