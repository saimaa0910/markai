'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card } from '@eaimos/ui';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { KeyRound, Loader2 } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(1, { message: "Password is required" }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function Login() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const {
    register: formRegister,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setLoading(true);
    setError(null);
    try {
      // Format as urlencoded form data for OAuth2 compliance
      const params = new URLSearchParams();
      params.append('username', data.email);
      params.append('password', data.password);

      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
      });

      const tokenData = await res.json();
      if (!res.ok) {
        throw new Error(tokenData.detail || 'Login failed');
      }

      // Fetch user profile info
      const userRes = await fetch('http://localhost:8000/api/v1/users/me', {
        headers: {
          Authorization: `Bearer ${tokenData.access_token}`,
        },
      });

      const userData = await userRes.json();
      if (!userRes.ok) {
        throw new Error('Failed to retrieve user profile.');
      }

      // Save to Zustand
      setAuth(tokenData.access_token, tokenData.refresh_token, userData);

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'An error occurred during sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-black text-white px-6">
      {/* Background patterns */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[160px]" />
      </div>

      <div className="relative w-full max-w-md">
        <Card className="glass shadow-2xl p-8 border-white/10">
          <div className="flex flex-col items-center mb-8 text-center">
            <div className="inline-flex p-3 rounded-xl border border-violet-500/20 bg-violet-500/5 text-violet-400 mb-4">
              <KeyRound className="w-6 h-6 animate-bounce" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Sign In</h2>
            <p className="text-sm text-neutral-400 mt-1">Access the EAIMOS marketing operating system</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Email Address</label>
              <input
                type="email"
                {...formRegister('email')}
                placeholder="name@company.com"
                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/15 focus:border-violet-500 focus:outline-none transition-colors text-sm"
              />
              {errors.email && <p className="text-xs text-rose-400 mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Password</label>
              <input
                type="password"
                {...formRegister('password')}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/15 focus:border-violet-500 focus:outline-none transition-colors text-sm"
              />
              {errors.password && <p className="text-xs text-rose-400 mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Signing In...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="text-center text-xs text-neutral-400 mt-6">
            Don't have an account?{' '}
            <Link href="/auth/register" className="text-violet-400 hover:underline">
              Create one
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
