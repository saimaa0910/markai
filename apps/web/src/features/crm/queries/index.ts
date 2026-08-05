/**
 * CRM React Query Hooks — Data fetching connected to existing backend.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { crmKeys } from './keys';
import { companiesApi, contactsApi, leadsApi, activitiesApi } from '../services/api';
import type { CompanyCreate, ContactCreate, LeadCreate, LeadUpdate, ActivityCreate } from '../types';

// ─── Companies ──────────────────────────────────────────────────────────────

export function useCompanies() {
  return useQuery({
    queryKey: crmKeys.companies(),
    queryFn: companiesApi.list,
  });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: crmKeys.company(id),
    queryFn: () => companiesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanyCreate) => companiesApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.companies() }); },
  });
}

export function useDeleteCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.companies() }); },
  });
}

// ─── Contacts ───────────────────────────────────────────────────────────────

export function useContacts() {
  return useQuery({
    queryKey: crmKeys.contacts(),
    queryFn: contactsApi.list,
  });
}

export function useCreateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ContactCreate) => contactsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.contacts() }); },
  });
}

export function useDeleteContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.contacts() }); },
  });
}

// ─── Leads ──────────────────────────────────────────────────────────────────

export function useLeads() {
  return useQuery({
    queryKey: crmKeys.leads(),
    queryFn: leadsApi.list,
  });
}

export function useCreateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LeadCreate) => leadsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.leads() }); },
  });
}

export function useUpdateLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: LeadUpdate }) => leadsApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.leads() }); },
  });
}

export function useDeleteLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => leadsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.leads() }); },
  });
}

// ─── Activities ─────────────────────────────────────────────────────────────

export function useActivities() {
  return useQuery({
    queryKey: crmKeys.activities(),
    queryFn: activitiesApi.list,
  });
}

export function useCreateActivity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ActivityCreate) => activitiesApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: crmKeys.activities() }); },
  });
}
