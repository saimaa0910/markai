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
import { useAuthStore } from '@/store/auth';
import { Sparkles, Mail, KeyRound, User, Building, AlertTriangle, CheckCircle } from 'lucide-react';
import { apiClient } from '@/services/api-client';

const registerSchema = z.object({
  fullName: z.string().min(2, { message: "Name must be at least 2 characters" }),
  email: z.string().email({ message: "Invalid email address" }),
  orgName: z.string().min(2, { message: "Organization name must be at least 2 characters" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine(val => val === true, {
    message: "You must accept the terms and conditions"
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

function GoogleOAuthButton({ onSuccess, disabled }: { onSuccess: () => void; disabled?: boolean }) {
  const [loading, setLoading] = React.useState(false);
  const { setAuth, setActiveOrg, setOrganizations } = useAuthStore();
  const router = useRouter();

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      if (typeof window !== 'undefined' && (window as any).google?.accounts?.oauth2) {
        const client = (window as any).google.accounts.oauth2.initTokenClient({
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
          scope: 'email profile openid',
          callback: async (tokenResponse: any) => {
            if (tokenResponse.access_token) {
              try {
                const res = await apiClient.post('/auth/oauth/google', {
                  access_token: tokenResponse.access_token,
                });
                const { access_token, refresh_token } = res.data;
                const profileRes = await apiClient.get('/users/me', {
                  headers: { Authorization: `Bearer ${access_token}` },
                });
                setAuth(access_token, refresh_token, profileRes.data);
                const orgsRes = await apiClient.get('/organizations/', {
                  headers: { Authorization: `Bearer ${access_token}` },
                });
                const orgs = orgsRes.data || [];
                setOrganizations(orgs);
                if (orgs.length > 0) setActiveOrg(orgs[0]);
                toast.success('Signed in with Google', `Welcome, ${profileRes.data.full_name || 'User'}!`);
                router.push('/dashboard');
                onSuccess();
              } catch (err: any) {
                const msg = err.response?.data?.detail || 'Google sign-in failed';
                toast.error('Authentication Failed', msg);
              }
            }
            setLoading(false);
          },
        });
        client.requestAccessToken();
      } else {
        toast.error('Google Sign-In unavailable', 'Please use email and password.');
        setLoading(false);
      }
    } catch {
      setLoading(false);
    }
  };

  return (
    <button
      id="google-oauth-btn"
      type="button"
      disabled={disabled || loading}
      onClick={handleGoogleLogin}
      className="w-full flex items-center justify-center gap-3 py-2.5 px-4 rounded-lg
                 bg-white/5 border border-white/10 text-white text-sm font-medium
                 hover:bg-white/10 hover:border-white/20 transition-all duration-200
                 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
      ) : (
        <GoogleIcon />
      )}
      <span>{loading ? 'Connecting...' : 'Continue with Google'}</span>
    </button>
  );
}

export default function Register() {
  const router = useRouter();
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [registeredEmail, setRegisteredEmail] = React.useState<string | null>(null);

  // Load Google Identity Services script
  React.useEffect(() => {
    if (process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      document.head.appendChild(script);
      return () => {
        try {
          document.head.removeChild(script);
        } catch {}
      };
    }
  }, []);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      acceptTerms: false
    }
  });

  const passwordVal = watch('password', '');

  // Calculate password strength score 0 to 4
  const getPasswordStrength = (pass: string) => {
    if (!pass) return 0;
    let score = 0;
    if (pass.length >= 8) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;
    return score;
  };

  const strengthScore = getPasswordStrength(passwordVal);

  const getStrengthLabel = (score: number) => {
    if (score === 0) return { label: '', color: 'bg-transparent', text: 'text-neutral-500' };
    if (score === 1) return { label: 'Weak', color: 'bg-rose-500 w-[25%]', text: 'text-rose-400' };
    if (score === 2) return { label: 'Fair', color: 'bg-amber-500 w-[50%]', text: 'text-amber-400' };
    if (score === 3) return { label: 'Good', color: 'bg-yellow-500 w-[75%]', text: 'text-yellow-400' };
    return { label: 'Strong', color: 'bg-emerald-500 w-[100%]', text: 'text-emerald-400' };
  };

  const strengthDetails = getStrengthLabel(strengthScore);

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
          'Please verify your email address before signing in.'
        );
        setRegisteredEmail(data.email);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'An error occurred during registration.';
      setError(msg);
      toast.error('Registration Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  if (registeredEmail) {
    return (
      <div className="flex flex-col gap-6 py-4 items-center text-center">
        <div className="w-16 h-16 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center mb-1">
          <Mail className="w-8 h-8 text-violet-400 animate-bounce" />
        </div>
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
            Verify your email <CheckCircle className="w-5 h-5 text-emerald-400" />
          </h2>
          <p className="text-sm text-neutral-400 max-w-sm">
            We sent a verification link to <span className="text-violet-400 font-semibold">{registeredEmail}</span>.
          </p>
        </div>
        <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 max-w-sm leading-relaxed">
          Please click the verification link in that email to fully activate your account and set up your workspace.
        </div>
        <div className="flex flex-col gap-3 w-full max-w-xs mt-3">
          <Button 
            id="back-to-login-btn"
            variant="violet" 
            onClick={() => router.push('/auth/login')}
            className="w-full"
          >
            Proceed to Sign In
          </Button>
          <button 
            onClick={() => setRegisteredEmail(null)}
            className="text-neutral-500 hover:text-neutral-300 text-xs transition-colors cursor-pointer"
          >
            Modify email / Register again
          </button>
        </div>
      </div>
    );
  }

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

      {/* Google OAuth */}
      {process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
        <>
          <GoogleOAuthButton onSuccess={() => {}} disabled={loading} />
          <div className="flex items-center gap-3">
            <div className="h-[1px] bg-white/10 flex-1" />
            <span className="text-[10px] text-neutral-500 font-semibold uppercase tracking-wider">Or register with email</span>
            <div className="h-[1px] bg-white/10 flex-1" />
          </div>
        </>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <Input
          id="register-fullname"
          label="Full Name"
          type="text"
          placeholder="John Doe"
          error={errors.fullName?.message}
          disabled={loading}
          leftIcon={<User className="w-4 h-4" />}
          {...register('fullName')}
        />

        <Input
          id="register-email"
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          error={errors.email?.message}
          disabled={loading}
          leftIcon={<Mail className="w-4 h-4" />}
          {...register('email')}
        />

        <Input
          id="register-orgname"
          label="Organization Name"
          type="text"
          placeholder="Acme Corporation"
          error={errors.orgName?.message}
          disabled={loading}
          leftIcon={<Building className="w-4 h-4" />}
          {...register('orgName')}
        />

        <div className="flex flex-col gap-1.5">
          <Input
            id="register-password"
            label="Password"
            type="password"
            placeholder="••••••••"
            error={errors.password?.message}
            disabled={loading}
            leftIcon={<KeyRound className="w-4 h-4" />}
            {...register('password')}
          />
          {/* Password strength meter */}
          {passwordVal && (
            <div className="flex flex-col gap-1 px-1">
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-neutral-500 font-medium">Password Strength:</span>
                <span className={`font-bold ${strengthDetails.text}`}>{strengthDetails.label}</span>
              </div>
              <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                <div className={`h-full transition-all duration-300 rounded-full ${strengthDetails.color}`} />
              </div>
            </div>
          )}
        </div>

        <Input
          id="register-confirmpassword"
          label="Confirm Password"
          type="password"
          placeholder="••••••••"
          error={errors.confirmPassword?.message}
          disabled={loading}
          leftIcon={<KeyRound className="w-4 h-4" />}
          {...register('confirmPassword')}
        />

        <div className="flex flex-col gap-1">
          <label className="flex items-start gap-3 cursor-pointer select-none py-1 group">
            <input
              id="register-acceptterms"
              type="checkbox"
              disabled={loading}
              className="mt-0.5 w-4 h-4 rounded border-white/10 bg-white/5 text-violet-600 
                         focus:ring-violet-500/20 focus:ring-offset-0 focus:ring-1
                         disabled:opacity-50 disabled:cursor-not-allowed"
              {...register('acceptTerms')}
            />
            <span className="text-xs text-neutral-400 group-hover:text-neutral-300 leading-normal transition-colors">
              I agree to the{' '}
              <a href="#" className="text-violet-400 hover:text-violet-300 underline font-medium">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-violet-400 hover:text-violet-300 underline font-medium">Privacy Policy</a>.
            </span>
          </label>
          {errors.acceptTerms && (
            <span className="text-[10px] text-rose-400 font-medium px-1 flex gap-1 items-center mt-0.5">
              <AlertTriangle className="w-3.5 h-3.5" /> {errors.acceptTerms.message}
            </span>
          )}
        </div>

        <Button 
          id="register-submit-btn" 
          type="submit" 
          variant="violet" 
          isLoading={loading} 
          className="w-full mt-2"
        >
          Create Unified Account
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
