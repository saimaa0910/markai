'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { KeyRound, Mail, AlertTriangle } from 'lucide-react';
import { apiClient } from '@/services/api-client';

const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(1, { message: "Password is required" }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth, setActiveOrg, setOrganizations } = useAuthStore();
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (searchParams.get('expired') === 'true') {
      toast.info('Session Expired', 'Please sign in again to continue.');
    }
  }, [searchParams]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('username', data.email);
      params.append('password', data.password);

      const loginRes = await apiClient.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const { access_token, refresh_token } = loginRes.data;

      // Fetch Profile
      const profileRes = await apiClient.get('/users/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      setAuth(access_token, refresh_token, profileRes.data);

      // Fetch User's Organizations
      const orgsRes = await apiClient.get('/organizations', {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      const orgs = orgsRes.data || [];
      setOrganizations(orgs);

      if (orgs.length > 0) {
        setActiveOrg(orgs[0]);
      }

      toast.success('Successfully Signed In', `Welcome back, ${profileRes.data.full_name || 'User'}!`);
      router.push('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Incorrect email or password.';
      setError(msg);
      toast.error('Authentication Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Sign in to your account
        </h1>
        <p className="text-sm text-neutral-400">
          Enter your credentials to access the EAIMOS Workspace.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex gap-2.5 items-center">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

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

        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          error={errors.password?.message}
          disabled={loading}
          leftIcon={<KeyRound className="w-4 h-4" />}
          {...register('password')}
        />

        <div className="flex justify-between items-center text-xs mt-1">
          <label className="flex items-center gap-2 cursor-pointer text-neutral-400 hover:text-white transition-colors">
            <input type="checkbox" className="rounded bg-neutral-900 border-white/10" />
            <span>Remember me</span>
          </label>
          <Link href="/auth/forgot-password" className="text-violet-400 hover:text-violet-300 transition-colors">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" variant="violet" isLoading={loading} className="w-full mt-2">
          Sign In
        </Button>
      </form>

      <div className="text-center text-xs text-neutral-400">
        Don't have an account?{' '}
        <Link href="/auth/register" className="text-violet-400 hover:text-violet-300 font-semibold transition-colors">
          Create an account
        </Link>
      </div>
    </div>
  );
}

export default function Login() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading Auth Session...</div>}>
      <LoginContent />
    </React.Suspense>
  );
}
