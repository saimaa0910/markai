/**
 * Organization API Service Client.
 */

import { apiClient } from '@/services/api-client';
import type { Organization, OrganizationMember, OrganizationInvitation, CreateOrganizationPayload, InviteMemberPayload, OrganizationRole } from '../types';

export const organizationsApi = {
  list: () => apiClient.get<Organization[]>('/organizations/').then(r => r.data),
  create: (data: CreateOrganizationPayload) => apiClient.post<Organization>('/organizations/', data).then(r => r.data),
  update: (id: string, name: string) => apiClient.patch<Organization>(`/organizations/${id}?name=${encodeURIComponent(name)}`).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/organizations/${id}`),

  getMembers: (orgId: string) => apiClient.get<OrganizationMember[]>(`/organizations/${orgId}/members/`).then(r => r.data),
  updateMemberRole: (orgId: string, userId: string, role: OrganizationRole) => apiClient.patch<OrganizationMember>(`/organizations/${orgId}/members/${userId}?role=${role}`).then(r => r.data),
  removeMember: (orgId: string, userId: string) => apiClient.delete(`/organizations/${orgId}/members/${userId}`),

  getInvitations: (orgId: string) => apiClient.get<OrganizationInvitation[]>(`/organizations/${orgId}/invitations/`).then(r => r.data),
  inviteMember: (orgId: string, data: InviteMemberPayload) => apiClient.post<OrganizationInvitation>(`/organizations/${orgId}/invitations/`, data).then(r => r.data),
};
