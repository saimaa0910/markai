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
import { KeyRound, Mail, AlertTriangle, ShieldAlert } from 'lucide-react';
import { apiClient } from '@/services/api-client';

const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(1, { message: 'Password is required' }),
});

const mfaSchema = z.object({
  code: z.string().length(6, { message: 'Code must be exactly 6 digits' }).regex(/^\d+$/, { message: 'Code must be digits only' }),
});

type LoginFormValues = z.infer<typeof loginSchema>;
type MfaFormValues = z.infer<typeof mfaSchema>;

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

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth, setActiveOrg, setOrganizations } = useAuthStore();
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [mfaToken, setMfaToken] = React.useState<string | null>(null);

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

  React.useEffect(() => {
    if (searchParams.get('expired') === 'true') {
      toast.info('Session Expired', 'Please sign in again to continue.');
    }
    if (searchParams.get('verified') === 'true') {
      toast.success('Email Verified!', 'Your email has been verified. Sign in to continue.');
    }
  }, [searchParams]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const {
    register: registerMfa,
    handleSubmit: handleSubmitMfa,
    formState: { errors: mfaErrors },
    reset: resetMfa,
  } = useForm<MfaFormValues>({
    resolver: zodResolver(mfaSchema),
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

      // Check if MFA challenge is returned
      if (loginRes.data.mfa_required) {
        setMfaToken(loginRes.data.mfa_token);
        toast.info('MFA Verification Required', 'Please enter your 6-digit authenticator code.');
        setLoading(false);
        return;
      }

      const { access_token, refresh_token } = loginRes.data;

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

      toast.success('Successfully Signed In', `Welcome back, ${profileRes.data.full_name || 'User'}!`);
      if (profileRes.data.deletion_requested_at) {
        toast.error('Account Deletion Pending', 'Your account is scheduled for deletion. Please restore it first.');
        router.push('/auth/restore-account');
      } else if (profileRes.data.metadata_json?.change_password_required) {
        toast.info('Change Password Required', 'Please change your temporary password to continue.');
        router.push('/dashboard/settings?change_password=true');
      } else {
        router.push('/dashboard');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Incorrect email or password.';
      setError(msg);
      toast.error('Authentication Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  const onMfaSubmit = async (data: MfaFormValues) => {
    if (!mfaToken) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/auth/mfa/verify', {
        mfa_token: mfaToken,
        code: data.code,
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

      toast.success('Successfully Signed In', `MFA verified. Welcome back, ${profileRes.data.full_name || 'User'}!`);
      if (profileRes.data.deletion_requested_at) {
        toast.error('Account Deletion Pending', 'Your account is scheduled for deletion. Please restore it first.');
        router.push('/auth/restore-account');
      } else if (profileRes.data.metadata_json?.change_password_required) {
        toast.info('Change Password Required', 'Please change your temporary password to continue.');
        router.push('/dashboard/settings?change_password=true');
      } else {
        router.push('/dashboard');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Invalid or expired MFA code.';
      setError(msg);
      toast.error('MFA Verification Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  // If in MFA verification mode
  if (mfaToken) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Two-Factor Auth <ShieldAlert className="w-5 h-5 text-amber-400" />
          </h1>
          <p className="text-sm text-neutral-400">
            Enter the 6-digit code from your authenticator app (e.g. Google Authenticator) to continue.
          </p>
        </div>

        {error && (
          <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex gap-2.5 items-center">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmitMfa(onMfaSubmit)} className="flex flex-col gap-4">
          <Input
            id="mfa-code"
            label="Verification Code"
            type="text"
            placeholder="000000"
            maxLength={6}
            error={mfaErrors.code?.message}
            disabled={loading}
            leftIcon={<KeyRound className="w-4 h-4" />}
            {...registerMfa('code')}
          />

          <Button 
            id="mfa-submit-btn" 
            type="submit" 
            variant="violet" 
            isLoading={loading} 
            className="w-full mt-2"
          >
            Verify Code
          </Button>

          <button
            id="mfa-cancel-btn"
            type="button"
            onClick={() => {
              setMfaToken(null);
              setError(null);
              resetMfa();
            }}
            className="text-xs text-neutral-500 hover:text-neutral-300 font-medium transition-colors py-1 cursor-pointer"
          >
            Cancel and Return to Sign In
          </button>
        </form>
      </div>
    );
  }

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

      {/* Google OAuth */}
      {process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
        <>
          <GoogleOAuthButton onSuccess={() => {}} disabled={loading} />
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-[#18181f] px-3 text-neutral-500">or continue with email</span>
            </div>
          </div>
        </>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <Input
          id="login-email"
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          error={errors.email?.message}
          disabled={loading}
          leftIcon={<Mail className="w-4 h-4" />}
          {...register('email')}
        />

        <Input
          id="login-password"
          label="Password"
          type="password"
          placeholder="••••••••"
          error={errors.password?.message}
          disabled={loading}
          leftIcon={<KeyRound className="w-4 h-4" />}
          {...register('password')}
        />

        <div className="flex justify-between items-center text-xs mt-1">
          <label className="flex items-center gap-2 cursor-pointer text-neutral-400 hover:text-white transition-colors select-none">
            <input 
              id="login-remember-me"
              type="checkbox" 
              className="rounded bg-neutral-900 border-white/10" 
            />
            <span>Remember me</span>
          </label>
          <Link 
            id="login-forgot-password-link"
            href="/auth/forgot-password" 
            className="text-violet-400 hover:text-violet-300 transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <Button 
          id="login-submit-btn"
          type="submit" 
          variant="violet" 
          isLoading={loading} 
          className="w-full mt-2"
        >
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
