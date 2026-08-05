/**
 * Organization React Query Hooks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationKeys } from './keys';
import { organizationsApi } from '../services/api';
import type { CreateOrganizationPayload, InviteMemberPayload, OrganizationRole } from '../types';

export function useOrganizations() {
  return useQuery({
    queryKey: organizationKeys.list(),
    queryFn: organizationsApi.list,
  });
}

export function useOrganizationMembers(orgId: string) {
  return useQuery({
    queryKey: organizationKeys.members(orgId),
    queryFn: () => organizationsApi.getMembers(orgId),
    enabled: !!orgId,
  });
}

export function useOrganizationInvitations(orgId: string) {
  return useQuery({
    queryKey: organizationKeys.invitations(orgId),
    queryFn: () => organizationsApi.getInvitations(orgId),
    enabled: !!orgId,
  });
}

export function useCreateOrganization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateOrganizationPayload) => organizationsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: organizationKeys.all }); },
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, data }: { orgId: string; data: InviteMemberPayload }) => organizationsApi.inviteMember(orgId, data),
    onSuccess: (_, variables) => { qc.invalidateQueries({ queryKey: organizationKeys.invitations(variables.orgId) }); },
  });
}

export function useUpdateMemberRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, userId, role }: { orgId: string; userId: string; role: OrganizationRole }) => organizationsApi.updateMemberRole(orgId, userId, role),
    onSuccess: (_, variables) => { qc.invalidateQueries({ queryKey: organizationKeys.members(variables.orgId) }); },
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orgId, userId }: { orgId: string; userId: string }) => organizationsApi.removeMember(orgId, userId),
    onSuccess: (_, variables) => { qc.invalidateQueries({ queryKey: organizationKeys.members(variables.orgId) }); },
  });
}
