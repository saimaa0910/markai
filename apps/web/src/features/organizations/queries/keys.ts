/**
 * Organization Query Key Factory.
 */

export const organizationKeys = {
  all: ['organizations'] as const,
  list: () => [...organizationKeys.all, 'list'] as const,
  members: (orgId: string) => [...organizationKeys.all, orgId, 'members'] as const,
  invitations: (orgId: string) => [...organizationKeys.all, orgId, 'invitations'] as const,
};
