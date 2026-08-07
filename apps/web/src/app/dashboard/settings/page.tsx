'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import Link from 'next/link';
import { Card } from '@eaimos/ui';
import { 
  Settings, Key, CreditCard, Radio, ToggleLeft, ToggleRight, 
  Plus, Check, Trash2, Building, Shield, User, Globe, AlertTriangle, Palette,
  Upload, UserCheck, Eye, Lock, Mail, Users, UserPlus, Clock, Bell, Copy
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { apiClient } from '@/services/api-client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ThemeSwitcher } from '@/components/ui/theme-switcher';

export default function SettingsDashboard() {
  const queryClient = useQueryClient();
  const { activeOrg, organizations, setOrganizations, setActiveOrg, user: currentUser } = useAuthStore();
  const [activeTab, setActiveTab] = React.useState<'profile' | 'org' | 'billing' | 'keys' | 'integrations' | 'appearance'>('profile');

  // --- Queries ---
  const { data: userProfile, refetch: refetchProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const res = await apiClient.get('/users/me');
      return res.data;
    },
  });

  const { data: members = [], refetch: refetchMembers } = useQuery({
    queryKey: ['org-members', activeOrg?.id],
    queryFn: async () => {
      if (!activeOrg) return [];
      const res = await apiClient.get(`/organizations/${activeOrg.id}/members/`);
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: invitations = [], refetch: refetchInvitations } = useQuery({
    queryKey: ['org-invitations', activeOrg?.id],
    queryFn: async () => {
      if (!activeOrg) return [];
      const res = await apiClient.get(`/organizations/${activeOrg.id}/invitations/`);
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  // --- Profile state variables ---
  const [fullName, setFullName] = React.useState('');
  const [email, setEmail] = React.useState('');
  React.useEffect(() => {
    if (userProfile) {
      setFullName(userProfile.full_name || '');
      setEmail(userProfile.email || '');
    }
  }, [userProfile]);

  // --- Password change states ---
  const [oldPassword, setOldPassword] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');

  // --- Org form states ---
  const [editOrgName, setEditOrgName] = React.useState('');
  const [newOrgName, setNewOrgName] = React.useState('');
  const [creatingOrg, setCreatingOrg] = React.useState(false);
  const [inviteEmail, setInviteEmail] = React.useState('');
  const [inviteRole, setInviteRole] = React.useState('MEMBER');

  React.useEffect(() => {
    if (activeOrg) {
      setEditOrgName(activeOrg.name);
    }
  }, [activeOrg]);

  // --- API key states ---
  const [apiKeys, setApiKeys] = React.useState<{ id: string; label: string; token: string; created: string }[]>([
    { id: 'key_1', label: 'Production API Key', token: 'ea_live_••••••••••••••••••••3a9b', created: '2026-07-01' }
  ]);
  const [newKeyLabel, setNewKeyLabel] = React.useState('');

  // --- Preferences state ---
  const [timezone, setTimezone] = React.useState('UTC');
  const [language, setLanguage] = React.useState('en');
  const [notifyEmail, setNotifyEmail] = React.useState(true);
  const [notifyInApp, setNotifyInApp] = React.useState(true);

  React.useEffect(() => {
    if (userProfile?.preferences) {
      const prefs = userProfile.preferences;
      setTimezone(prefs.timezone || 'UTC');
      setLanguage(prefs.language || 'en');
      setNotifyEmail(prefs.notify_email !== false);
      setNotifyInApp(prefs.notify_in_app !== false);
    }
  }, [userProfile]);

  // --- Integrations states ---
  const [integrations, setIntegrations] = React.useState([
    { id: 'slack', name: 'Slack Alerts', desc: 'Push automated campaign performance alerts.', active: true },
    { id: 'gmail', name: 'Gmail Connector', desc: 'Sync customer mailing lists and outbound logs.', active: false },
    { id: 'drive', name: 'Google Drive', desc: 'Ingest collateral documents directly to Knowledge base.', active: false },
    { id: 'openai', name: 'OpenAI Developer Keys', desc: 'Enable secondary completions via custom keys.', active: true }
  ]);

  // --- Mutations ---
  const updateProfileMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch('/users/me', { full_name: fullName, email });
    },
    onSuccess: () => {
      refetchProfile();
      toast.success('Profile Saved', 'Your user profile details have been updated.');
    },
    onError: (err: any) => {
      toast.error('Update Failed', err.response?.data?.detail || err.message);
    }
  });

  const changePasswordMutation = useMutation({
    mutationFn: async () => {
      if (newPassword !== confirmPassword) {
        throw new Error('New passwords do not match');
      }
      return apiClient.post(`/auth/password-change?old_password=${encodeURIComponent(oldPassword)}&new_password=${encodeURIComponent(newPassword)}`);
    },
    onSuccess: () => {
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Password Updated', 'Your security password has been changed.');
    },
    onError: (err: any) => {
      toast.error('Change Failed', err.response?.data?.detail || err.message);
    }
  });

  const updateOrgMutation = useMutation({
    mutationFn: async () => {
      return apiClient.patch(`/organizations/${activeOrg?.id}?name=${encodeURIComponent(editOrgName)}`);
    },
    onSuccess: (res) => {
      const updatedOrg = res.data;
      setActiveOrg(updatedOrg);
      setOrganizations(organizations.map(org => org.id === updatedOrg.id ? updatedOrg : org));
      toast.success('Organization Updated', 'Workspace configuration settings successfully saved.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.response?.data?.detail || err.message);
    }
  });

  const inviteMutation = useMutation({
    mutationFn: async () => {
      return apiClient.post(`/organizations/${activeOrg?.id}/invitations/?email=${encodeURIComponent(inviteEmail)}&role=${inviteRole}`);
    },
    onSuccess: () => {
      setInviteEmail('');
      refetchInvitations();
      toast.success('Invitation Created', 'Onboarding invitation link printed to logs.');
    },
    onError: (err: any) => {
      toast.error('Invite Failed', err.response?.data?.detail || err.message);
    }
  });

  const updateMemberRoleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      return apiClient.patch(`/organizations/${activeOrg?.id}/members/${userId}?role=${role}`);
    },
    onSuccess: () => {
      refetchMembers();
      toast.success('Role Updated', 'Team member access tier updated.');
    },
    onError: (err: any) => {
      toast.error('Update Failed', err.response?.data?.detail || err.message);
    }
  });

  const removeMemberMutation = useMutation({
    mutationFn: async (userId: string) => {
      return apiClient.delete(`/organizations/${activeOrg?.id}/members/${userId}`);
    },
    onSuccess: () => {
      refetchMembers();
      toast.success('Member Removed', 'User has been removed from workspace.');
    },
    onError: (err: any) => {
      toast.error('Removal Failed', err.response?.data?.detail || err.message);
    }
  });

  const updatePrefsMutation = useMutation({
    mutationFn: async (payload: any) => {
      return apiClient.patch('/users/me/preferences', payload);
    },
    onSuccess: () => {
      refetchProfile();
      toast.success('Preferences Saved', 'General workspace settings updated.');
    },
    onError: (err: any) => {
      toast.error('Save Failed', err.response?.data?.detail || err.message);
    }
  });

  // Avatar Upload simulation
  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await apiClient.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      refetchProfile();
      toast.success('Avatar Uploaded', 'Your profile photo has been refreshed.');
    } catch (err: any) {
      toast.error('Upload Failed', err.response?.data?.detail || err.message);
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setCreatingOrg(true);
    try {
      const res = await apiClient.post('/organizations/', { name: newOrgName });
      const newOrg = res.data;
      const updatedOrgs = [...organizations, newOrg];
      setOrganizations(updatedOrgs);
      setActiveOrg(newOrg);
      setNewOrgName('');
      toast.success('Organization Created', `Switching to ${newOrg.name} workspace.`);
    } catch (err: any) {
      toast.error('Creation Failed', err.response?.data?.detail || err.message);
    } finally {
      setCreatingOrg(false);
    }
  };

  const handleCreateAPIKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyLabel.trim()) return;
    const newKey = {
      id: `key_${Date.now()}`,
      label: newKeyLabel,
      token: `ea_live_val_${Math.random().toString(36).substring(2, 10)}••••••••`,
      created: new Date().toLocaleDateString()
    };
    setApiKeys([...apiKeys, newKey]);
    setNewKeyLabel('');
    toast.success('API Token Generated', 'Make sure to save it now. It won\'t be shown again.');
  };

  const handleDeleteAPIKey = (id: string) => {
    setApiKeys(apiKeys.filter(k => k.id !== id));
    toast.success('API Key Revoked', 'The credentials are no longer authorized.');
  };

  const hasPermission = (perm: string) => {
    return userProfile?.permissions?.includes(perm) || userProfile?.is_superuser;
  };

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Settings Console <Settings className="w-6 h-6 text-violet-500" />
        </h1>
        <p className="text-neutral-400 mt-1">Configure tenant profiles, check active pricing tiers, manage team roles, and integrate webhooks.</p>
      </header>

      {/* Tabs Layout Split */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
        
        {/* Navigation Sidebar */}
        <Card className="glass p-3 border-white/5 flex flex-col gap-1">
          {[
            { id: 'profile', label: 'My Profile & Security', icon: User },
            { id: 'org', label: 'Organization & Team', icon: Building },
            { id: 'billing', label: 'Billing & Subscriptions', icon: CreditCard },
            { id: 'keys', label: 'API Credentials', icon: Key },
            { id: 'integrations', label: 'Connected Apps', icon: Radio },
            { id: 'appearance', label: 'Preferences', icon: Palette },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-all text-left cursor-pointer ${
                  activeTab === tab.id 
                    ? 'bg-violet-600/15 text-violet-400 font-semibold border-l-2 border-violet-500 rounded-l-none' 
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </Card>

        {/* Tab Workspaces */}
        <div className="lg:col-span-3">

          {/* ================================================== */}
          {/* TAB: MY PROFILE & SECURITY */}
          {/* ================================================== */}
          {activeTab === 'profile' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Profile Details</h3>
                  <p className="text-xs text-neutral-400 mt-1">Update your basic profile settings and photo.</p>
                </div>

                <div className="flex flex-col md:flex-row gap-8 items-start">
                  <div className="flex flex-col items-center gap-3 shrink-0">
                    <img 
                      src={userProfile?.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${fullName}`}
                      alt="Avatar" 
                      className="w-20 h-20 rounded-full border border-violet-500/20 bg-neutral-900 object-cover"
                    />
                    <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 text-[11px] text-neutral-300 hover:text-white cursor-pointer transition-colors bg-neutral-950/60 font-semibold">
                      <Upload className="w-3.5 h-3.5" /> Upload Photo
                      <input type="file" className="hidden" accept="image/*" onChange={handleAvatarUpload} />
                    </label>
                  </div>

                  <div className="flex-1 flex flex-col gap-4 max-w-md">
                    <Input
                      label="Full Name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Jane Smith"
                    />

                    <Input
                      label="Email Address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@company.com"
                    />

                    <Button 
                      variant="violet" 
                      onClick={() => updateProfileMutation.mutate()}
                      isLoading={updateProfileMutation.isPending}
                      className="self-start mt-2 px-5 py-2 text-xs"
                    >
                      Save Profile
                    </Button>
                  </div>
                </div>
              </Card>

              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white flex items-center gap-2"><Lock className="w-4 h-4 text-violet-400" /> Change Security Password</h3>
                  <p className="text-xs text-neutral-400 mt-1">Ensure your password uses at least 8 characters with a mix of symbols.</p>
                </div>

                <div className="flex flex-col gap-4 max-w-md">
                  <Input
                    label="Current Password"
                    type="password"
                    placeholder="••••••••"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                  />

                  <Input
                    label="New Password"
                    type="password"
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />

                  <Input
                    label="Confirm New Password"
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />

                  <Button 
                    variant="violet"
                    onClick={() => changePasswordMutation.mutate()}
                    isLoading={changePasswordMutation.isPending}
                    className="self-start mt-2 px-5 py-2 text-xs"
                  >
                    Change Password
                  </Button>
                </div>
              </Card>

              {/* Danger Zone */}
              <Card className="border-rose-500/20 bg-rose-500/5 p-6 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-rose-400 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-rose-500" /> Danger Zone</h3>
                  <p className="text-xs text-neutral-400 mt-1">Actions that can permanently delete or deactivate your account.</p>
                </div>

                <div className="flex flex-col gap-4 max-w-md">
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    Once you initiate account deletion, your profile, active sessions, and organizations ownership will be scheduled for permanent destruction after 7 days.
                  </p>

                  <Link 
                    id="danger-zone-delete-link"
                    href="/auth/delete-account" 
                    className="inline-flex items-center justify-center rounded-lg bg-rose-600/10 border border-rose-500/20 px-4 py-2 text-xs font-semibold text-rose-400 hover:bg-rose-600 hover:text-white transition-all duration-200 self-start cursor-pointer"
                  >
                    Initiate Account Deletion
                  </Link>
                </div>
              </Card>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: ORGANIZATION & TEAM */}
          {/* ================================================== */}
          {activeTab === 'org' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active Tenant Profile</h3>
                  <p className="text-xs text-neutral-400 mt-1">Configure details of the current operating workspace environment.</p>
                </div>
                
                <div className="flex flex-col gap-4 max-w-md">
                  <Input
                    label="Organization Name"
                    value={editOrgName}
                    onChange={(e) => setEditOrgName(e.target.value)}
                    disabled={!hasPermission('manage_users')}
                    helperText="Manage users permissions are required to rename organizations."
                  />

                  <Input
                    label="Workspace Slug (Router Key)"
                    value={activeOrg?.slug || ''}
                    disabled
                  />

                  {hasPermission('manage_users') && (
                    <Button 
                      variant="violet"
                      onClick={() => updateOrgMutation.mutate()}
                      isLoading={updateOrgMutation.isPending}
                      className="self-start mt-2 px-5"
                    >
                      Update Organization Name
                    </Button>
                  )}
                </div>
              </Card>

              {/* Members listing */}
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-base text-white flex items-center gap-2"><Users className="w-4 h-4 text-violet-400" /> Active Workspace Members</h3>
                    <p className="text-xs text-neutral-400 mt-1 font-normal">Manage team access tiers and roles in this active organization.</p>
                  </div>
                  <Badge variant="violet">{members.length} Users</Badge>
                </div>

                <div className="flex flex-col gap-3.5 mt-2">
                  {members.map((member: any) => (
                    <div key={member.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-3.5 rounded-lg bg-neutral-950/60 border border-white/5 gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white uppercase select-none">
                          {(member.full_name || member.email).charAt(0)}
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                            {member.full_name} {member.id === currentUser?.id && <span className="text-[10px] bg-white/10 text-neutral-400 px-1.5 py-0.5 rounded-md font-bold">You</span>}
                          </span>
                          <span className="text-[10px] text-neutral-500 font-mono mt-0.5">{member.email}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 self-end sm:self-center">
                        <Select
                          value={member.role?.toUpperCase() || 'MEMBER'}
                          onChange={(e) => updateMemberRoleMutation.mutate({ userId: member.id, role: e.target.value })}
                          disabled={!hasPermission('manage_users') || member.id === currentUser?.id || member.role?.toUpperCase() === 'OWNER'}
                          options={[
                            { label: 'Owner', value: 'OWNER' },
                            { label: 'Admin', value: 'ADMIN' },
                            { label: 'Member', value: 'MEMBER' },
                            { label: 'Viewer', value: 'GUEST' },
                          ]}
                          className="h-8 max-w-[120px] text-xs py-0 select-none bg-neutral-900 border-white/10"
                        />

                        {hasPermission('manage_users') && member.id !== currentUser?.id && member.role?.toUpperCase() !== 'OWNER' && (
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => removeMemberMutation.mutate(member.id)}
                            className="p-1 h-8 w-8 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5 rounded-md"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Invite User & Pending Invitations */}
              {hasPermission('manage_users') && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Invite user */}
                  <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                    <div>
                      <h3 className="font-bold text-base text-white flex items-center gap-2"><UserPlus className="w-4 h-4 text-violet-400" /> Send Invite</h3>
                      <p className="text-xs text-neutral-400 mt-1">Add team members via secure onboarding links.</p>
                    </div>

                    <div className="flex flex-col gap-4">
                      <Input
                        label="Email Address"
                        placeholder="collaborator@company.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        leftIcon={<Mail className="w-4 h-4" />}
                      />

                      <Select
                        label="Default Role"
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        options={[
                          { label: 'Admin', value: 'ADMIN' },
                          { label: 'Member', value: 'MEMBER' },
                          { label: 'Viewer', value: 'GUEST' },
                        ]}
                      />

                      <Button 
                        variant="violet" 
                        onClick={() => inviteMutation.mutate()}
                        isLoading={inviteMutation.isPending}
                        className="mt-2 w-full"
                      >
                        Send Invitation
                      </Button>
                    </div>
                  </Card>

                  {/* Pending invites */}
                  <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                    <div>
                      <h3 className="font-bold text-base text-white flex items-center gap-2"><Clock className="w-4 h-4 text-violet-400" /> Pending Invites</h3>
                      <p className="text-xs text-neutral-400 mt-1">Copy and share active registration links.</p>
                    </div>

                    <div className="flex flex-col gap-3 overflow-y-auto max-h-[220px]">
                      {invitations.length === 0 ? (
                        <div className="text-center py-6 text-neutral-500 text-xs flex flex-col items-center gap-2 bg-neutral-950/20 border border-dashed border-white/5 rounded-lg">
                          <Users className="w-5 h-5 text-neutral-600" />
                          <span>No pending invitations active.</span>
                        </div>
                      ) : (
                        invitations.map((invite: any) => (
                          <div key={invite.id} className="flex justify-between items-center p-3 rounded-lg bg-neutral-950/40 border border-white/5">
                            <div className="flex flex-col gap-0.5">
                              <span className="text-xs font-semibold text-white truncate max-w-[130px]">{invite.email}</span>
                              <span className="text-[9px] text-neutral-500 flex items-center gap-1">Role: {invite.role}</span>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => {
                                navigator.clipboard.writeText(invite.invite_link);
                                toast.success('Link Copied', 'Invitation onboarding URL copied to clipboard.');
                              }}
                              className="h-7 px-2 text-[10px] gap-1 text-violet-400 hover:text-white hover:bg-violet-500/10 border border-violet-500/15"
                            >
                              <Copy className="w-3 h-3" /> Copy URL
                            </Button>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>
              )}
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: BILLING & SUBSCRIPTIONS */}
          {/* ================================================== */}
          {activeTab === 'billing' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active Plan Tier</h3>
                  <p className="text-xs text-neutral-400 mt-1">Current subscription details and billing cycles.</p>
                </div>

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 rounded-xl border border-violet-500/20 bg-violet-500/5 gap-4">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider">Current Subscription Plan</span>
                    <span className="text-xl font-bold text-white mt-1">Enterprise Developer Pro</span>
                    <span className="text-[11px] text-neutral-400 mt-1">Renews on August 15, 2026</span>
                  </div>
                  <div className="flex items-baseline gap-1 text-white">
                    <span className="text-3xl font-extrabold">$249</span>
                    <span className="text-xs text-neutral-400">/ month</span>
                  </div>
                </div>
              </Card>

              {/* Pricing breakdown list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="p-5 border-white/5 bg-neutral-900/30 flex flex-col justify-between gap-4">
                  <div>
                    <h4 className="font-bold text-sm text-white">Unlimited Agent Tokens</h4>
                    <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                      Run multiple autonomous campaigns side-by-side using Gemini, Claude and GPT gateways without threshold restrictions.
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded px-2 py-0.5 self-start">
                    ACTIVE FOR ACTIVE ORGANIZATIONS
                  </span>
                </Card>

                <Card className="p-5 border-white/5 bg-neutral-900/30 flex flex-col justify-between gap-4">
                  <div>
                    <h4 className="font-bold text-sm text-white">Custom SLA Webhooks</h4>
                    <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                      Vectorize bulk databases, store prompt templates versioning, and configure Slack notifications integrations.
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded px-2 py-0.5 self-start">
                    ACTIVE FOR ACTIVE ORGANIZATIONS
                  </span>
                </Card>
              </div>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: API CREDENTIALS */}
          {/* ================================================== */}
          {activeTab === 'keys' && (
            <div className="flex flex-col gap-6">
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white">Active API Credentials</h3>
                  <p className="text-xs text-neutral-400 mt-1">Generate developer tokens to authorize external integrations with the EAIMOS API.</p>
                </div>

                {/* API Key list table */}
                <div className="flex flex-col gap-3">
                  {apiKeys.map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-3.5 rounded-lg bg-neutral-950/60 border border-white/5">
                      <div className="flex flex-col">
                        <span className="text-xs font-semibold text-white">{key.label}</span>
                        <span className="font-mono text-[10px] text-violet-400 mt-0.5">{key.token}</span>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-neutral-500">Created: {key.created}</span>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleDeleteAPIKey(key.id)}
                          className="p-1 h-7 w-7 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5 rounded-md"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Create key form */}
                <form onSubmit={handleCreateAPIKey} className="flex gap-3 max-w-md items-end border-t border-white/5 pt-4">
                  <div className="flex-1">
                    <Input
                      label="New API Key Label"
                      placeholder="e.g. GitHub Workflow Key"
                      required
                      value={newKeyLabel}
                      onChange={(e) => setNewKeyLabel(e.target.value)}
                    />
                  </div>
                  <Button type="submit" variant="violet" className="h-10 px-5 shrink-0">
                    Generate Key
                  </Button>
                </form>
              </Card>
            </div>
          )}

          {/* ================================================== */}
          {/* TAB: CONNECTED APPS & INTEGRATIONS */}
          {/* ================================================== */}
          {activeTab === 'integrations' && (
            <Card className="glass p-6 border-white/5 flex flex-col gap-6">
              <div>
                <h3 className="font-bold text-base text-white">Connected Applications & Integrations</h3>
                <p className="text-xs text-neutral-400 mt-1">Configure automated triggers and webhook loops across external platforms.</p>
              </div>

              {/* Integrations grid list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {integrations.map((int) => (
                  <div key={int.id} className="p-4 rounded-xl border border-white/5 bg-neutral-900/30 flex justify-between items-center gap-4 hover:border-violet-500/10 transition-colors">
                    <div>
                      <h4 className="text-sm font-semibold text-white">{int.name}</h4>
                      <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">{int.desc}</p>
                    </div>

                    <button 
                      onClick={() => setIntegrations(integrations.map(i => i.id === int.id ? { ...i, active: !i.active } : i))}
                      className="text-neutral-500 hover:text-white transition-colors cursor-pointer border-0 bg-transparent p-0"
                    >
                      {int.active ? (
                        <ToggleRight className="w-9 h-9 text-violet-500" />
                      ) : (
                        <ToggleLeft className="w-9 h-9 text-neutral-600" />
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ================================================== */}
          {/* TAB: PREFERENCES */}
          {/* ================================================== */}
          {activeTab === 'appearance' && (
            <div className="flex flex-col gap-6">
              {/* Preferences Form */}
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white flex items-center gap-2"><Globe className="w-4 h-4 text-violet-400" /> Workspace Preferences</h3>
                  <p className="text-xs text-neutral-400 mt-1">Configure timezone, language options, and user custom preferences.</p>
                </div>

                <div className="flex flex-col gap-4 max-w-md">
                  <Select
                    label="Language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    options={[
                      { label: 'English (US)', value: 'en' },
                      { label: 'Español (ES)', value: 'es' },
                      { label: 'Français (FR)', value: 'fr' },
                      { label: 'Deutsch (DE)', value: 'de' },
                    ]}
                  />

                  <Select
                    label="Timezone"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    options={[
                      { label: 'Coordinated Universal Time (UTC)', value: 'UTC' },
                      { label: 'US Eastern Standard Time (EST)', value: 'EST' },
                      { label: 'US Pacific Standard Time (PST)', value: 'PST' },
                      { label: 'Greenwich Mean Time (GMT)', value: 'GMT' },
                      { label: 'India Standard Time (IST)', value: 'IST' },
                    ]}
                  />

                  <div className="flex flex-col gap-3.5 border-t border-white/5 pt-4">
                    <h4 className="text-xs font-semibold text-white">Notifications Channels</h4>
                    <label className="flex items-center justify-between cursor-pointer text-xs text-neutral-400 hover:text-white transition-colors">
                      <span>Enable Email Updates</span>
                      <button 
                        type="button"
                        onClick={() => setNotifyEmail(!notifyEmail)}
                        className="border-0 bg-transparent p-0 cursor-pointer"
                      >
                        {notifyEmail ? <ToggleRight className="w-8 h-8 text-violet-500" /> : <ToggleLeft className="w-8 h-8 text-neutral-600" />}
                      </button>
                    </label>

                    <label className="flex items-center justify-between cursor-pointer text-xs text-neutral-400 hover:text-white transition-colors">
                      <span>Enable In-App Push alerts</span>
                      <button 
                        type="button"
                        onClick={() => setNotifyInApp(!notifyInApp)}
                        className="border-0 bg-transparent p-0 cursor-pointer"
                      >
                        {notifyInApp ? <ToggleRight className="w-8 h-8 text-violet-500" /> : <ToggleLeft className="w-8 h-8 text-neutral-600" />}
                      </button>
                    </label>
                  </div>

                  <Button 
                    variant="violet"
                    onClick={() => updatePrefsMutation.mutate({
                      timezone,
                      language,
                      notify_email: notifyEmail,
                      notify_in_app: notifyInApp,
                    })}
                    isLoading={updatePrefsMutation.isPending}
                    className="self-start mt-2 px-5 py-2 text-xs"
                  >
                    Save Preferences
                  </Button>
                </div>
              </Card>

              {/* Theme Selector */}
              <Card className="glass p-6 border-white/5 flex flex-col gap-6">
                <div>
                  <h3 className="font-bold text-base text-white flex items-center gap-2"><Palette className="w-4 h-4 text-violet-400" /> Theme & Appearance</h3>
                  <p className="text-xs text-neutral-400 mt-1">
                    Choose between light, dark, or system-synced color scheme.
                  </p>
                </div>

                <div className="flex flex-col gap-4">
                  <ThemeSwitcher variant="tabs" className="self-start" />

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
                    {[
                      {
                        label: 'Dark',
                        desc: 'Deep dark workspace with violet accents',
                        preview: 'bg-neutral-950 border-white/10',
                        dot: 'bg-violet-500',
                      },
                      {
                        label: 'Light',
                        desc: 'Clean bright surface for daytime productivity',
                        preview: 'bg-white border-neutral-200',
                        dot: 'bg-violet-600',
                      },
                      {
                        label: 'System',
                        desc: 'Automatically follows your OS preference',
                        preview: 'bg-gradient-to-br from-neutral-950 to-white border-neutral-400',
                        dot: 'bg-violet-400',
                      },
                    ].map((item) => (
                      <div key={item.label} className={`p-4 rounded-xl border ${item.preview} flex flex-col gap-2`}>
                        <div className={`w-3 h-3 rounded-full ${item.dot}`} />
                        <p className="text-xs font-bold mt-1 text-neutral-700 dark:text-neutral-200">{item.label}</p>
                        <p className="text-[10px] text-neutral-400 leading-relaxed">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

// Helper Badge Component since it might be imported differently in this layout
function Badge({ children, variant = 'neutral' }: { children: React.ReactNode, variant?: 'neutral' | 'violet' }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
      variant === 'violet' ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20' : 'bg-neutral-800 text-neutral-400 border border-white/5'
    }`}>
      {children}
    </span>
  );
}
