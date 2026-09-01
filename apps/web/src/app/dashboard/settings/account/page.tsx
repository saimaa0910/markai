'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { accountLifecycleService } from '@/services/account-lifecycle.service';
import { apiClient } from '@/services/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { User, Mail, Shield, Upload, CheckCircle2, AlertTriangle, Trash2, Clock, Building } from 'lucide-react';
import { Card } from '@eaimos/ui';

export default function AccountSettingsPage() {
  const router = useRouter();
  const { user: currentUser, activeOrg } = useAuthStore();

  const [showDeactivateDialog, setShowDeactivateDialog] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [deactivateReason, setDeactivateReason] = React.useState('');
  const [deletionPassword, setDeletionPassword] = React.useState('');
  const [deletionConfirmation, setDeletionConfirmation] = React.useState('');
  const [processing, setProcessing] = React.useState(false);

  // Profile data
  const { data: userProfile, refetch: refetchProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const res = await apiClient.get('/users/me');
      return res.data;
    },
  });

  const [fullName, setFullName] = React.useState('');
  const [email, setEmail] = React.useState('');

  const avatarSeed = encodeURIComponent((fullName || 'User').trim());
  const fallbackAvatarUrl = `https://api.dicebear.com/7.x/initials/svg?seed=${avatarSeed}`;

  React.useEffect(() => {
    if (userProfile) {
      setFullName(userProfile.full_name || currentUser?.full_name || '');
      setEmail(userProfile.email || currentUser?.email || '');
    } else if (currentUser) {
      setFullName(currentUser.full_name || '');
      setEmail(currentUser.email || '');
    }
  }, [userProfile, currentUser]);

  const updateProfileMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch('/users/me', { full_name: fullName, email });
    },
    onSuccess: () => {
      refetchProfile();
      toast.success('Profile Saved', 'Your user profile details have been updated.');
    },
    onError: (err: any) => {
      toast.error('Update Failed', err.response?.data?.detail || err.message);
    }
  });

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await apiClient.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      refetchProfile();
      toast.success('Avatar Uploaded', 'Your profile photo has been refreshed.');
    } catch (err: any) {
      toast.error('Upload Failed', err.response?.data?.detail || err.message);
    }
  };

  const handleDeactivate = async () => {
    try {
      setProcessing(true);
      await accountLifecycleService.deactivateAccount({ reason: deactivateReason });
      toast.success('Account deactivated successfully');
      setShowDeactivateDialog(false);
      router.push('/auth/login?deactivated=true');
    } catch (error: any) {
      toast.error('Failed to deactivate account', error.message);
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
    } catch (error: any) {
      toast.error('Failed to schedule account deletion', error.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          Account & Profile <User className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-2">
          Manage your personal profile, email verification, organization memberships, and account lifecycle.
        </p>
      </div>

      {/* User Profile Card */}
      <Card className="glass p-6 border-white/5 flex flex-col gap-6">
        <div>
          <h2 className="font-bold text-lg text-white">Profile Details</h2>
          <p className="text-xs text-neutral-400 mt-1">Manage public profile identity and verified contact email.</p>
        </div>

        <div className="flex flex-col md:flex-row gap-8 items-start">
          <div className="flex flex-col items-center gap-3 shrink-0">
            <img 
              src={userProfile?.avatar || (currentUser as any)?.avatar || fallbackAvatarUrl}
              alt="Avatar" 
              className="w-20 h-20 rounded-full border border-violet-500/20 bg-neutral-900 object-cover"
            />
            <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 text-[11px] text-neutral-300 hover:text-white cursor-pointer transition-colors bg-neutral-950/60 font-semibold">
              <Upload className="w-3.5 h-3.5" /> Upload Photo
              <input type="file" className="hidden" accept="image/*" onChange={handleAvatarUpload} />
            </label>
          </div>

          <div className="flex-1 flex flex-col gap-4 max-w-md">
            <Input
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your full name"
            />

            <Input
              label="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@company.com"
            />

            <div className="flex items-center gap-4 text-xs text-neutral-400 mt-1">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Email Verified</span>
              </div>
              <div className="flex items-center gap-1.5 text-violet-400">
                <Shield className="w-4 h-4" />
                <span>Role: {currentUser?.role || userProfile?.role || 'Member'}</span>
              </div>
              {activeOrg && (
                <div className="flex items-center gap-1.5 text-neutral-300">
                  <Building className="w-4 h-4 text-neutral-400" />
                  <span>Tenant: {activeOrg.name}</span>
                </div>
              )}
            </div>

            <Button 
              variant="violet" 
              onClick={() => updateProfileMutation.mutate()}
              isLoading={updateProfileMutation.isPending}
              className="self-start mt-2 px-5 py-2 text-xs"
            >
              Save Profile
            </Button>
          </div>
        </div>
      </Card>

      {/* Account Status Card */}
      <Card className="glass p-6 border-white/5">
        <h2 className="text-lg font-semibold text-white mb-2">Account Status</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-white text-sm">Account Active</p>
            <p className="text-xs text-neutral-400">
              Your account is currently active and authenticated across all platform services.
            </p>
          </div>
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-semibold">
            Active
          </span>
        </div>
      </Card>

      {/* Deactivate Account Section */}
      <Card className="glass p-6 border-amber-500/20 bg-amber-500/[0.02]">
        <h2 className="text-lg font-semibold text-amber-300 mb-2 flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" /> Deactivate Account
        </h2>
        <p className="text-xs text-neutral-400 mb-4">
          Temporarily deactivate your account. You can reactivate anytime by logging back in.
        </p>
        <ul className="text-xs text-neutral-400 space-y-1 mb-4 ml-4 list-disc">
          <li>Your platform data, API keys, and workspace resources will be preserved</li>
          <li>You will be logged out of active sessions</li>
          <li>Reactivate instantly by signing in</li>
        </ul>
        <Button
          variant="outline"
          onClick={() => setShowDeactivateDialog(true)}
          className="border-amber-500/30 text-amber-300 hover:bg-amber-500/10 text-xs"
        >
          Deactivate Account
        </Button>
      </Card>

      {/* Delete Account Section */}
      <Card className="glass p-6 border-rose-500/20 bg-rose-500/[0.02]">
        <h2 className="text-lg font-semibold text-rose-400 mb-2 flex items-center gap-2">
          <Trash2 className="w-4 h-4 text-rose-400" /> Delete Account
        </h2>
        <p className="text-xs text-neutral-400 mb-4">
          Permanently delete your user account and all personal records. This action includes a 7-day grace period.
        </p>
        <ul className="text-xs text-neutral-400 space-y-1 mb-4 ml-4 list-disc">
          <li>7-day grace period to cancel deletion if initiated in error</li>
          <li>All personal documents, conversations, and custom settings will be removed</li>
          <li>Confirmation notification will be sent to your verified email</li>
        </ul>
        <Button
          variant="destructive"
          onClick={() => setShowDeleteDialog(true)}
          className="bg-rose-600 hover:bg-rose-700 text-white text-xs"
        >
          Delete Account
        </Button>
      </Card>

      {/* Deactivate Dialog */}
      <Dialog
        isOpen={showDeactivateDialog}
        onClose={() => setShowDeactivateDialog(false)}
        title="Deactivate Your Account?"
        description="Your account will be temporarily deactivated. You can reactivate anytime by logging in."
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-neutral-300 mb-2">
              Reason for deactivation (optional)
            </label>
            <textarea
              className="w-full bg-neutral-900 border border-white/10 rounded-lg p-3 text-xs text-white placeholder:text-neutral-600 focus:outline-none focus:border-violet-500"
              rows={3}
              value={deactivateReason}
              onChange={(e) => setDeactivateReason(e.target.value)}
              placeholder="Help us improve..."
            />
          </div>
          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowDeactivateDialog(false)}
              className="flex-1 text-xs"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeactivate}
              disabled={processing}
              className="flex-1 text-xs"
            >
              {processing ? 'Deactivating...' : 'Deactivate Account'}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        title="⚠️ Delete Your Account?"
        description="This action will schedule your account for permanent deletion after 7 days."
      >
        <div className="space-y-4">
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
            <h4 className="font-semibold text-rose-400 text-xs mb-1">Warning: 7-Day Grace Period</h4>
            <ul className="text-[11px] text-rose-300 space-y-0.5 ml-3 list-disc">
              <li>Your account will be deleted permanently after 7 days</li>
              <li>You can cancel anytime during this window</li>
            </ul>
          </div>

          <div>
            <label className="block text-xs font-medium text-neutral-300 mb-1">
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
            <label className="block text-xs font-medium text-neutral-300 mb-1">
              Type <code className="bg-neutral-800 text-rose-400 px-1.5 py-0.5 rounded font-mono">DELETE MY ACCOUNT</code> to confirm
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
              className="flex-1 text-xs"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRequestDeletion}
              disabled={processing || deletionConfirmation !== 'DELETE MY ACCOUNT' || !deletionPassword}
              className="flex-1 text-xs"
            >
              {processing ? 'Processing...' : 'Schedule Deletion'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}