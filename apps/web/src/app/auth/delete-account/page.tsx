'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { AlertTriangle, Trash2, Shield, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';

const deleteSchema = z.object({
  reason: z.string().optional(),
  confirm_text: z.string().refine(v => v === 'DELETE', {
    message: 'Please type DELETE to confirm',
  }),
});

type DeleteValues = z.infer<typeof deleteSchema>;

export default function DeleteAccountPage() {
  const router = useRouter();
  const { accessToken, logout } = useAuthStore();
  const [deleting, setDeleting] = React.useState(false);
  const [scheduled, setScheduled] = React.useState<string | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<DeleteValues>({
    resolver: zodResolver(deleteSchema),
  });

  const onDelete = async (data: DeleteValues) => {
    setDeleting(true);
    try {
      const res = await apiClient.post('/users/me/delete', {
        confirm: true,
        reason: data.reason || null,
      }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      setScheduled(res.data.deletion_scheduled_at);
      toast.info(
        'Account Deletion Scheduled',
        'Your account will be permanently deleted in 7 days. You can restore it before then.'
      );
      // Logout — account is now disabled
      logout();
      setTimeout(() => router.push('/auth/login'), 3000);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to schedule deletion.';
      toast.error('Error', msg);
    } finally {
      setDeleting(false);
    }
  };

  if (scheduled) {
    return (
      <div className="flex flex-col items-center gap-6 py-4">
        <div className="w-16 h-16 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
          <Clock className="w-8 h-8 text-amber-400" />
        </div>
        <div className="text-center flex flex-col gap-2">
          <h2 className="text-xl font-bold text-white">Deletion Scheduled</h2>
          <p className="text-neutral-400 text-sm">
            Your account will be permanently deleted on{' '}
            <span className="text-amber-400 font-semibold">
              {new Date(scheduled).toLocaleDateString('en-US', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
              })}
            </span>
          </p>
          <p className="text-neutral-500 text-xs">Signing you out now...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center mb-1">
          <Trash2 className="w-6 h-6 text-rose-400" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Delete Account</h1>
        <p className="text-sm text-neutral-400">
          This will permanently delete your EAIMOS account and all associated data.
        </p>
      </div>

      {/* Warning */}
      <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex flex-col gap-3">
        <div className="flex gap-2 items-center">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span className="text-rose-400 font-semibold text-sm">This action cannot be undone</span>
        </div>
        <ul className="text-rose-400/80 text-xs space-y-1 list-disc list-inside">
          <li>Your account will be <strong>immediately deactivated</strong></li>
          <li>All organizations you own may be <strong>archived</strong></li>
          <li>All your data will be <strong>permanently erased after 7 days</strong></li>
          <li>Your email will be freed for use on a new account</li>
        </ul>
      </div>

      {/* Recovery Window Notice */}
      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 flex gap-3 items-start">
        <Shield className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-400">
          <p className="font-semibold mb-0.5">7-Day Recovery Window</p>
          <p className="text-blue-400/70">
            You have 7 days to restore your account before permanent deletion.
            You'll receive an email with a restore link.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onDelete)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-neutral-400">
            Reason for leaving (optional)
          </label>
          <textarea
            {...register('reason')}
            rows={3}
            placeholder="Tell us why you're leaving..."
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2
                       text-white text-sm placeholder:text-neutral-600
                       focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20
                       resize-none transition-colors"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-neutral-400">
            Type <span className="text-rose-400 font-bold font-mono">DELETE</span> to confirm
          </label>
          <Input
            type="text"
            placeholder="DELETE"
            error={errors.confirm_text?.message}
            className="font-mono"
            {...register('confirm_text')}
          />
        </div>

        <Button
          id="confirm-delete-btn"
          type="submit"
          isLoading={deleting}
          className="w-full bg-rose-600 hover:bg-rose-500 text-white border-rose-500 mt-1"
        >
          Schedule Account Deletion
        </Button>
      </form>

      <button
        onClick={() => router.back()}
        className="text-neutral-500 hover:text-neutral-300 text-xs text-center transition-colors"
      >
        ← Cancel, keep my account
      </button>
    </div>
  );
}
