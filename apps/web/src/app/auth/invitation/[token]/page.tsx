'use client';

import * as React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Building2, Users, Shield, CheckCircle2, XCircle, AlertTriangle, KeyRound, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';

interface InvitationDetails {
  token: string;
  email: string;
  role: string;
  organization_name: string;
  organization_id: string;
  expires_at: string | null;
}

const newAccountSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine(d => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type NewAccountValues = z.infer<typeof newAccountSchema>;

const ROLE_COLORS: Record<string, string> = {
  OWNER: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  ADMIN: 'text-violet-400 bg-violet-400/10 border-violet-400/20',
  MEMBER: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  GUEST: 'text-neutral-400 bg-neutral-400/10 border-neutral-400/20',
};

function InvitationContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  const { user: currentUser, accessToken } = useAuthStore();

  const [invitation, setInvitation] = React.useState<InvitationDetails | null>(null);
  const [loadingInvitation, setLoadingInvitation] = React.useState(true);
  const [invitationError, setInvitationError] = React.useState<string | null>(null);
  const [accepting, setAccepting] = React.useState(false);
  const [declining, setDeclining] = React.useState(false);
  const [accepted, setAccepted] = React.useState(false);
  const [needsAccount, setNeedsAccount] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<NewAccountValues>({ resolver: zodResolver(newAccountSchema) });

  // Load invitation details
  React.useEffect(() => {
    if (!token) {
      setInvitationError('No invitation token provided.');
      setLoadingInvitation(false);
      return;
    }

    apiClient.get(`/auth/invitations/${token}`)
      .then(res => {
        setInvitation(res.data);
        // Check if user is logged in and matches
        if (!currentUser && !accessToken) {
          // Need to check if email is registered
          setNeedsAccount(true);
        }
      })
      .catch(err => {
        const msg = err.response?.data?.detail || 'Invitation not found or expired.';
        setInvitationError(msg);
      })
      .finally(() => setLoadingInvitation(false));
  }, [token, currentUser, accessToken]);

  const handleAccept = async () => {
    if (!token) return;
    setAccepting(true);
    try {
      await apiClient.post('/auth/invitations/accept', { token }, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
      });
      setAccepted(true);
      toast.success('Invitation Accepted!', `Welcome to ${invitation?.organization_name}!`);
      setTimeout(() => router.push('/dashboard'), 2000);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to accept invitation.';
      toast.error('Error', msg);
    } finally {
      setAccepting(false);
    }
  };

  const handleDecline = async () => {
    if (!token) return;
    setDeclining(true);
    try {
      await apiClient.post('/auth/invitations/reject', { token });
      toast.info('Invitation Declined', 'The invitation has been declined.');
      router.push('/');
    } catch {
      toast.error('Error', 'Failed to decline invitation.');
    } finally {
      setDeclining(false);
    }
  };

  const onCreateAccount = async (data: NewAccountValues) => {
    if (!invitation || !token) return;
    setAccepting(true);
    try {
      // Register with the invitation token
      const registerRes = await apiClient.post('/auth/register', {
        email: invitation.email,
        password: data.password,
        full_name: data.full_name,
        invitation_token: token,
      });

      toast.success(
        'Account Created!',
        `Welcome to ${invitation.organization_name}! Check your email to verify your account.`
      );
      router.push('/auth/login?registered=true');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to create account.';
      toast.error('Registration Failed', msg);
    } finally {
      setAccepting(false);
    }
  };

  if (loadingInvitation) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-neutral-400 text-sm">Loading invitation details...</p>
      </div>
    );
  }

  if (invitationError) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-white">Invitation Not Found</h1>
        </div>
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex gap-3 items-start">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-rose-400 font-medium text-sm">Invalid or Expired Invitation</p>
            <p className="text-rose-400/70 text-xs mt-1">{invitationError}</p>
          </div>
        </div>
        <Link href="/auth/login" className="text-violet-400 hover:text-violet-300 text-sm text-center">
          ← Back to Sign In
        </Link>
      </div>
    );
  }

  if (accepted) {
    return (
      <div className="flex flex-col items-center gap-6 py-4">
        <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
          <CheckCircle2 className="w-8 h-8 text-emerald-400" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-bold text-white mb-2">You've joined {invitation?.organization_name}!</h2>
          <p className="text-neutral-400 text-sm">Redirecting you to your workspace...</p>
        </div>
        <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const roleColor = invitation ? (ROLE_COLORS[invitation.role] || ROLE_COLORS.MEMBER) : '';

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Organization Invitation
        </h1>
        <p className="text-sm text-neutral-400">
          You've been invited to join a team on EAIMOS.
        </p>
      </div>

      {/* Invitation Card */}
      <div className="p-5 rounded-xl bg-white/[0.03] border border-white/10 flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center shrink-0">
            <Building2 className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{invitation?.organization_name}</h2>
            <p className="text-neutral-400 text-sm">Invited: <span className="text-white">{invitation?.email}</span></p>
          </div>
        </div>

        <div className="flex items-center gap-2 pt-2 border-t border-white/5">
          <Shield className="w-4 h-4 text-neutral-500" />
          <span className="text-neutral-400 text-sm">Your role:</span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${roleColor}`}>
            {invitation?.role}
          </span>
        </div>

        {invitation?.expires_at && (
          <p className="text-neutral-500 text-xs">
            Expires: {new Date(invitation.expires_at).toLocaleDateString('en-US', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
            })}
          </p>
        )}
      </div>

      {/* Logged in — show accept/decline */}
      {currentUser && !needsAccount && (
        <div className="flex flex-col gap-3">
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 flex gap-2 items-center">
            <Users className="w-4 h-4 text-blue-400 shrink-0" />
            <p className="text-blue-400 text-xs">
              Signed in as <strong>{currentUser.email}</strong>. Accept to join {invitation?.organization_name}.
            </p>
          </div>
          <Button
            id="accept-invitation-btn"
            variant="violet"
            isLoading={accepting}
            onClick={handleAccept}
            className="w-full"
          >
            Accept Invitation
          </Button>
          <Button
            variant="ghost"
            isLoading={declining}
            onClick={handleDecline}
            className="w-full text-neutral-400"
          >
            Decline
          </Button>
        </div>
      )}

      {/* New user — create account form */}
      {needsAccount && (
        <div className="flex flex-col gap-4">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex gap-2 items-start">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-amber-400 text-xs">
              Create a new account to accept this invitation. Your account will be linked to {invitation?.email}.
            </p>
          </div>

          <form onSubmit={handleSubmit(onCreateAccount)} className="flex flex-col gap-3">
            <Input
              label="Full Name"
              type="text"
              placeholder="Your name"
              error={errors.full_name?.message}
              leftIcon={<User className="w-4 h-4" />}
              {...register('full_name')}
            />
            <Input
              label="Password"
              type="password"
              placeholder="At least 8 characters"
              error={errors.password?.message}
              leftIcon={<KeyRound className="w-4 h-4" />}
              {...register('password')}
            />
            <Input
              label="Confirm Password"
              type="password"
              placeholder="Repeat password"
              error={errors.confirm_password?.message}
              leftIcon={<KeyRound className="w-4 h-4" />}
              {...register('confirm_password')}
            />
            <Button
              id="create-and-accept-btn"
              type="submit"
              variant="violet"
              isLoading={accepting}
              className="w-full mt-1"
            >
              Create Account & Join
            </Button>
          </form>

          <p className="text-center text-xs text-neutral-500">
            Already have an account?{' '}
            <Link
              href={`/auth/login?next=/auth/invitation?token=${token}`}
              className="text-violet-400 hover:text-violet-300"
            >
              Sign in
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}

export default function InvitationPage() {
  return (
    <React.Suspense fallback={<div className="text-neutral-500 text-xs">Loading...</div>}>
      <InvitationContent />
    </React.Suspense>
  );
}
