/**
 * CRM Feature Types — Mapped 1:1 to existing backend Pydantic schemas.
 * @see apps/api/src/api/schemas/crm.py
 */

// --- Company Types ---

export interface Company {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  size: string | null;
  organization_id: string;
}

export interface CompanyCreate {
  name: string;
  domain?: string | null;
  industry?: string | null;
  size?: string | null;
}

// --- Contact Types ---

export interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  job_title: string | null;
  company_id: string | null;
  organization_id: string;
}

export interface ContactCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  job_title?: string | null;
  company_id?: string | null;
}

// --- Lead Types ---

export type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';

export interface Lead {
  id: string;
  title: string;
  status: LeadStatus;
  value: number;
  contact_id: string | null;
  company_id: string | null;
  organization_id: string;
}

export interface LeadCreate {
  title: string;
  status?: LeadStatus;
  value?: number;
  contact_id?: string | null;
  company_id?: string | null;
}

export interface LeadUpdate {
  title?: string;
  status?: LeadStatus;
  value?: number;
  contact_id?: string | null;
  company_id?: string | null;
}

// --- Activity Types ---

export type ActivityType = 'CALL' | 'EMAIL' | 'MEETING' | 'NOTE' | 'TASK';

export interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description: string | null;
  lead_id: string | null;
  contact_id: string | null;
  organization_id: string;
}

export interface ActivityCreate {
  type: ActivityType;
  title: string;
  description?: string | null;
  lead_id?: string | null;
  contact_id?: string | null;
}

// --- Deal Types ---

export interface Pipeline {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  currency: string;
  organization_id: string;
}

export interface DealStage {
  id: string;
  pipeline_id: string;
  name: string;
  position: number;
  probability: number;
  color: string | null;
  is_won: boolean;
  is_lost: boolean;
}

export interface Deal {
  id: string;
  name: string;
  amount: number;
  currency: string;
  probability: number;
  expected_close_date: string | null;
  pipeline_id: string;
  stage_id: string;
  company_id: string | null;
  contact_id: string | null;
  owner_id: string | null;
  source: string | null;
  notes: string | null;
  organization_id: string;
}

// --- CRM Stats ---

export interface CRMStats {
  totalContacts: number;
  totalCompanies: number;
  totalLeads: number;
  totalDeals: number;
  pipelineValue: number;
}
