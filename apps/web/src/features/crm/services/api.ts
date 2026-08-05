/**
 * CRM API Service — Connects to existing backend REST endpoints.
 * Reuses: /api/v1/crm/companies, /api/v1/crm/contacts, /api/v1/crm/leads, /api/v1/crm/activities
 * @see apps/api/src/api/routes/crm.py
 */

import { apiClient } from '@/services/api-client';
import type {
  Company, CompanyCreate,
  Contact, ContactCreate,
  Lead, LeadCreate, LeadUpdate,
  Activity, ActivityCreate,
} from '../types';

// ─── Companies ──────────────────────────────────────────────────────────────

export const companiesApi = {
  list: () => apiClient.get<Company[]>('/crm/companies').then(r => r.data),
  get: (id: string) => apiClient.get<Company>(`/crm/companies/${id}`).then(r => r.data),
  create: (data: CompanyCreate) => apiClient.post<Company>('/crm/companies', data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/crm/companies/${id}`),
};

// ─── Contacts ───────────────────────────────────────────────────────────────

export const contactsApi = {
  list: () => apiClient.get<Contact[]>('/crm/contacts').then(r => r.data),
  create: (data: ContactCreate) => apiClient.post<Contact>('/crm/contacts', data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/crm/contacts/${id}`),
};

// ─── Leads ──────────────────────────────────────────────────────────────────

export const leadsApi = {
  list: () => apiClient.get<Lead[]>('/crm/leads').then(r => r.data),
  create: (data: LeadCreate) => apiClient.post<Lead>('/crm/leads', data).then(r => r.data),
  update: (id: string, data: LeadUpdate) => apiClient.patch<Lead>(`/crm/leads/${id}`, data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/crm/leads/${id}`),
};

// ─── Activities ─────────────────────────────────────────────────────────────

export const activitiesApi = {
  list: () => apiClient.get<Activity[]>('/crm/activities').then(r => r.data),
  create: (data: ActivityCreate) => apiClient.post<Activity>('/crm/activities', data).then(r => r.data),
};
