'use client';

import { useEffect, useState } from 'react';
import { accountLifecycleService, PrivacyDashboard, DataExportStatus } from '@/services/account-lifecycle.service';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { LoadingOverlay } from '@/components/ui/loading-overlay';
import { StatCard } from '@/components/ui/stat-card';

export default function PrivacySettingsPage() {
  const [dashboard, setDashboard] = useState<PrivacyDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');
  const [exporting, setExporting] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await accountLifecycleService.getPrivacyDashboard();
      setDashboard(data);
    } catch (error) {
      toast.error('Failed to load privacy dashboard');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestExport = async () => {
    try {
      setExporting(true);
      const exportData = await accountLifecycleService.requestDataExport({
        format: exportFormat,
        include_files: true
      });
      toast.success('Data export requested. You will be notified when it\'s ready.');
      setShowExportDialog(false);
      await loadDashboard();
    } catch (error) {
      toast.error('Failed to request data export');
      console.error(error);
    } finally {
      setExporting(false);
    }
  };

  const handleCancelDeletion = async () => {
    try {
      setCancelling(true);
      await accountLifecycleService.cancelAccountDeletion();
      toast.success('Account deletion cancelled successfully');
      await loadDashboard();
    } catch (error) {
      toast.error('Failed to cancel deletion');
      console.error(error);
    } finally {
      setCancelling(false);
    }
  };

  const handleDownloadExport = (exportData: DataExportStatus) => {
    if (exportData.download_url) {
      window.open(exportData.download_url, '_blank');
      toast.success('Download started');
    }
  };

  if (loading) {
    return <LoadingOverlay />;
  }

  if (!dashboard) {
    return <div>Error loading privacy dashboard</div>;
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Privacy & Data</h1>
        <p className="text-muted-foreground mt-2">
          Manage your data, privacy settings, and GDPR compliance
        </p>
      </div>

      {/* Deletion Warning Banner */}
      {dashboard.deletion_scheduled && (
        <div className="border-2 border-red-500 bg-red-50 dark:bg-red-900/30 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <span className="text-3xl">⚠️</span>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-700 dark:text-red-300 mb-2">
                Your account is scheduled for deletion
              </h3>
              <p className="text-sm text-red-600 dark:text-red-400 mb-4">
                Your account will be permanently deleted on{' '}
                {dashboard.deletion_scheduled_for && 
                  new Date(dashboard.deletion_scheduled_for).toLocaleDateString()}
                . You can cancel this deletion before that date.
              </p>
              {dashboard.can_cancel_deletion && (
                <Button
                  variant="destructive"
                  onClick={handleCancelDeletion}
                  disabled={cancelling}
                >
                  {cancelling ? 'Cancelling...' : 'Cancel Deletion'}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Privacy Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Active Sessions"
          value={dashboard.active_sessions_count.toString()}
          icon="🔐"
          description="Devices logged in"
        />
        <StatCard
          title="Trusted Devices"
          value={dashboard.trusted_devices_count.toString()}
          icon="📱"
          description="Devices with MFA skip"
        />
        <StatCard
          title="Data Retention"
          value={`${dashboard.data_retention_days} days`}
          icon="📅"
          description="Before auto-deletion"
        />
      </div>

      {/* Data Export Section */}
      <div className="border rounded-lg p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold mb-2">Export Your Data</h2>
            <p className="text-sm text-muted-foreground">
              Request a copy of all your data (GDPR Article 20 - Right to Data Portability)
            </p>
          </div>
          <Button onClick={() => setShowExportDialog(true)}>
            💾 Request Export
          </Button>
        </div>

        {/* Recent Exports */}
        {dashboard.recent_exports && dashboard.recent_exports.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold mb-3">Recent Data Exports</h3>
            <div className="space-y-2">
              {dashboard.recent_exports.map((exp) => (
                <div
                  key={exp.id}
                  className="flex justify-between items-center border rounded-lg p-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{exp.format.toUpperCase()}</span>
                      <Badge variant={exp.status === 'completed' ? 'success' : 'default'}>
                        {exp.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Requested: {new Date(exp.created_at).toLocaleString()}
                    </p>
                  </div>
                  {exp.status === 'completed' && exp.download_url && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadExport(exp)}
                    >
                      Download
                    </Button>
                  )}
                  {exp.status === 'processing' && (
                    <span className="text-sm text-muted-foreground">Processing...</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Privacy Information */}
      <div className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Your Privacy Rights</h2>
        <div className="space-y-3 text-sm">
          <div>
            <h4 className="font-medium mb-1">✅ Right to Access</h4>
            <p className="text-muted-foreground">You can request and download all your personal data at any time.</p>
          </div>
          <div>
            <h4 className="font-medium mb-1">✅ Right to Rectification</h4>
            <p className="text-muted-foreground">You can update and correct your personal information in account settings.</p>
          </div>
          <div>
            <h4 className="font-medium mb-1">✅ Right to Erasure</h4>
            <p className="text-muted-foreground">You can request permanent deletion of your account and all associated data.</p>
          </div>
          <div>
            <h4 className="font-medium mb-1">✅ Right to Data Portability</h4>
            <p className="text-muted-foreground">Export your data in machine-readable formats (JSON, CSV).</p>
          </div>
        </div>
      </div>

      {/* Export Dialog */}
      {showExportDialog && (
        <Dialog
          open={showExportDialog}
          onClose={() => setShowExportDialog(false)}
          title="Export Your Data"
          description="Choose a format for your data export"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-3">Export Format</label>
              <div className="space-y-2">
                <div
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    exportFormat === 'json'
                      ? 'border-primary bg-primary/10'
                      : 'hover:border-gray-300'
                  }`}
                  onClick={() => setExportFormat('json')}
                >
                  <div className="flex items-center">
                    <input
                      type="radio"
                      checked={exportFormat === 'json'}
                      onChange={() => setExportFormat('json')}
                      className="mr-3"
                    />
                    <div>
                      <p className="font-medium">JSON Format</p>
                      <p className="text-xs text-muted-foreground">
                        Complete data with full structure (recommended for developers)
                      </p>
                    </div>
                  </div>
                </div>
                <div
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    exportFormat === 'csv'
                      ? 'border-primary bg-primary/10'
                      : 'hover:border-gray-300'
                  }`}
                  onClick={() => setExportFormat('csv')}
                >
                  <div className="flex items-center">
                    <input
                      type="radio"
                      checked={exportFormat === 'csv'}
                      onChange={() => setExportFormat('csv')}
                      className="mr-3"
                    />
                    <div>
                      <p className="font-medium">CSV Format</p>
                      <p className="text-xs text-muted-foreground">
                        Spreadsheet-friendly format (opens in Excel/Google Sheets)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm">
              <p className="text-blue-800 dark:text-blue-200">
                💬 Processing typically takes 5-10 minutes. You'll receive an email when your export is ready.
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowExportDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleRequestExport}
                disabled={exporting}
                className="flex-1"
              >
                {exporting ? 'Requesting...' : 'Request Export'}
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}
