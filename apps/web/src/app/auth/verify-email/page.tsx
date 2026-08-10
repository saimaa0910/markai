'use client';

import * as React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, CheckCircle2, XCircle, RefreshCcw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';

const resendSchema = z.object({
  email: z.string().email('Please enter a valid email'),
});

type ResendValues = z.infer<typeof resendSchema>;

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [verifying, setVerifying] = React.useState(false);
  const [verified, setVerified] = React.useState(false);
  const [verifyError, setVerifyError] = React.useState<string | null>(null);
  const [resending, setResending] = React.useState(false);
  const [cooldown, setCooldown] = React.useState(0);
  const [showResendForm, setShowResendForm] = React.useState(!token);

  const { register, handleSubmit, formState: { errors } } = useForm<ResendValues>({
    resolver: zodResolver(resendSchema),
  });

  // Countdown timer for resend cooldown
  React.useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown(c => c - 1), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  // Auto-verify if token in URL
  React.useEffect(() => {
    if (!token) return;
    setVerifying(true);
    apiClient.post('/auth/verify-email', { token })
      .then(() => {
        setVerified(true);
        toast.success('Email Verified!', 'Your account is now fully active. Welcome to EAIMOS!');
        setTimeout(() => router.push('/auth/login?verified=true'), 2500);
      })
      .catch(err => {
        const msg = err.response?.data?.detail || 'Verification failed. The link may have expired.';
        const msgLower = msg.toLowerCase();
        if (msgLower.includes('already verified') || msgLower.includes('already')) {
          setVerifyError('already_verified');
        } else if (msgLower.includes('expired') || msgLower.includes('expire')) {
          setVerifyError('expired');
        } else {
          setVerifyError('invalid');
        }
      })
      .finally(() => setVerifying(false));
  }, [token, router]);

  const onResend = async (data: ResendValues) => {
    setResending(true);
    try {
      await apiClient.post('/auth/resend-verification', { email: data.email });
      toast.success('Verification Email Sent', 'Check your inbox for a new verification link.');
      setCooldown(60);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to resend verification email.';
      toast.error('Error', msg);
    } finally {
      setResending(false);
    }
  };

  // ── Verifying state ──
  if (verifying) {
    return (
      <div className="flex flex-col items-center gap-6 py-6">
        <div className="w-14 h-14 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
          <div className="w-7 h-7 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-bold text-white mb-1">Verifying your email...</h2>
          <p className="text-neutral-400 text-sm">Please wait a moment.</p>
        </div>
      </div>
    );
  }

  // ── Verified success ──
  if (verified) {
    return (
      <div className="flex flex-col items-center gap-6 py-4">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-400" />
          </div>
          <div className="absolute inset-0 rounded-full bg-emerald-400/20 animate-ping" />
        </div>
        <div className="text-center flex flex-col gap-2">
          <h2 className="text-2xl font-bold text-white">Email Verified! 🎉</h2>
          <p className="text-neutral-400 text-sm">
            Your account is now fully activated. Welcome to EAIMOS!
          </p>
          <p className="text-neutral-500 text-xs">Redirecting you to sign in...</p>
        </div>
        <Link href="/auth/login" className="text-violet-400 hover:text-violet-300 text-sm">
          Sign in now →
        </Link>
      </div>
    );
  }

  // ── Verification error (expired/already verified/invalid token) ──
  if (verifyError) {
    const isAlreadyVerified = verifyError === 'already_verified';
    const isExpired = verifyError === 'expired';

    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-white">
            {isAlreadyVerified ? 'Already Verified' : isExpired ? 'Link Expired' : 'Verification Failed'}
          </h1>
        </div>

        <div className={`p-4 rounded-xl border flex gap-3 items-start ${
          isAlreadyVerified 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
        }`}>
          {isAlreadyVerified ? (
            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
          )}
          <div>
            <p className="font-semibold text-sm">
              {isAlreadyVerified ? 'Email Already Verified' : isExpired ? 'Verification Link Expired' : 'Invalid Verification Link'}
            </p>
            <p className="text-xs mt-1 opacity-80">
              {isAlreadyVerified 
                ? 'Your email address is already verified. You can sign in using your credentials.' 
                : isExpired 
                  ? 'This link has expired. Verification links are only valid for 24 hours.' 
                  : 'The verification token is invalid or has already been used.'}
            </p>
          </div>
        </div>

        {!isAlreadyVerified && (
          <div className="flex flex-col gap-4">
            <p className="text-neutral-400 text-sm">
              Request a new verification link below.
            </p>
            <form onSubmit={handleSubmit(onResend)} className="flex flex-col gap-3">
              <Input
                label="Email Address"
                type="email"
                placeholder="name@company.com"
                error={errors.email?.message}
                leftIcon={<Mail className="w-4 h-4" />}
                {...register('email')}
              />
              <Button
                id="resend-verification-btn"
                type="submit"
                variant="violet"
                isLoading={resending}
                disabled={cooldown > 0}
                className="w-full"
              >
                {cooldown > 0 ? (
                  <span className="flex items-center gap-2">
                    <RefreshCcw className="w-4 h-4" />
                    Resend in {cooldown}s
                  </span>
                ) : (
                  'Send New Verification Link'
                )}
              </Button>
            </form>
          </div>
        )}

        <Link href="/auth/login" className="text-neutral-500 hover:text-neutral-300 text-xs text-center">
          {isAlreadyVerified ? 'Go to Sign In' : '← Back to Sign In'}
        </Link>
      </div>
    );
  }

  // ── No token — resend form ──
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="w-12 h-12 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center mb-1">
          <Mail className="w-6 h-6 text-violet-400" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Verify your email
        </h1>
        <p className="text-sm text-neutral-400">
          We sent a verification link to your email address. Check your inbox and click the link to activate your account.
        </p>
      </div>

      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 flex gap-3 items-start">
        <AlertTriangle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-blue-400">
          <p className="font-medium mb-0.5">Didn't get the email?</p>
          <p className="text-blue-400/70">Check your spam folder, or request a new link below. Links expire after 24 hours.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onResend)} className="flex flex-col gap-3">
        <Input
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          error={errors.email?.message}
          leftIcon={<Mail className="w-4 h-4" />}
          {...register('email')}
        />
        <Button
          id="resend-verification-btn"
          type="submit"
          variant="violet"
          isLoading={resending}
          disabled={cooldown > 0}
          className="w-full"
        >
          {cooldown > 0 ? (
            <span className="flex items-center gap-2">
              <RefreshCcw className="w-4 h-4" />
              Resend in {cooldown}s
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <RefreshCcw className="w-4 h-4" />
              Resend Verification Email
            </span>
          )}
        </Button>
      </form>

      <div className="text-center text-xs text-neutral-500">
        <Link href="/auth/login" className="text-neutral-400 hover:text-white transition-colors">
          ← Back to Sign In
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading...</div>}>
      <VerifyEmailContent />
    </React.Suspense>
  );
}
