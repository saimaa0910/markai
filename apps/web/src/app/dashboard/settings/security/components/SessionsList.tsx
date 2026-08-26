'use client';

import { useEffect, useState } from 'react';
import { authSessionService, Session } from '@/services/auth-session.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { LoadingOverlay } from '@/components/ui/loading-overlay';

export function SessionsList() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [showRevokeAllDialog, setShowRevokeAllDialog] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await authSessionService.listSessions();
      setSessions(data.sessions);
    } catch (error) {
      toast.error('Failed to load sessions');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      setRevoking(sessionId);
      await authSessionService.revokeSession(sessionId);
      toast.success('Session revoked successfully');
      await loadSessions();
    } catch (error) {
      toast.error('Failed to revoke session');
      console.error(error);
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAllOtherSessions = async () => {
    try {
      await authSessionService.revokeAllOtherSessions();
      toast.success('All other sessions revoked');
      setShowRevokeAllDialog(false);
      await loadSessions();
    } catch (error) {
      toast.error('Failed to revoke sessions');
      console.error(error);
    }
  };

  if (loading) {
    return <LoadingOverlay />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">Active Sessions</h2>
          <p className="text-sm text-muted-foreground">
            Manage your active login sessions across devices
          </p>
        </div>
        {sessions.length > 1 && (
          <Button
            variant="destructive"
            onClick={() => setShowRevokeAllDialog(true)}
          >
            Revoke All Other Sessions
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {sessions.map((session) => (
          <div
            key={session.id}
            className="border rounded-lg p-4 flex justify-between items-start"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-medium">
                  {session.device_name || `${session.device_type || 'Unknown'} Device`}
                </h3>
                {session.is_current && (
                  <Badge variant="neutral">Current Session</Badge>
                )}
              </div>
              
              <div className="text-sm text-muted-foreground space-y-1">
                {session.browser && (
                  <p>🌐 {session.browser}</p>
                )}
                {session.device_os && (
                  <p>💻 {session.device_os}</p>
                )}
                {session.ip_address && (
                  <p>🌍 {session.ip_address} {session.location && `(${session.location})`}</p>
                )}
                <p>🕒 Last active: {new Date(session.last_active_at).toLocaleString()}</p>
                <p>📅 Created: {new Date(session.created_at).toLocaleString()}</p>
              </div>
            </div>

            {!session.is_current && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRevokeSession(session.id)}
                disabled={revoking === session.id}
              >
                {revoking === session.id ? 'Revoking...' : 'Revoke'}
              </Button>
            )}
          </div>
        ))}
      </div>

      {/* Revoke All Dialog */}
      {showRevokeAllDialog && (
        <Dialog
          isOpen={showRevokeAllDialog}
          onClose={() => setShowRevokeAllDialog(false)}
          title="Revoke All Other Sessions?"
          description="This will log you out from all other devices. Your current session will remain active."
        >
          <div className="flex gap-2 pt-4 justify-end">
            <Button
              variant="outline"
              onClick={() => setShowRevokeAllDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRevokeAllOtherSessions}
            >
              Revoke All
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}