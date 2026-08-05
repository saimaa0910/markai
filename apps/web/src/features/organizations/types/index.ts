/**
 * Organization Feature Types — Mapped 1:1 to backend schemas.
 * @see apps/api/src/api/routes/organizations.py
 */

export type OrganizationRole = 'OWNER' | 'ADMIN' | 'MEMBER' | 'GUEST';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role: OrganizationRole;
  created_at?: string | null;
}

export interface OrganizationInvitation {
  id: string;
  email: string;
  role: OrganizationRole;
  expires_at: string;
  invite_link?: string;
}

export interface CreateOrganizationPayload {
  name: string;
  slug?: string;
}

export interface InviteMemberPayload {
  email: string;
  role: OrganizationRole;
}
