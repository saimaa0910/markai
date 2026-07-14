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
import { Sparkles, Mail, KeyRound, User, Building, AlertTriangle } from 'lucide-react';
import { apiClient } from '@/services/api-client';

const registerSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
  fullName: z.string().min(2, { message: "Name must be at least 2 characters" }),
  orgName: z.string().min(2, { message: "Organization name must be at least 2 characters" }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function Register() {
  const router = useRouter();
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/auth/register', {
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        org_name: data.orgName,
      });

      if (res.status === 201 || res.status === 200) {
        toast.success(
          'Account Created Successfully!',
          'Your organization has been configured. Sign in to start.'
        );
        router.push('/auth/login');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred during registration.';
      setError(msg);
      toast.error('Registration Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Create your account <Sparkles className="w-5 h-5 text-violet-400 animate-pulse" />
        </h1>
        <p className="text-sm text-neutral-400">
          Set up your organization and unified marketing dashboard.
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
          label="Full Name"
          type="text"
          placeholder="John Doe"
          error={errors.fullName?.message}
          disabled={loading}
          leftIcon={<User className="w-4 h-4" />}
          {...register('fullName')}
        />

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
          label="Organization Name"
          type="text"
          placeholder="Acme Corporation"
          error={errors.orgName?.message}
          disabled={loading}
          leftIcon={<Building className="w-4 h-4" />}
          {...register('orgName')}
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

        <Button type="submit" variant="violet" isLoading={loading} className="w-full mt-2">
          Register Now
        </Button>
      </form>

      <div className="text-center text-xs text-neutral-400">
        Already have an account?{' '}
        <Link href="/auth/login" className="text-violet-400 hover:text-violet-300 font-semibold transition-colors">
          Sign In
        </Link>
      </div>
    </div>
  );
}
