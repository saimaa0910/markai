/**
 * CRM React Query Keys — Centralized query key factory.
 */

export const crmKeys = {
  all: ['crm'] as const,
  companies: () => [...crmKeys.all, 'companies'] as const,
  company: (id: string) => [...crmKeys.companies(), id] as const,
  contacts: () => [...crmKeys.all, 'contacts'] as const,
  contact: (id: string) => [...crmKeys.contacts(), id] as const,
  leads: () => [...crmKeys.all, 'leads'] as const,
  lead: (id: string) => [...crmKeys.leads(), id] as const,
  activities: () => [...crmKeys.all, 'activities'] as const,
};
