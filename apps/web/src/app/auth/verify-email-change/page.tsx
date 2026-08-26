'use client';

import * as React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Mail, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';

function VerifyEmailChangeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  const email = searchParams.get('email');

  const [verifying, setVerifying] = React.useState(false);
  const [confirmed, setConfirmed] = React.useState(false);
  const [confirmError, setConfirmError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!token || confirmed) return;
    setVerifying(true);
    apiClient
      .post('/users/email/confirm', { token, new_email: email })
      .then(() => {
        setConfirmed(true);
        toast.success('Email Updated!', 'Your email address has been changed.');
        setTimeout(() => router.push('/auth/login?email_changed=true'), 2500);
      })
      .catch((err) => {
        const msg =
          err.response?.data?.detail ||
          'Confirmation failed. The link may have expired.';
        setConfirmError(msg);
        toast.error('Email Change Failed', msg);
      })
      .finally(() => setVerifying(false));
  }, [token, email, confirmed, router]);

  if (verifying) {
    return (
      <div className="flex flex-col gap-4 text-center">
        <div className="mx-auto w-12 h-12 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-neutral-400">Confirming your new email...</p>
      </div>
    );
  }

  if (confirmed) {
    return (
      <div className="flex flex-col gap-4 text-center">
        <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
        <h1 className="text-xl font-bold text-white">Email Updated</h1>
        <p className="text-sm text-neutral-400">
          Your email address has been successfully changed.
        </p>
        <Button onClick={() => router.push('/auth/login')}>Go to Sign In</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-center">
      <XCircle className="w-12 h-12 text-rose-400 mx-auto" />
      <h1 className="text-xl font-bold text-white">Email Change Failed</h1>
      <p className="text-sm text-neutral-400">
        {confirmError || 'The link may be invalid or expired.'}
      </p>
      <Link href="/auth/login" className="text-sm text-violet-400 hover:text-violet-300">
        Back to Sign In
      </Link>
    </div>
  );
}

export default function VerifyEmailChangePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#09090B] px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center gap-2">
          <Mail className="w-10 h-10 text-violet-400" />
          <h2 className="text-2xl font-bold text-white">Confirm Email Change</h2>
        </div>
        <React.Suspense fallback={<div className="text-neutral-400 text-sm text-center">Loading...</div>}>
          <VerifyEmailChangeContent />
        </React.Suspense>
      </div>
    </div>
  );
}
