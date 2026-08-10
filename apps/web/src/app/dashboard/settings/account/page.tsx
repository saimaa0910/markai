'use client';

import { useState } from 'react';
import { accountLifecycleService } from '@/services/account-lifecycle.service';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { useRouter } from 'next/navigation';

export default function AccountSettingsPage() {
  const router = useRouter();
  const [showDeactivateDialog, setShowDeactivateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deactivateReason, setDeactivateReason] = useState('');
  const [deletionPassword, setDeletionPassword] = useState('');
  const [deletionConfirmation, setDeletionConfirmation] = useState('');
  const [processing, setProcessing] = useState(false);

  const handleDeactivate = async () => {
    try {
      setProcessing(true);
      await accountLifecycleService.deactivateAccount({ reason: deactivateReason });
      toast.success('Account deactivated successfully');
      setShowDeactivateDialog(false);
      // Logout user
      router.push('/auth/login?deactivated=true');
    } catch (error) {
      toast.error('Failed to deactivate account');
      console.error(error);
    } finally {
      setProcessing(false);
    }
  };

  const handleRequestDeletion = async () => {
    if (deletionConfirmation !== 'DELETE MY ACCOUNT') {
      toast.error('Please type the confirmation text exactly');
      return;
    }

    try {
      setProcessing(true);
      await accountLifecycleService.requestAccountDeletion({
        password: deletionPassword,
        confirmation_text: deletionConfirmation
      });
      toast.success('Account deletion scheduled. You have 7 days to cancel.');
      setShowDeleteDialog(false);
      router.push('/auth/login?deletion_scheduled=true');
    } catch (error) {
      toast.error('Failed to schedule account deletion');
      console.error(error);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account status and preferences
        </p>
      </div>

      {/* Account Status Section */}
      <div className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Account Status</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Account Active</p>
              <p className="text-sm text-muted-foreground">
                Your account is currently active and fully functional
              </p>
            </div>
            <div className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm font-medium">
              ✅ Active
            </div>
          </div>
        </div>
      </div>

      {/* Deactivate Account Section */}
      <div className="border border-yellow-300 dark:border-yellow-800 rounded-lg p-6 bg-yellow-50 dark:bg-yellow-900/20">
        <h2 className="text-xl font-semibold mb-2">Deactivate Account</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Temporarily deactivate your account. You can reactivate it anytime by logging in.
        </p>
        <ul className="text-sm text-muted-foreground space-y-1 mb-4 ml-4">
          <li>• Your data will be preserved</li>
          <li>• You will be logged out of all devices</li>
          <li>• Your profile will be hidden</li>
          <li>• You can reactivate anytime</li>
        </ul>
        <Button
          variant="outline"
          onClick={() => setShowDeactivateDialog(true)}
        >
          Deactivate Account
        </Button>
      </div>

      {/* Delete Account Section */}
      <div className="border border-red-300 dark:border-red-800 rounded-lg p-6 bg-red-50 dark:bg-red-900/20">
        <h2 className="text-xl font-semibold mb-2 text-red-700 dark:text-red-300">Delete Account</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Permanently delete your account and all associated data. This action cannot be undone after the 7-day grace period.
        </p>
        <ul className="text-sm text-muted-foreground space-y-1 mb-4 ml-4">
          <li>• 7-day grace period to cancel</li>
          <li>• All data will be permanently deleted</li>
          <li>• Cannot be recovered after grace period</li>
          <li>• You will receive email confirmation</li>
        </ul>
        <Button
          variant="destructive"
          onClick={() => setShowDeleteDialog(true)}
        >
          Delete Account
        </Button>
      </div>

      {/* Deactivate Dialog */}
      {showDeactivateDialog && (
        <Dialog
          open={showDeactivateDialog}
          onClose={() => setShowDeactivateDialog(false)}
          title="Deactivate Your Account?"
          description="Your account will be temporarily deactivated. You can reactivate it by logging in."
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Reason for deactivation (optional)
              </label>
              <textarea
                className="w-full border rounded-lg p-3 text-sm"
                rows={3}
                value={deactivateReason}
                onChange={(e) => setDeactivateReason(e.target.value)}
                placeholder="Help us improve by telling us why..."
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowDeactivateDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeactivate}
                disabled={processing}
                className="flex-1"
              >
                {processing ? 'Deactivating...' : 'Deactivate Account'}
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Delete Dialog */}
      {showDeleteDialog && (
        <Dialog
          open={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          title="⚠️ Delete Your Account?"
          description="This action will schedule your account for permanent deletion after 7 days."
          size="lg"
        >
          <div className="space-y-4">
            <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
              <h4 className="font-semibold text-red-700 dark:text-red-300 mb-2">Warning: This is permanent!</h4>
              <ul className="text-sm text-red-600 dark:text-red-400 space-y-1 ml-4">
                <li>• Your account will be deleted after 7 days</li>
                <li>• All your data will be permanently lost</li>
                <li>• This cannot be undone after the grace period</li>
                <li>• You can cancel within 7 days</li>
              </ul>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Confirm your password
              </label>
              <Input
                type="password"
                value={deletionPassword}
                onChange={(e) => setDeletionPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Type <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">DELETE MY ACCOUNT</code> to confirm
              </label>
              <Input
                value={deletionConfirmation}
                onChange={(e) => setDeletionConfirmation(e.target.value)}
                placeholder="DELETE MY ACCOUNT"
              />
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowDeleteDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleRequestDeletion}
                disabled={processing || deletionConfirmation !== 'DELETE MY ACCOUNT' || !deletionPassword}
                className="flex-1"
              >
                {processing ? 'Processing...' : 'Schedule Deletion'}
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}
