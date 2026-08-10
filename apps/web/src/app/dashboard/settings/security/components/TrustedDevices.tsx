'use client';

import { useEffect, useState } from 'react';
import { securityService, TrustedDevice } from '@/services/security.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/toast';
import { LoadingOverlay } from '@/components/ui/loading-overlay';
import { EmptyState } from '@/components/ui/empty-state';

export function TrustedDevices() {
  const [devices, setDevices] = useState<TrustedDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      setLoading(true);
      const data = await securityService.listTrustedDevices();
      setDevices(data);
    } catch (error) {
      toast.error('Failed to load trusted devices');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      setRemoving(deviceId);
      await securityService.removeTrustedDevice(deviceId);
      toast.success('Device removed successfully');
      await loadDevices();
    } catch (error) {
      toast.error('Failed to remove device');
      console.error(error);
    } finally {
      setRemoving(null);
    }
  };

  if (loading) {
    return <LoadingOverlay />;
  }

  if (devices.length === 0) {
    return (
      <EmptyState
        title="No Trusted Devices"
        description="You don't have any trusted devices yet. Enable 'Trust this device' when logging in to skip MFA on trusted devices."
        icon="📱"
      />
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Trusted Devices</h2>
        <p className="text-sm text-muted-foreground">
          Devices you've trusted to skip MFA verification
        </p>
      </div>

      <div className="space-y-3">
        {devices.map((device) => (
          <div
            key={device.id}
            className="border rounded-lg p-4 flex justify-between items-start"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-medium">{device.device_name}</h3>
                {device.is_current && (
                  <Badge variant="success">Current Device</Badge>
                )}
              </div>
              
              <div className="text-sm text-muted-foreground space-y-1">
                <p>📱 {device.device_type}</p>
                {device.device_os && <p>💻 {device.device_os}</p>}
                {device.browser && <p>🌐 {device.browser}</p>}
                <p>🕒 Last used: {new Date(device.last_used_at).toLocaleString()}</p>
                <p>✅ Trusted since: {new Date(device.trusted_at).toLocaleString()}</p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRemoveDevice(device.id)}
              disabled={removing === device.id}
            >
              {removing === device.id ? 'Removing...' : 'Remove Trust'}
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <p className="text-sm text-yellow-800 dark:text-yellow-200">
          ⚠️ <strong>Security Note:</strong> Removing trust from a device will require MFA verification on next login.
        </p>
      </div>
    </div>
  );
}
