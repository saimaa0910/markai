'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { toast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Users, UserPlus, Mail, Shield, MoreHorizontal, Search,
  Crown, RefreshCcw, Trash2, Send, ChevronDown, CheckCircle2, Clock,
} from 'lucide-react';

type MemberRole = 'OWNER' | 'ADMIN' | 'MEMBER' | 'GUEST';

interface Member {
  id: string;
  email: string;
  full_name: string;
  role: MemberRole;
  is_active: boolean;
  joined_at?: string;
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  expires_at: string;
  invite_link: string;
  resent_count?: number;
}

const ROLE_STYLES: Record<string, string> = {
  OWNER: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  ADMIN: 'text-violet-400 bg-violet-400/10 border-violet-400/20',
  MEMBER: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  GUEST: 'text-neutral-400 bg-neutral-400/10 border-neutral-400/20',
};

const ROLE_ICONS: Record<string, React.ReactNode> = {
  OWNER: <Crown className="w-3 h-3" />,
  ADMIN: <Shield className="w-3 h-3" />,
  MEMBER: <Users className="w-3 h-3" />,
  GUEST: <Users className="w-3 h-3" />,
};

export default function MembersPage() {
  const { accessToken, activeOrg, user } = useAuthStore();
  const [members, setMembers] = React.useState<Member[]>([]);
  const [invitations, setInvitations] = React.useState<Invitation[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [search, setSearch] = React.useState('');
  const [showInviteForm, setShowInviteForm] = React.useState(false);
  const [inviteEmail, setInviteEmail] = React.useState('');
  const [inviteRole, setInviteRole] = React.useState<MemberRole>('MEMBER');
  const [inviting, setInviting] = React.useState(false);
  const [activeMenu, setActiveMenu] = React.useState<string | null>(null);
  const [tab, setTab] = React.useState<'members' | 'invitations'>('members');

  const orgId = activeOrg?.id;
  const headers = { Authorization: `Bearer ${accessToken}`, 'X-Organization-Id': orgId || '' };

  const fetchData = React.useCallback(async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const [membersRes, inviteRes] = await Promise.all([
        apiClient.get(`/organizations/${orgId}/members/`, { headers }),
        apiClient.get(`/organizations/${orgId}/invitations/`, { headers }),
      ]);
      setMembers(membersRes.data || []);
      setInvitations(inviteRes.data || []);
    } catch (err) {
      toast.error('Error', 'Failed to load members.');
    } finally {
      setLoading(false);
    }
  }, [orgId, accessToken]);

  React.useEffect(() => { fetchData(); }, [fetchData]);

  const filteredMembers = members.filter(m =>
    m.full_name.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleInvite = async () => {
    if (!inviteEmail || !orgId) return;
    setInviting(true);
    try {
      await apiClient.post(`/organizations/${orgId}/invitations/`, {
        email: inviteEmail,
        role: inviteRole,
      }, { headers });
      toast.success('Invitation Sent', `Invitation sent to ${inviteEmail}`);
      setInviteEmail('');
      setShowInviteForm(false);
      fetchData();
    } catch (err: any) {
      toast.error('Error', err.response?.data?.detail || 'Failed to send invitation.');
    } finally {
      setInviting(false);
    }
  };

  const handleResendInvitation = async (invitationId: string, email: string) => {
    try {
      await apiClient.post(`/organizations/${orgId}/invitations/${invitationId}/resend`, {}, { headers });
      toast.success('Resent', `Invitation resent to ${email}`);
      fetchData();
    } catch (err: any) {
      toast.error('Error', err.response?.data?.detail || 'Failed to resend.');
    }
  };

  const handleRevokeInvitation = async (invitationId: string, email: string) => {
    try {
      await apiClient.delete(`/organizations/${orgId}/invitations/${invitationId}`, { headers });
      toast.success('Revoked', `Invitation for ${email} revoked.`);
      fetchData();
    } catch {
      toast.error('Error', 'Failed to revoke invitation.');
    }
  };

  const handleRoleChange = async (userId: string, newRole: MemberRole) => {
    try {
      await apiClient.patch(`/organizations/${orgId}/members/${userId}`, null, {
        params: { role: newRole },
        headers,
      });
      toast.success('Role Updated', `Member role changed to ${newRole}`);
      fetchData();
    } catch {
      toast.error('Error', 'Failed to update role.');
    }
    setActiveMenu(null);
  };

  const handleRemoveMember = async (userId: string, email: string) => {
    if (!confirm(`Remove ${email} from ${activeOrg?.name}?`)) return;
    try {
      await apiClient.delete(`/organizations/${orgId}/members/${userId}`, { headers });
      toast.success('Removed', `${email} has been removed from the organization.`);
      fetchData();
    } catch {
      toast.error('Error', 'Failed to remove member.');
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-400" />
            Members
          </h1>
          <p className="text-neutral-400 text-sm mt-1">
            Manage team members and invitations for <span className="text-white font-medium">{activeOrg?.name}</span>
          </p>
        </div>
        <Button
          id="invite-member-btn"
          variant="violet"
          onClick={() => setShowInviteForm(v => !v)}
          className="flex items-center gap-2"
        >
          <UserPlus className="w-4 h-4" />
          Invite Member
        </Button>
      </div>

      {/* Invite Form */}
      {showInviteForm && (
        <div className="p-5 rounded-xl bg-white/[0.03] border border-white/10 flex flex-col gap-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Mail className="w-4 h-4 text-violet-400" />
            Invite a new member
          </h3>
          <div className="flex gap-3">
            <Input
              type="email"
              placeholder="colleague@company.com"
              value={inviteEmail}
              onChange={e => setInviteEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4" />}
              className="flex-1"
            />
            <select
              value={inviteRole}
              onChange={e => setInviteRole(e.target.value as MemberRole)}
              className="bg-white/[0.05] border border-white/10 rounded-lg px-3 text-white text-sm
                         focus:outline-none focus:border-violet-500/50 min-w-[110px]"
            >
              {(['ADMIN', 'MEMBER', 'GUEST'] as MemberRole[]).map(r => (
                <option key={r} value={r} className="bg-neutral-900">{r}</option>
              ))}
            </select>
            <Button
              id="send-invitation-btn"
              variant="violet"
              isLoading={inviting}
              onClick={handleInvite}
            >
              Send
            </Button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/[0.03] border border-white/10 rounded-xl p-1 w-fit">
        {[
          { key: 'members', label: `Members (${members.length})` },
          { key: 'invitations', label: `Pending Invitations (${invitations.length})` },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as any)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.key
                ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Members Tab */}
      {tab === 'members' && (
        <div className="flex flex-col gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 pointer-events-none" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white
                         placeholder:text-neutral-600 focus:outline-none focus:border-violet-500/50 transition-colors"
            />
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.02]">
                    <th className="text-left px-4 py-3 text-neutral-400 font-medium">Member</th>
                    <th className="text-left px-4 py-3 text-neutral-400 font-medium">Role</th>
                    <th className="text-left px-4 py-3 text-neutral-400 font-medium">Status</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredMembers.map(member => (
                    <tr key={member.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-violet-500/20 border border-violet-500/30
                                          flex items-center justify-center text-xs font-bold text-violet-400">
                            {(member.full_name || member.email)[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="text-white font-medium text-sm">
                              {member.full_name}
                              {member.id === user?.id && (
                                <span className="ml-2 text-xs text-neutral-500">(you)</span>
                              )}
                            </div>
                            <div className="text-neutral-500 text-xs">{member.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border ${ROLE_STYLES[member.role] || ROLE_STYLES.MEMBER}`}>
                          {ROLE_ICONS[member.role]}
                          {member.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                          member.is_active
                            ? 'text-emerald-400 bg-emerald-400/10'
                            : 'text-rose-400 bg-rose-400/10'
                        }`}>
                          <div className={`w-1.5 h-1.5 rounded-full ${member.is_active ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                          {member.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {member.id !== user?.id && (
                          <div className="relative">
                            <button
                              onClick={() => setActiveMenu(activeMenu === member.id ? null : member.id)}
                              className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 hover:text-white transition-colors"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </button>
                            {activeMenu === member.id && (
                              <div className="absolute right-0 top-8 z-20 bg-[#1a1a24] border border-white/10 rounded-xl
                                              shadow-xl shadow-black/50 min-w-[180px] overflow-hidden">
                                <p className="text-xs text-neutral-500 px-3 pt-2 pb-1">Change Role</p>
                                {(['ADMIN', 'MEMBER', 'GUEST'] as MemberRole[]).map(r => (
                                  <button
                                    key={r}
                                    onClick={() => handleRoleChange(member.id, r)}
                                    className="w-full text-left px-3 py-1.5 text-sm text-neutral-300 hover:bg-white/5
                                               hover:text-white transition-colors flex items-center gap-2"
                                  >
                                    {ROLE_ICONS[r]}
                                    {r}
                                    {member.role === r && <CheckCircle2 className="w-3 h-3 text-violet-400 ml-auto" />}
                                  </button>
                                ))}
                                <div className="border-t border-white/10 mt-1">
                                  <button
                                    onClick={() => handleRemoveMember(member.id, member.email)}
                                    className="w-full text-left px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/10
                                               transition-colors flex items-center gap-2"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                    Remove from org
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {filteredMembers.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-neutral-500 text-sm">
                        No members found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Invitations Tab */}
      {tab === 'invitations' && (
        <div className="flex flex-col gap-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : invitations.length === 0 ? (
            <div className="text-center py-12 text-neutral-500">
              <Mail className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No pending invitations</p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {invitations.map(inv => (
                <div key={inv.id} className="p-4 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                      <Clock className="w-4 h-4 text-amber-400" />
                    </div>
                    <div>
                      <p className="text-white text-sm font-medium">{inv.email}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-xs font-semibold px-1.5 py-0.5 rounded border ${ROLE_STYLES[inv.role] || ROLE_STYLES.MEMBER}`}>
                          {inv.role}
                        </span>
                        <span className="text-neutral-500 text-xs">
                          Expires {new Date(inv.expires_at).toLocaleDateString()}
                        </span>
                        {inv.resent_count && inv.resent_count > 0 && (
                          <span className="text-neutral-600 text-xs">· {inv.resent_count} resend(s)</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleResendInvitation(inv.id, inv.email)}
                      title="Resend invitation"
                      className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 hover:text-violet-400 transition-colors"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleRevokeInvitation(inv.id, inv.email)}
                      title="Revoke invitation"
                      className="p-1.5 rounded-lg hover:bg-rose-500/10 text-neutral-400 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
