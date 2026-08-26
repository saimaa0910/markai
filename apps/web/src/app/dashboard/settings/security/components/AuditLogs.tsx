'use client';

import { useEffect, useState } from 'react';
import { securityService, AuditLog } from '@/services/security.service';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingOverlay } from '@/components/ui/loading-overlay';
import { EmptyState } from '@/components/ui/empty-state';

const EVENT_ICONS: Record<string, string> = {
  login: '🔑',
  logout: '🚪',
  password_change: '🔐',
  mfa_enabled: '✅',
  mfa_disabled: '❌',
  device_trusted: '📱',
  session_revoked: '🚫',
  account_deactivated: '⚠️',
  default: '📝'
};

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    loadLogs();
  }, [page]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await securityService.getAuditLogs({ page, page_size: pageSize });
      setLogs(data.logs);
      setTotal(data.total);
    } catch (error) {
      console.error(error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading && logs.length === 0) {
    return <LoadingOverlay />;
  }

  if (logs.length === 0) {
    return (
      <EmptyState
        title="No Activity Logs"
        description="Your security activity log is empty"
        icon="📋"
      />
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Security Activity Log</h2>
        <p className="text-sm text-muted-foreground">
          View your recent security-related activities
        </p>
      </div>

      <div className="space-y-2">
        {logs.map((log) => (
          <div
            key={log.id}
            className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">
                {EVENT_ICONS[log.event_type] || EVENT_ICONS.default}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium">{log.description}</h3>
                  <Badge variant="neutral">{log.event_category}</Badge>
                </div>
                <div className="text-sm text-muted-foreground space-y-0.5">
                  <p>🕒 {new Date(log.created_at).toLocaleString()}</p>
                  {log.ip_address && <p>🌍 {log.ip_address} {log.location && `(${log.location})`}</p>}
                  {log.user_agent && <p>🌐 {log.user_agent}</p>}
                </div>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                      View details
                    </summary>
                    <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto">
                      {JSON.stringify(log.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages} ({total} total events)
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || loading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
