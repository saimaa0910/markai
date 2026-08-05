'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2, Users, UserPlus, Shield, Trash2, X, Loader2, AlertCircle, Mail, CheckCircle2, Copy, Key, Settings,
} from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useOrganizationMembers, useOrganizationInvitations, useInviteMember, useUpdateMemberRole, useRemoveMember } from '../queries';
import type { OrganizationRole } from '../types';

function InviteMemberDialog({ open, onClose, orgId }: { open: boolean; onClose: () => void; orgId: string }) {
  const inviteMutation = useInviteMember();
  const [email, setEmail] = React.useState('');
  const [role, setRole] = React.useState<OrganizationRole>('MEMBER');
  const [error, setError] = React.useState('');
  const [copiedLink, setCopiedLink] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) { setError('Email is required'); return; }
    try {
      const res = await inviteMutation.mutateAsync({ orgId, data: { email, role } });
      if (res?.invite_link) setCopiedLink(res.invite_link);
      setEmail('');
      setError('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send invitation');
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-md p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><UserPlus className="w-5 h-5 text-violet-400" /> Invite Team Member</h2>
            <button onClick={onClose} className="text-zinc-500 hover:text-white"><X className="w-5 h-5" /></button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}

          {copiedLink ? (
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs">
                <p className="font-semibold flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" /> Invitation Sent & Created!</p>
                <p className="mt-1 text-zinc-300">Share this direct link with your team member if email is delayed:</p>
                <div className="mt-2 flex items-center gap-2 bg-zinc-950 p-2 rounded border border-zinc-800 text-zinc-400 font-mono text-[11px] truncate">
                  <span className="truncate">{copiedLink}</span>
                  <button onClick={() => navigator.clipboard.writeText(copiedLink)} className="p-1 hover:text-white"><Copy className="w-3.5 h-3.5" /></button>
                </div>
              </div>
              <button onClick={() => { setCopiedLink(null); onClose(); }} className="w-full py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium">Done</button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Email Address *</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                  placeholder="colleague@company.com" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Assigned Role</label>
                <select value={role} onChange={e => setRole(e.target.value as OrganizationRole)}
                  className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50">
                  <option value="MEMBER">Member — Standard Access</option>
                  <option value="ADMIN">Admin — Full Management</option>
                  <option value="GUEST">Guest — Read-Only</option>
                  <option value="OWNER">Owner — Full Ownership</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 bg-zinc-800 text-white rounded-lg text-sm font-medium">Cancel</button>
                <button type="submit" disabled={inviteMutation.isPending}
                  className="flex-1 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2">
                  {inviteMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Sending...</> : <><Mail className="w-4 h-4" /> Send Invite</>}
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function OrganizationPage() {
  const { activeOrg } = useAuthStore();
  const orgId = activeOrg?.id || '';

  const { data: members, isLoading: membersLoading } = useOrganizationMembers(orgId);
  const { data: invitations } = useOrganizationInvitations(orgId);
  const updateRoleMutation = useUpdateMemberRole();
  const removeMemberMutation = useRemoveMember();

  const [showInvite, setShowInvite] = React.useState(false);

  const handleRoleChange = async (userId: string, newRole: OrganizationRole) => {
    try {
      await updateRoleMutation.mutateAsync({ orgId, userId, role: newRole });
    } catch (e) {
      console.error('Failed to update role', e);
    }
  };

  const handleRemove = async (userId: string) => {
    try {
      await removeMemberMutation.mutateAsync({ orgId, userId });
    } catch (e) {
      console.error('Failed to remove member', e);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Building2 className="w-6 h-6 text-violet-400" /> {activeOrg?.name || 'Workspace Settings'}
          </h1>
          <p className="text-sm text-zinc-500 mt-1">Manage organization members, RBAC roles, and workspace invitations</p>
        </div>
        <button onClick={() => setShowInvite(true)} className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium flex items-center gap-2 shadow-lg shadow-violet-500/20">
          <UserPlus className="w-4 h-4" /> Invite Member
        </button>
      </div>

      {/* Members Section */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Users className="w-5 h-5 text-zinc-400" /> Active Members ({members?.length || 0})
        </h2>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
          {membersLoading ? (
            <div className="flex items-center justify-center py-16"><Loader2 className="w-6 h-6 text-violet-400 animate-spin" /><span className="ml-3 text-zinc-500 text-sm">Loading members...</span></div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Member</th>
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Email</th>
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Role</th>
                  <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {members?.map(m => (
                  <tr key={m.id} className="hover:bg-zinc-800/30 transition-colors group">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white text-xs font-semibold">
                          {m.full_name[0]}
                        </div>
                        <div>
                          <span className="text-sm font-medium text-white block">{m.full_name}</span>
                          {m.is_superuser && <span className="text-[10px] text-amber-400 font-semibold uppercase">Superadmin</span>}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-sm text-zinc-400">{m.email}</td>
                    <td className="px-5 py-4">
                      <select value={m.role} onChange={e => handleRoleChange(m.id, e.target.value as OrganizationRole)}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-zinc-800 text-zinc-200 border border-zinc-700 focus:outline-none cursor-pointer">
                        <option value="OWNER">OWNER</option>
                        <option value="ADMIN">ADMIN</option>
                        <option value="MEMBER">MEMBER</option>
                        <option value="GUEST">GUEST</option>
                      </select>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button onClick={() => handleRemove(m.id)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Pending Invitations Section */}
      {invitations && invitations.length > 0 && (
        <div className="space-y-4 pt-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Mail className="w-5 h-5 text-amber-400" /> Pending Invitations ({invitations.length})
          </h2>
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Email</th>
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Role</th>
                  <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Expires</th>
                  <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Copy Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {invitations.map(i => (
                  <tr key={i.id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-5 py-4 text-sm font-medium text-white">{i.email}</td>
                    <td className="px-5 py-4"><span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400">{i.role}</span></td>
                    <td className="px-5 py-4 text-sm text-zinc-400">{new Date(i.expires_at).toLocaleDateString()}</td>
                    <td className="px-5 py-4 text-right">
                      {i.invite_link && (
                        <button onClick={() => navigator.clipboard.writeText(i.invite_link!)} className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 ml-auto">
                          <Copy className="w-3.5 h-3.5" /> Copy Invite Link
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <InviteMemberDialog open={showInvite} onClose={() => setShowInvite(false)} orgId={orgId} />
    </div>
  );
}
