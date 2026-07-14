'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { DataTable, DataTableColumn } from '@/components/ui/data-table';
import { Dialog } from '@/components/ui/dialog';
import { StatCard } from '@/components/ui/stat-card';
import { EmptyState } from '@/components/ui/empty-state';
import { toast } from '@/components/ui/toast';
import {
  Users, UserPlus, Trash2, Shield, UserCheck,
  Crown, Eye, Mail, CheckCircle2, XCircle, AlertTriangle
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
type UserRow = Record<string, unknown> & {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role?: string;
  created_at?: string;
};

const ROLE_CONFIG: Record<string, { variant: any; label: string; icon: React.ReactNode }> = {
  superuser: { variant: 'violet', label: 'Super Admin', icon: <Crown className="w-3 h-3" /> },
  admin:     { variant: 'amber',  label: 'Admin',       icon: <Shield className="w-3 h-3" /> },
  member:    { variant: 'sky',    label: 'Member',      icon: <UserCheck className="w-3 h-3" /> },
  viewer:    { variant: 'neutral', label: 'Viewer',     icon: <Eye className="w-3 h-3" /> },
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function UsersPage() {
  const { activeOrg, user: currentUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [showInvite, setShowInvite] = React.useState(false);
  const [inviteForm, setInviteForm] = React.useState({ email: '', full_name: '', role: 'member', password: '' });

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: members = [], isLoading } = useQuery({
    queryKey: ['org-members', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get(`/organizations/${activeOrg?.id}/members/`);
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  // Fall back to fetching all users if org member endpoint not available
  const { data: allUsers = [], isLoading: loadingUsers } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await apiClient.get('/users/');
      return res.data || [];
    },
    enabled: members.length === 0,
  });

  const users: UserRow[] = (members.length > 0 ? members : allUsers).map((u: any) => ({
    ...u,
    role: u.is_superuser ? 'superuser' : u.role ?? 'member',
  }));

  // ── Mutations ─────────────────────────────────────────────────────────────
  const inviteMutation = useMutation({
    mutationFn: () =>
      apiClient.post('/auth/register', {
        email:      inviteForm.email,
        full_name:  inviteForm.full_name,
        password:   inviteForm.password || 'TemporaryPass123!',
        organization_id: activeOrg?.id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['org-members'] });
      setShowInvite(false);
      setInviteForm({ email: '', full_name: '', role: 'member', password: '' });
      toast.success('User Invited', 'Account created. Share credentials with the new team member.');
    },
    onError: () => toast.error('Error', 'Failed to create user account.'),
  });

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => apiClient.patch(`/users/${userId}`, { is_active: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success('Deactivated', 'User account has been deactivated.');
    },
  });

  // ── Stats ─────────────────────────────────────────────────────────────────
  const activeCount = users.filter((u) => u.is_active).length;
  const adminCount  = users.filter((u) => u.is_superuser).length;

  // ── Columns ───────────────────────────────────────────────────────────────
  const columns: DataTableColumn<UserRow>[] = [
    {
      key: 'full_name',
      label: 'User',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
            {(row.full_name || row.email).charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="text-xs font-semibold text-white">{row.full_name || '—'}</div>
            <div className="text-[10px] text-neutral-500 flex items-center gap-1">
              <Mail className="w-2.5 h-2.5" />{row.email}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      label: 'Role',
      sortable: true,
      render: (row) => {
        const roleKey = String(row.role ?? (row.is_superuser ? 'superuser' : 'member'));
        const cfg = ROLE_CONFIG[roleKey] ?? ROLE_CONFIG.member;
        return (
          <Badge variant={cfg.variant} className="gap-1">
            {cfg.icon} {cfg.label}
          </Badge>
        );
      },
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (row) => (
        <div className="flex items-center gap-1.5">
          {row.is_active
            ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            : <XCircle className="w-4 h-4 text-rose-400" />
          }
          <Badge variant={row.is_active ? 'emerald' : 'rose'} dot size="sm">
            {row.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      ),
    },
    {
      key: 'created_at',
      label: 'Joined',
      sortable: true,
      render: (row) => (
        <span className="text-[11px] text-neutral-500">
          {row.created_at ? new Date(String(row.created_at)).toLocaleDateString() : '—'}
        </span>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Users & Teams"
        description="Manage team members, roles, permissions, and access controls for your organization."
        icon={<Users className="w-5 h-5" />}
        badge={<Badge variant="violet">{users.length} Members</Badge>}
        actions={
          <Button variant="violet" size="sm" onClick={() => setShowInvite(true)}>
            <UserPlus className="w-3.5 h-3.5" />
            Invite User
          </Button>
        }
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Members"  value={users.length}  icon={<Users className="w-4 h-4" />}       description="In organization"       isLoading={isLoading || loadingUsers} />
        <StatCard title="Active"         value={activeCount}   icon={<CheckCircle2 className="w-4 h-4" />} iconColor="text-emerald-400" description="With active accounts"  isLoading={isLoading || loadingUsers} />
        <StatCard title="Admins"         value={adminCount}    icon={<Crown className="w-4 h-4" />}        iconColor="text-violet-400"  description="Superuser privileges"  isLoading={isLoading || loadingUsers} />
        <StatCard title="Inactive"       value={users.length - activeCount} icon={<AlertTriangle className="w-4 h-4" />} iconColor="text-amber-400" description="Suspended accounts" isLoading={isLoading || loadingUsers} />
      </div>

      {/* RBAC Info */}
      <div className="p-4 rounded-xl border border-violet-500/15 bg-violet-500/5 flex items-start gap-3">
        <Shield className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-violet-300">Role-Based Access Control</p>
          <p className="text-[11px] text-neutral-400 mt-0.5">
            <strong className="text-violet-300">Super Admin</strong> — Full access. 
            <strong className="text-amber-300"> Admin</strong> — Org settings, members. 
            <strong className="text-sky-300"> Member</strong> — Read/write data. 
            <strong className="text-neutral-300"> Viewer</strong> — Read-only access.
          </p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={users}
        isLoading={isLoading || loadingUsers}
        searchable
        searchPlaceholder="Search by name or email..."
        pageSize={15}
        emptyMessage="No team members found."
        emptyIcon={<Users className="w-8 h-8" />}
        actions={(row) => (
          row.id !== currentUser?.id ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => deactivateMutation.mutate(String(row.id))}
              disabled={!row.is_active}
              className="h-7 text-[11px] text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          ) : (
            <Badge variant="neutral" size="sm">You</Badge>
          )
        )}
      />

      {/* Invite Dialog */}
      <Dialog isOpen={showInvite} onClose={() => setShowInvite(false)} title="Invite Team Member">
        <form
          onSubmit={(e) => { e.preventDefault(); inviteMutation.mutate(); }}
          className="flex flex-col gap-4"
        >
          <Input
            label="Full Name"
            value={inviteForm.full_name}
            onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })}
            placeholder="Jane Smith"
            required
          />
          <Input
            label="Email Address"
            type="email"
            value={inviteForm.email}
            onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
            placeholder="jane@company.com"
            required
          />
          <Input
            label="Temporary Password"
            type="password"
            value={inviteForm.password}
            onChange={(e) => setInviteForm({ ...inviteForm, password: e.target.value })}
            placeholder="Min 8 characters"
            helperText="Share this with the team member to set a permanent password."
            required
          />
          <Select
            label="Role"
            value={inviteForm.role}
            onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
            options={[
              { label: 'Member', value: 'member' },
              { label: 'Admin', value: 'admin' },
              { label: 'Viewer', value: 'viewer' },
            ]}
          />
          <div className="flex gap-2 pt-1">
            <Button type="submit" variant="violet" size="sm" isLoading={inviteMutation.isPending} className="flex-1">
              Create Account
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setShowInvite(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
