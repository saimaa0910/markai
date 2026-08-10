'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Mail, ArrowLeft } from 'lucide-react';
import { apiClient } from '@/services/api-client';
import { authLifecycleService } from '@/services/auth-lifecycle.service';

const forgotPasswordSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPassword() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [email, setEmail] = React.useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    setLoading(true);
    setEmail(data.email);
    try {
      await authLifecycleService.requestPasswordReset(data.email);
      setSuccess(true);
      toast.success('Reset link sent', 'Check your inbox for recovery instructions.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred. Please try again.';
      toast.error('Request Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) return;
    setLoading(true);
    try {
      await authLifecycleService.requestPasswordReset(email);
      toast.success('Reset link resent', 'A fresh recovery link has been sent to your inbox.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred. Please try again.';
      toast.error('Resend Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {!success && (
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Reset your password
          </h1>
          <p className="text-sm text-neutral-400">
            Enter your email address and we'll send you a password recovery link.
          </p>
        </div>
      )}

      {success ? (
        <div className="flex flex-col items-center gap-6 py-4 text-center">
          <div className="relative">
            <div className="w-16 h-16 rounded-full bg-violet-500/20 border-2 border-violet-500/40 flex items-center justify-center">
              <Mail className="w-8 h-8 text-violet-400 animate-pulse" />
            </div>
            <div className="absolute inset-0 rounded-full bg-violet-500/10 animate-ping" style={{ animationDuration: '3s' }} />
          </div>
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-bold text-white">Reset Link Sent! ✉️</h2>
            <p className="text-sm text-neutral-400 max-w-sm">
              We have sent recovery instructions to <span className="text-white font-medium">{email}</span>. Please check your inbox.
            </p>
          </div>
          <div className="flex flex-col gap-3 w-full">
            <Button
              variant="outline"
              isLoading={loading}
              onClick={handleResend}
              className="w-full border-white/10 hover:bg-white/5 hover:text-white"
            >
              Resend Link
            </Button>
            <Link href="/auth/login" className="w-full">
              <Button variant="violet" className="w-full">
                Back to Sign In
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="name@company.com"
            error={errors.email?.message}
            disabled={loading}
            leftIcon={<Mail className="w-4 h-4" />}
            {...register('email')}
          />

          <Button type="submit" variant="violet" isLoading={loading} className="w-full mt-2">
            Send Reset Instructions
          </Button>
        </form>
      )}

      {!success && (
        <div className="text-center text-xs text-neutral-400">
          <Link href="/auth/login" className="inline-flex items-center gap-1.5 text-neutral-400 hover:text-white transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to sign in
          </Link>
        </div>
      )}
    </div>
  );
}
