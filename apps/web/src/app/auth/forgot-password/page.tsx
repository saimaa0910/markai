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

const forgotPasswordSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPassword() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    setLoading(true);
    try {
      await apiClient.post(`/auth/forgot-password?email=${encodeURIComponent(data.email)}`);
      setSuccess(true);
      toast.success('Reset link sent', 'Check your console logs or inbox for recovery instructions.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred. Please try again.';
      toast.error('Request Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Reset your password
        </h1>
        <p className="text-sm text-neutral-400">
          Enter your email address and we'll send you a password recovery link.
        </p>
      </div>

      {success ? (
        <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-center">
          <p className="text-sm text-neutral-200">
            We have printed a password recovery URL to the backend logs.
          </p>
          <Button variant="outline" className="mt-4 w-full" onClick={() => router.push('/auth/login')}>
            Back to Sign In
          </Button>
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

      <div className="text-center text-xs text-neutral-400">
        <Link href="/auth/login" className="inline-flex items-center gap-1.5 text-neutral-400 hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to sign in
        </Link>
      </div>
    </div>
  );
}
