'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { KeyRound, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { apiClient } from '@/services/api-client';

const resetPasswordSchema = z.object({
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [loading, setLoading] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const passwordVal = watch('password', '');

  const onSubmit = async (data: ResetPasswordFormValues) => {
    if (!token) {
      toast.error('Invalid Request', 'Reset token is missing from the URL.');
      return;
    }
    setLoading(true);
    try {
      await apiClient.post(`/auth/reset-password?token=${encodeURIComponent(token)}&new_password=${encodeURIComponent(data.password)}`);
      toast.success('Password updated', 'You can now sign in with your new password.');
      router.push('/auth/login');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred. Please try again.';
      toast.error('Reset Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrength = (val: string) => {
    if (!val) return { score: 0, label: '', color: 'bg-neutral-800' };
    let score = 0;
    if (val.length >= 8) score++;
    if (/[a-z]/.test(val) && /[A-Z]/.test(val)) score++;
    if (/\d/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;

    const scoreMap = [
      { label: 'Very Weak', color: 'bg-rose-500' },
      { label: 'Weak', color: 'bg-orange-500' },
      { label: 'Medium', color: 'bg-amber-500' },
      { label: 'Strong', color: 'bg-emerald-500' },
    ];
    return {
      score,
      ...scoreMap[Math.min(score - 1, 3)],
    };
  };

  const strength = getPasswordStrength(passwordVal);

  if (!token) {
    return (
      <div className="flex flex-col gap-4 text-center">
        <h1 className="text-xl font-bold text-white">Invalid Reset Link</h1>
        <p className="text-sm text-neutral-400">
          The password reset token is missing or has expired.
        </p>
        <Link href="/auth/forgot-password" className="text-violet-400 hover:text-violet-300 text-xs font-semibold mt-2">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Create new password
        </h1>
        <p className="text-sm text-neutral-400">
          Please enter and confirm your new password below.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="relative">
          <Input
            label="New Password"
            type={showPassword ? "text" : "password"}
            placeholder="••••••••"
            error={errors.password?.message}
            disabled={loading}
            leftIcon={<KeyRound className="w-4 h-4" />}
            {...register('password')}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[38px] text-neutral-500 hover:text-white transition-colors"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {passwordVal && (
          <div className="flex flex-col gap-1.5 mt-0.5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-neutral-500">Password Strength:</span>
              <span className={
                strength.score === 1 ? 'text-rose-400 font-semibold' :
                strength.score === 2 ? 'text-orange-400 font-semibold' :
                strength.score === 3 ? 'text-amber-400 font-semibold' :
                'text-emerald-400 font-semibold'
              }>{strength.label}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5 h-1">
              {[1, 2, 3, 4].map((index) => (
                <div
                  key={index}
                  className={`h-full rounded-full transition-all duration-300 ${
                    index <= strength.score ? strength.color : 'bg-white/5'
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        <Input
          label="Confirm New Password"
          type="password"
          placeholder="••••••••"
          error={errors.confirmPassword?.message}
          disabled={loading}
          leftIcon={<KeyRound className="w-4 h-4" />}
          {...register('confirmPassword')}
        />

        <Button type="submit" variant="violet" isLoading={loading} className="w-full mt-2">
          Reset Password
        </Button>
      </form>

      <div className="text-center text-xs text-neutral-400">
        <Link href="/auth/login" className="inline-flex items-center gap-1.5 text-neutral-400 hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to sign in
        </Link>
      </div>
    </div>
  );
}

export default function ResetPassword() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading recovery session...</div>}>
      <ResetPasswordContent />
    </React.Suspense>
  );
}
