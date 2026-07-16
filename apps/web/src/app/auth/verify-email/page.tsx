'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/services/api-client';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = React.useState<'verifying' | 'success' | 'error'>('verifying');
  const [errorMsg, setErrorMsg] = React.useState('');

  React.useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMsg('Verification token is missing.');
      return;
    }

    const triggerVerification = async () => {
      try {
        await apiClient.post(`/auth/verify-email?token=${encodeURIComponent(token)}`);
        setStatus('success');
        toast.success('Email Verified', 'Your account has been successfully verified.');
      } catch (err: any) {
        setStatus('error');
        setErrorMsg(err.response?.data?.detail || err.message || 'Verification failed.');
      }
    };

    triggerVerification();
  }, [token]);

  return (
    <div className="flex flex-col gap-6 text-center items-center py-4">
      {status === 'verifying' && (
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-violet-500 animate-spin" />
          <h1 className="text-xl font-bold text-white">Verifying your email</h1>
          <p className="text-sm text-neutral-400">
            Please wait while we confirm your email token...
          </p>
        </div>
      )}

      {status === 'success' && (
        <div className="flex flex-col items-center gap-4">
          <CheckCircle2 className="w-16 h-16 text-emerald-400" />
          <h1 className="text-2xl font-bold text-white">Email Verified!</h1>
          <p className="text-sm text-neutral-300">
            Your email has been verified. You can now access your EAIMOS workspace.
          </p>
          <Button variant="violet" className="mt-2 w-full" onClick={() => router.push('/dashboard')}>
            Go to Dashboard
          </Button>
        </div>
      )}

      {status === 'error' && (
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="w-16 h-16 text-rose-400" />
          <h1 className="text-xl font-bold text-white">Verification Failed</h1>
          <p className="text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3.5 py-2.5 rounded-lg">
            {errorMsg}
          </p>
          <p className="text-xs text-neutral-400">
            The link may have expired or is invalid.
          </p>
          <div className="flex flex-col gap-2 w-full mt-2">
            <Button variant="violet" onClick={() => router.push('/auth/login')}>
              Sign In
            </Button>
            <Link href="/auth/forgot-password" className="text-violet-400 hover:text-violet-300 text-xs font-semibold mt-1">
              Need to reset password?
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default function VerifyEmail() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading email validation session...</div>}>
      <VerifyEmailContent />
    </React.Suspense>
  );
}
