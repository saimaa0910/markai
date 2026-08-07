'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, RefreshCcw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';
import Link from 'next/link';

function RestoreAccountContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { accessToken } = useAuthStore();
  const [restoring, setRestoring] = React.useState(false);
  const [restored, setRestored] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleRestore = async () => {
    setRestoring(true);
    try {
      await apiClient.post('/users/me/restore', {}, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
      });
      setRestored(true);
      toast.success('Account Restored!', 'Your account is back. Welcome back to EAIMOS!');
      setTimeout(() => router.push('/dashboard'), 2500);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to restore account. The recovery window may have passed.';
      setError(msg);
      toast.error('Restore Failed', msg);
    } finally {
      setRestoring(false);
    }
  };

  if (restored) {
    return (
      <div className="flex flex-col items-center gap-6 py-4">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center">
            <ShieldCheck className="w-10 h-10 text-emerald-400" />
          </div>
          <div className="absolute inset-0 rounded-full bg-emerald-400/10 animate-ping" />
        </div>
        <div className="text-center flex flex-col gap-2">
          <h2 className="text-2xl font-bold text-white">Account Restored! 🎉</h2>
          <p className="text-neutral-400 text-sm">
            Your account is fully restored and all your data is intact.
          </p>
          <p className="text-neutral-500 text-xs">Redirecting to your dashboard...</p>
        </div>
        <Link href="/dashboard" className="text-violet-400 hover:text-violet-300 text-sm">
          Go to Dashboard →
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mb-1">
          <RefreshCcw className="w-6 h-6 text-emerald-400" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Restore Account</h1>
        <p className="text-sm text-neutral-400">
          Your account is pending deletion. Cancel the deletion and restore your account now.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex gap-3 items-start">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-rose-400 font-semibold text-sm">Restore Failed</p>
            <p className="text-rose-400/70 text-xs mt-1">{error}</p>
          </div>
        </div>
      )}

      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex gap-3 items-start">
        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs text-emerald-400">
          <p className="font-semibold mb-0.5">Restoring your account will:</p>
          <ul className="text-emerald-400/70 space-y-0.5 list-disc list-inside">
            <li>Cancel the scheduled deletion</li>
            <li>Reactivate your account immediately</li>
            <li>Restore all your data and access</li>
          </ul>
        </div>
      </div>

      {!accessToken ? (
        <div className="flex flex-col gap-3">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <p className="text-amber-400 text-xs">
              You need to sign in to restore your account. Use your credentials — your account is still accessible during the recovery window.
            </p>
          </div>
          <Link href="/auth/login">
            <Button variant="violet" className="w-full">Sign In to Restore Account</Button>
          </Link>
        </div>
      ) : (
        <Button
          id="restore-account-btn"
          variant="violet"
          isLoading={restoring}
          onClick={handleRestore}
          className="w-full"
        >
          <RefreshCcw className="w-4 h-4 mr-2" />
          Restore My Account
        </Button>
      )}

      <p className="text-center text-xs text-neutral-600">
        Changed your mind?{' '}
        <Link href="/auth/login" className="text-neutral-400 hover:text-white">
          Return to sign in
        </Link>
      </p>
    </div>
  );
}

export default function RestoreAccountPage() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading...</div>}>
      <RestoreAccountContent />
    </React.Suspense>
  );
}
