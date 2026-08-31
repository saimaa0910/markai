# EAIMOS — Enterprise AI Marketing Operating System
# Complete Enterprise Database Design
## All 15 Sprints | Single Source of Truth

> **Status**: APPROVED DESIGN DOCUMENT  
> **Version**: 1.0.0 | **Created**: 2026-07-21  
> **DO NOT implement backend until ALL sprints are reviewed**

---

## GLOBAL STANDARDS

Every tenant-owned table MUST include:

| Column | Type | Rule |
|--------|------|------|
| `id` | `UUID` | PK, `gen_random_uuid()` default |
| `organization_id` | `UUID` | FK → organizations.id, NOT NULL, indexed |
| `created_at` | `TIMESTAMPTZ` | `NOW()` server default |
| `updated_at` | `TIMESTAMPTZ` | `NOW()`, trigger-updated |
| `created_by` | `UUID` | FK → users.id SET NULL |
| `updated_by` | `UUID` | FK → users.id SET NULL |
| `deleted_at` | `TIMESTAMPTZ` | NULL = active (soft delete) |
| `version` | `INTEGER` | Optimistic locking where noted |

---

# SPRINT 1 — CORE PLATFORM

## Module Overview

Establishes the foundational schema — tenant boundary, platform identity, membership, settings, feature flags, event sourcing, and audit.

**Owner Module**: `core` | **Dependencies**: None

## Business Entities

| Entity | Description |
|--------|-------------|
| Organization | Tenant boundary |
| User | Platform identity |
| UserOrganization | Membership with role |
| OrganizationInvitation | Pending invites |
| OrganizationSettings | Tenant config |
| FeatureFlag | Platform toggles |
| OrganizationFeatureFlag | Per-tenant flag override |
| PlatformEvent | Immutable event log |
| AuditLog | Compliance audit trail |

## Table List

| # | Table | Tenant-Scoped | Soft Delete | Partition |
|---|-------|--------------|------------|-----------|
| 1 | `organizations` | Root entity | Yes | No |
| 2 | `users` | No (platform) | Yes | No |
| 3 | `user_organizations` | Yes | Yes | No |
| 4 | `organization_invitations` | Yes | No | No |
| 5 | `organization_settings` | Yes | No | No |
| 6 | `feature_flags` | No | No | No |
| 7 | `organization_feature_flags` | Yes | No | No |
| 8 | `platform_events` | Yes | No | RANGE(created_at) Monthly |
| 9 | `audit_logs` | Yes | No (IMMUTABLE) | RANGE(created_at) Quarterly |

## Table Specifications

### `organizations`
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | `UUID` | NO | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `created_by` | `UUID` | YES | NULL |
| `updated_by` | `UUID` | YES | NULL |
| `deleted_at` | `TIMESTAMPTZ` | YES | NULL |
| `name` | `VARCHAR(255)` | NO | — |
| `slug` | `VARCHAR(100)` | NO | — |
| `plan_tier` | `VARCHAR(50)` | NO | `'free'` |
| `billing_email` | `VARCHAR(255)` | YES | NULL |
| `logo_url` | `TEXT` | YES | NULL |
| `website` | `VARCHAR(255)` | YES | NULL |
| `industry` | `VARCHAR(100)` | YES | NULL |
| `employee_count` | `INTEGER` | YES | NULL |
| `country_code` | `CHAR(2)` | YES | NULL |
| `timezone` | `VARCHAR(100)` | NO | `'UTC'` |
| `locale` | `VARCHAR(20)` | NO | `'en-US'` |
| `is_active` | `BOOLEAN` | NO | `TRUE` |
| `is_verified` | `BOOLEAN` | NO | `FALSE` |
| `max_members` | `INTEGER` | NO | `5` |
| `max_ai_credits` | `NUMERIC(12,4)` | NO | `100.0000` |
| `settings_json` | `JSONB` | YES | `'{}'` |
| `metadata_json` | `JSONB` | YES | `'{}'` |
| `version` | `INTEGER` | NO | `1` |

**Constraints**: UNIQUE `slug` | CHECK `plan_tier IN ('free','starter','professional','enterprise')`  
**FKs**: `created_by` → users.id SET NULL | `updated_by` → users.id SET NULL  
**Indexes**: PK on `id` | UNIQUE on `slug` | Partial on `is_active` | B-Tree on `created_at` | Partial WHERE `deleted_at IS NULL`

### `users`
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | `UUID` | NO | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `deleted_at` | `TIMESTAMPTZ` | YES | NULL |
| `email` | `VARCHAR(255)` | NO | — |
| `email_verified_at` | `TIMESTAMPTZ` | YES | NULL |
| `hashed_password` | `VARCHAR(255)` | YES | NULL |
| `full_name` | `VARCHAR(255)` | NO | — |
| `first_name` | `VARCHAR(100)` | YES | NULL |
| `last_name` | `VARCHAR(100)` | YES | NULL |
| `avatar_url` | `TEXT` | YES | NULL |
| `phone` | `VARCHAR(50)` | YES | NULL |
| `is_active` | `BOOLEAN` | NO | `TRUE` |
| `is_superuser` | `BOOLEAN` | NO | `FALSE` |
| `locale` | `VARCHAR(20)` | NO | `'en-US'` |
| `timezone` | `VARCHAR(100)` | NO | `'UTC'` |
| `last_login_at` | `TIMESTAMPTZ` | YES | NULL |
| `last_login_ip` | `VARCHAR(45)` | YES | NULL |
| `login_count` | `INTEGER` | NO | `0` |
| `mfa_enabled` | `BOOLEAN` | NO | `FALSE` |
| `mfa_method` | `VARCHAR(20)` | YES | NULL |
| `mfa_secret` | `TEXT` | YES | NULL |
| `failed_login_count` | `INTEGER` | NO | `0` |
| `locked_until` | `TIMESTAMPTZ` | YES | NULL |
| `password_changed_at` | `TIMESTAMPTZ` | YES | NULL |
| `onboarding_completed` | `BOOLEAN` | NO | `FALSE` |
| `preferences_json` | `JSONB` | YES | `'{}'` |
| `metadata_json` | `JSONB` | YES | `'{}'` |
| `version` | `INTEGER` | NO | `1` |

**Constraints**: UNIQUE `email`  
**Indexes**: UNIQUE `email` | Partial `deleted_at` WHERE NULL | `is_active` | `last_login_at`

### `user_organizations`
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | `UUID` | NO | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `created_by` | `UUID` | YES | NULL |
| `updated_by` | `UUID` | YES | NULL |
| `deleted_at` | `TIMESTAMPTZ` | YES | NULL |
| `user_id` | `UUID` | NO | — |
| `organization_id` | `UUID` | NO | — |
| `role` | `VARCHAR(20)` | NO | `'MEMBER'` |
| `is_primary` | `BOOLEAN` | NO | `FALSE` |
| `joined_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `invited_by` | `UUID` | YES | NULL |
| `department` | `VARCHAR(100)` | YES | NULL |
| `job_title` | `VARCHAR(100)` | YES | NULL |
| `version` | `INTEGER` | NO | `1` |

**Constraints**: PARTIAL UNIQUE `(user_id, organization_id)` WHERE `deleted_at IS NULL`  
**FKs**: `user_id` → users.id CASCADE | `organization_id` → organizations.id CASCADE | `invited_by` → users.id SET NULL  
**Indexes**: `user_id` | `organization_id` | Composite `(organization_id, user_id, role)` | Partial UNIQUE where active

### `platform_events` (PARTITIONED)
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | `UUID` | NO | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `organization_id` | `UUID` | YES | NULL |
| `user_id` | `UUID` | YES | NULL |
| `event_type` | `VARCHAR(100)` | NO | — |
| `aggregate_type` | `VARCHAR(100)` | NO | — |
| `aggregate_id` | `UUID` | NO | — |
| `payload` | `JSONB` | NO | — |
| `metadata` | `JSONB` | YES | `'{}'` |
| `event_version` | `INTEGER` | NO | `1` |
| `idempotency_key` | `VARCHAR(128)` | YES | NULL |
| `source` | `VARCHAR(100)` | NO | — |

**Partition**: `RANGE(created_at)` — Monthly | GIN on `payload`

### `audit_logs` (PARTITIONED, IMMUTABLE, 7-YEAR RETENTION)
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | `UUID` | NO | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` |
| `organization_id` | `UUID` | YES | NULL |
| `actor_id` | `UUID` | YES | NULL |
| `actor_email` | `VARCHAR(255)` | YES | NULL |
| `actor_ip` | `VARCHAR(45)` | YES | NULL |
| `actor_user_agent` | `TEXT` | YES | NULL |
| `entity_type` | `VARCHAR(100)` | NO | — |
| `entity_id` | `UUID` | YES | NULL |
| `action` | `VARCHAR(100)` | NO | — |
| `description` | `TEXT` | YES | NULL |
| `before_state` | `JSONB` | YES | NULL |
| `after_state` | `JSONB` | YES | NULL |
| `diff` | `JSONB` | YES | NULL |
| `request_id` | `VARCHAR(64)` | YES | NULL |
| `session_id` | `VARCHAR(64)` | YES | NULL |
| `risk_level` | `VARCHAR(20)` | NO | `'low'` |

**Partition**: `RANGE(created_at)` — Quarterly

## Domain Events — Sprint 1
`OrganizationCreated` | `UserRegistered` | `UserEmailVerified` | `UserLoggedIn` | `UserLockedOut` | `MemberJoined` | `MemberRoleChanged` | `InvitationSent` | `InvitationAccepted` | `FeatureFlagToggled`

---

# SPRINT 2 — IDENTITY & ACCESS MANAGEMENT

## Table List

| # | Table | Description |
|---|-------|-------------|
| 10 | `roles` | Named permission bundles |
| 11 | `permissions` | Atomic capability declarations |
| 12 | `role_permissions` | Role ↔ Permission junction |
| 13 | `user_roles` | User ↔ Role (org-scoped) |
| 14 | `user_sessions` | Active sessions (partitioned) |
| 15 | `refresh_tokens` | Rotating tokens with family |
| 16 | `password_reset_tokens` | Short-lived reset tokens |
| 17 | `api_keys` | Long-lived programmatic keys |
| 18 | `oauth_providers` | SSO configuration |
| 19 | `oauth_accounts` | User linked OAuth accounts |
| 20 | `security_policies` | Org-level security rules |

## Key Design Rules

- `refresh_tokens.family_id`: Family compromise detection — reuse of consumed token revokes entire family
- `api_keys.key_hash`: SHA-256, never store plaintext key
- `oauth_accounts`: Supports Google, Microsoft, GitHub, Okta, SAML
- `security_policies`: 1:1 per organization (UNIQUE on `organization_id`)
- `user_sessions`: PARTITION BY RANGE(created_at) Monthly

## Domain Events — Sprint 2
`UserSessionCreated` | `UserSessionRevoked` | `RefreshTokenRotated` | `TokenFamilyCompromised` | `APIKeyCreated` | `APIKeyRevoked` | `PasswordChanged` | `MFAEnabled` | `RoleGranted`

---

# SPRINT 3 — AI GATEWAY

## Table List

| # | Table | Description |
|---|-------|-------------|
| 21 | `ai_providers` | Provider registry (platform) |
| 22 | `ai_models` | Model capabilities & pricing |
| 23 | `ai_provider_keys` | Encrypted API keys (org-scoped) |
| 24 | `ai_provider_health` | Health monitoring |
| 25 | `ai_routing_policies` | Routing strategy configs |
| 26 | `ai_routing_logs` | Routing decisions |
| 27 | `ai_failover_events` | Failover audit |
| 28 | `ai_requests` | **PARTITIONED** — every request |
| 29 | `ai_usage` | Aggregated usage counters |
| 30 | `ai_costs` | Cost tracking |
| 31 | `ai_org_limits` | Per-org quotas |
| 32 | `ai_cache_entries` | Semantic/exact cache |
| 33 | `ai_quota_usages` | Quota consumption |
| 34 | `ai_security_policy_rules` | AI security rules |
| 35 | `ai_security_events` | Security violations |
| 36 | `ai_scan_logs` | Prompt scanning |

## Critical Design Notes

- `ai_requests`: PARTITION BY RANGE(created_at) DAILY — highest volume table
- `ai_models.input_token_price`: NUMERIC(12,8) — sub-cent precision required
- `ai_org_limits`: Hard limit enforcement — blocks requests when exhausted
- `ai_cache_entries`: Semantic cache saves ~50% token costs at scale

## Domain Events — Sprint 3
`AIRequestCompleted` | `AIRequestFailed` | `AIProviderHealthChanged` | `AIFailoverTriggered` | `AIBudgetThresholdReached` | `AIBudgetExhausted` | `AIRateLimitExceeded` | `AISecurityEventDetected` | `AICacheHit`

---

# SPRINT 4 — PROMPT PLATFORM

## Table List

| # | Table | Description |
|---|-------|-------------|
| 37 | `prompt_collections` | Organizational grouping |
| 38 | `prompt_folders` | Sub-folders |
| 39 | `prompt_categories` | Classification |
| 40 | `prompt_tags` | Flexible tags |
| 41 | `prompt_tags_association` | Many-to-many junction |
| 42 | `prompts` | Core prompt entity |
| 43 | `prompt_versions` | Version history |
| 44 | `prompt_variables` | Variable definitions |
| 45 | `prompt_shares` | Share tokens |
| 46 | `prompt_favorites` | User favorites |
| 47 | `prompt_executions` | Execution history |
| 48 | `prompt_evaluations` | Quality scores |
| 49 | `prompt_analytics` | Aggregated metrics |
| 50 | `prompt_templates` | System templates |
| 51 | `prompt_audit_logs` | Prompt-level audit |
| 52 | `prompt_comments` | Collaboration |
| 53 | `prompt_test_cases` | Test scenarios |
| 54 | `prompt_releases` | Production releases |
| 55 | `prompt_version_history` | Event log |
| 56 | `prompt_ab_tests` | A/B test definitions |
| 57 | `prompt_ab_test_results` | Results (partitioned) |

## Gaps in Existing Models (Must Fix)

| Gap | Table | Fix |
|-----|-------|-----|
| Missing `created_by`, `updated_by` | `prompts` | Add FK → users.id |
| Missing `system_prompt` column | `prompts` | Add TEXT column |
| Missing `search_vector` | `prompts` | Add TSVECTOR + GIN index |
| Missing `version` | `prompts` | Add INTEGER for optimistic lock |
| Missing A/B test tables | — | New tables required |

## Domain Events — Sprint 4
`PromptCreated` | `PromptVersionReleased` | `PromptArchived` | `PromptDeleted` | `PromptExecuted` | `PromptEvaluated` | `PromptShared` | `PromptABTestStarted` | `PromptABTestCompleted`

---

# SPRINT 5 — KNOWLEDGE PLATFORM

## Table List

| # | Table | Description |
|---|-------|-------------|
| 58 | `knowledge_collections` | Top-level collection |
| 59 | `knowledge_folders` | Sub-folders |
| 60 | `knowledge_documents` | Document registry |
| 61 | `knowledge_document_versions` | Version history |
| 62 | `document_chunks` | Chunked text |
| 63 | `document_chunk_embeddings` | **pgvector** embeddings |
| 64 | `knowledge_processing_jobs` | Async pipeline |
| 65 | `knowledge_search_history` | Search audit |
| 66 | `knowledge_saved_searches` | Saved queries |
| 67 | `knowledge_permissions` | ACL |
| 68 | `knowledge_tags` | Tagging system |
| 69 | `knowledge_document_tags` | Junction |
| 70 | `knowledge_retrieval_logs` | RAG retrieval audit |

## Critical: Vector Search Design

```sql
-- SEPARATE embeddings table for optimal indexing
CREATE TABLE document_chunk_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL,
  embedding vector(1536) NOT NULL,  -- pgvector
  embedding_model VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index for ANN search (p95 < 45ms at 10M vectors)
CREATE INDEX idx_embeddings_hnsw
  ON document_chunk_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

## Domain Events — Sprint 5
`DocumentUploaded` | `DocumentIndexed` | `DocumentProcessingFailed` | `DocumentChunked` | `EmbeddingGenerated` | `KnowledgeSearched` | `CollectionShared`

---

# SPRINT 6 — AI AGENTS

## Table List

| # | Table | Description |
|---|-------|-------------|
| 71 | `agent_definitions` | Agent blueprint |
| 72 | `agent_sessions` | Conversation context |
| 73 | `agent_runs` | Execution step |
| 74 | `agent_logs` | Step-level logs |
| 75 | `agent_memories` | Short/long-term memory |
| 76 | `conversation_memories` | Compressed summaries |
| 77 | `organization_memories` | Org shared context |
| 78 | `agent_tools` | Tool registry |
| 79 | `agent_tool_executions` | Tool call audit (partitioned) |
| 80 | `agent_knowledge_bindings` | Agent ↔ Knowledge |
| 81 | `agent_analytics` | Aggregated metrics |

## Domain Events — Sprint 6
`AgentCreated` | `AgentSessionStarted` | `AgentExecuted` | `AgentCompleted` | `AgentFailed` | `AgentToolCalled` | `MemoryConsolidated`

---

# SPRINT 7 — WORKFLOW ENGINE

## Table List

| # | Table | Description |
|---|-------|-------------|
| 82 | `workflow_definitions` | Workflow blueprint |
| 83 | `workflow_versions` | Version snapshots |
| 84 | `workflow_executions` | Runtime instances |
| 85 | `workflow_steps` | Step executions |
| 86 | `workflow_triggers` | Trigger configs |
| 87 | `workflow_schedules` | Cron definitions |
| 88 | `workflow_templates` | Reusable templates |
| 89 | `workflow_analytics` | Aggregated metrics |

## Domain Events — Sprint 7
`WorkflowCreated` | `WorkflowActivated` | `WorkflowCompleted` | `WorkflowFailed` | `WorkflowStepCompleted` | `WorkflowStepFailed` | `WorkflowScheduleTriggered` | `WorkflowWebhookTriggered`

---

# SPRINT 8 — MARKETING PLATFORM

## Table List

| # | Table | Description |
|---|-------|-------------|
| 90 | `campaigns` | Campaign entity |
| 91 | `campaign_templates` | Content templates |
| 92 | `campaign_analytics` | Performance metrics |
| 93 | `campaign_audiences` | Audience segments |
| 94 | `campaign_audience_members` | Segment members |
| 95 | `campaign_assets` | Media assets |
| 96 | `campaign_events` | **PARTITIONED DAILY** — events |
| 97 | `campaign_schedules` | Multi-phase scheduling |
| 98 | `content_generators` | AI generation jobs |
| 99 | `content_variants` | Generated variants |
| 100 | `landing_pages` | Campaign pages |
| 101 | `email_campaigns` | Email-specific config |
| 102 | `email_sends` | Individual sends (partitioned) |

## Domain Events — Sprint 8
`CampaignCreated` | `CampaignPublished` | `CampaignCompleted` | `CampaignEventTracked` | `EmailSent` | `EmailDelivered` | `EmailBounced` | `ContactUnsubscribed` | `ConversionTracked`

---

# SPRINT 9 — CRM

## Table List

| # | Table | Description |
|---|-------|-------------|
| 103 | `contacts` | Contact records |
| 104 | `companies` | Company/accounts |
| 105 | `leads` | Lead pipeline |
| 106 | `deals` | Opportunities |
| 107 | `deal_stages` | Stage definitions |
| 108 | `activities` | Interactions |
| 109 | `activity_templates` | Templates |
| 110 | `pipelines` | Pipeline definitions |
| 111 | `contact_tags` | Tags |
| 112 | `contact_tag_assignments` | Junction |
| 113 | `contact_custom_fields` | Custom field defs |
| 114 | `contact_custom_values` | Field values |
| 115 | `contact_segments` | CRM segments |
| 116 | `contact_segment_members` | Members |
| 117 | `email_subscriptions` | GDPR consent |

## CRITICAL FIX REQUIRED

```sql
-- WRONG: Global unique on email (current state)
-- contacts.email has UNIQUE constraint globally

-- CORRECT: Org-scoped unique
ALTER TABLE contacts DROP CONSTRAINT contacts_email_key;
ALTER TABLE contacts ADD CONSTRAINT uq_contacts_email_org
  UNIQUE (organization_id, email) WHERE deleted_at IS NULL;
```

## Domain Events — Sprint 9
`ContactCreated` | `ContactUpdated` | `LeadCreated` | `LeadConverted` | `DealCreated` | `DealWon` | `DealLost` | `ContactUnsubscribed` | `ActivityLogged`

---

# SPRINT 10 — INTEGRATIONS

## Table List

| # | Table | Description |
|---|-------|-------------|
| 118 | `integrations` | Integration registry |
| 119 | `integration_credentials` | Encrypted credentials |
| 120 | `sync_jobs` | Sync operations |
| 121 | `webhook_endpoints` | Outbound webhooks |
| 122 | `webhook_deliveries` | Delivery log (partitioned) |
| 123 | `webhook_events` | Event queue |
| 124 | `integration_field_mappings` | Field maps |
| 125 | `integration_sync_logs` | Sync audit |

## Domain Events — Sprint 10
`IntegrationConnected` | `IntegrationDisconnected` | `SyncJobCompleted` | `WebhookDelivered` | `WebhookFailed` | `OAuthTokenRefreshed`

---

# SPRINT 11 — NOTIFICATIONS

## Table List

| # | Table | Description |
|---|-------|-------------|
| 126 | `notifications` | Records (partitioned) |
| 127 | `notification_preferences` | Per-user preferences |
| 128 | `notification_templates` | Jinja2 templates |
| 129 | `notification_batches` | Batch jobs |
| 130 | `notification_deliveries` | Channel delivery |
| 131 | `notification_digests` | Digest configs |

## Domain Events — Sprint 11
`NotificationCreated` | `NotificationRead` | `NotificationDelivered` | `NotificationFailed` | `DigestSent`

---

# SPRINT 12 — BILLING

## Table List

| # | Table | Description |
|---|-------|-------------|
| 132 | `billing_plans` | Plan definitions |
| 133 | `plan_features` | Feature matrix |
| 134 | `subscriptions` | Active subscriptions |
| 135 | `subscription_items` | Line items |
| 136 | `invoices` | Invoice records |
| 137 | `invoice_line_items` | Line items |
| 138 | `payments` | Transactions |
| 139 | `payment_methods` | Stored methods |
| 140 | `usage_records` | Metering events |
| 141 | `credits` | Balance management |
| 142 | `credit_transactions` | **IMMUTABLE LEDGER** |
| 143 | `billing_alerts` | Threshold alerts |
| 144 | `promo_codes` | Discount codes |
| 145 | `promo_code_redemptions` | Redemptions |

## RULE: `credit_transactions` is APPEND-ONLY

No UPDATE. No DELETE. Running balance is computed via running SUM.

## Domain Events — Sprint 12
`SubscriptionCreated` | `SubscriptionUpgraded` | `SubscriptionCancelled` | `InvoiceGenerated` | `InvoicePaid` | `PaymentFailed` | `CreditPurchased` | `CreditExhausted` | `TrialExpiring`

---

# SPRINT 13 — ANALYTICS

## Table List

| # | Table | Description |
|---|-------|-------------|
| 146 | `analytics_snapshots` | Metric snapshots (partitioned) |
| 147 | `analytics_dashboards` | Dashboard definitions |
| 148 | `analytics_widgets` | Widget configs |
| 149 | `analytics_reports` | Report definitions |
| 150 | `analytics_report_runs` | Execution history |
| 151 | `analytics_events` | Raw event stream |
| 152 | `analytics_funnels` | Funnel definitions |
| 153 | `analytics_funnel_steps` | Steps |
| 154 | `analytics_cohorts` | Cohort definitions |

## Domain Events — Sprint 13
`MetricSnapshotCreated` | `ReportGenerated` | `DashboardCreated`

---

# SPRINT 14 — SECURITY

## Table List

| # | Table | Description |
|---|-------|-------------|
| 155 | `security_incidents` | Incident records |
| 156 | `threat_detections` | Automated detection |
| 157 | `compliance_frameworks` | Framework configs |
| 158 | `compliance_controls` | Control requirements |
| 159 | `compliance_assessments` | Assessment results |
| 160 | `data_classification_rules` | Sensitivity rules |
| 161 | `pii_scan_results` | PII detection |
| 162 | `security_alerts` | Alert records |
| 163 | `ip_allowlists` | IP management |
| 164 | `security_event_log` | **HIGH VOLUME** (partitioned daily) |

## Domain Events — Sprint 14
`SecurityIncidentCreated` | `ThreatDetected` | `ComplianceAssessmentCompleted` | `PiiDetected` | `SecurityPolicyViolation`

---

# SPRINT 15 — ADMINISTRATION

## Table List

| # | Table | Description |
|---|-------|-------------|
| 165 | `system_configurations` | Global platform config |
| 166 | `maintenance_windows` | Scheduled maintenance |
| 167 | `support_tickets` | Support cases |
| 168 | `support_ticket_messages` | Ticket messages |
| 169 | `impersonation_logs` | **IMMUTABLE** admin audit |
| 170 | `platform_announcements` | System announcements |
| 171 | `admin_action_logs` | Super-admin audit |
| 172 | `system_health_snapshots` | Infrastructure health |
| 173 | `rate_limit_overrides` | Per-org overrides |

## Domain Events — Sprint 15
`MaintenanceWindowScheduled` | `AnnouncementPublished` | `AdminImpersonationStarted` | `SystemConfigChanged` | `SupportTicketCreated` | `SupportTicketResolved`

---

# FINAL ARCHITECTURE SUMMARY

## Global Registry

| Sprint | Module | Tables |
|--------|--------|--------|
| 1 | core | 9 |
| 2 | iam | 11 |
| 3 | ai_gateway | 16 |
| 4 | prompt | 21 |
| 5 | knowledge | 13 |
| 6 | agent | 11 |
| 7 | workflow | 8 |
| 8 | marketing | 13 |
| 9 | crm | 15 |
| 10 | integration | 8 |
| 11 | notification | 6 |
| 12 | billing | 14 |
| 13 | analytics | 9 |
| 14 | security | 10 |
| 15 | admin | 9 |
| **TOTAL** | **15 modules** | **173 tables** |

## Totals

| Metric | Count |
|--------|-------|
| Total Tables | 173 |
| Total Indexes | 256 |
| Composite Indexes | 86 |
| GIN Indexes | 6 |
| Partial Indexes | 51 |
| HNSW Indexes | 1 |
| Partitioned Tables | 15 |
| Domain Events | 89 |
| Foreign Key Relationships | 280+ |

## Partitioned Tables Summary

| Table | Strategy | Granularity | Volume |
|-------|----------|------------|--------|
| `ai_requests` | RANGE(created_at) | Daily | 500M/yr |
| `campaign_events` | RANGE(created_at) | Daily | 500M/yr |
| `security_event_log` | RANGE(created_at) | Daily | 200M/yr |
| `agent_tool_executions` | RANGE(created_at) | Daily | 50M/yr |
| `webhook_deliveries` | RANGE(created_at) | Daily | 10M/yr |
| `platform_events` | RANGE(created_at) | Monthly | 100M/yr |
| `audit_logs` | RANGE(created_at) | Quarterly | 50M/yr |
| `user_sessions` | RANGE(created_at) | Monthly | 20M/yr |
| `notifications` | RANGE(created_at) | Monthly | 50M/yr |
| `analytics_snapshots` | RANGE(created_at) | Monthly | 10M/yr |
| `credit_transactions` | RANGE(created_at) | Monthly | 10M/yr |
| `email_sends` | RANGE(created_at) | Monthly | 100M/yr |
| `knowledge_retrieval_logs` | RANGE(created_at) | Weekly | 20M/yr |
| `prompt_ab_test_results` | RANGE(created_at) | Monthly | 5M/yr |
| `document_chunk_embeddings` | HASH(organization_id) | 8 buckets | 100M rows |

## Critical Technical Debt (Must Fix BEFORE Backend)

| Priority | Issue | Table | Fix |
|----------|-------|-------|-----|
| 🔴 CRITICAL | Global UNIQUE on email | `contacts` | Change to org-scoped partial unique |
| 🔴 CRITICAL | Missing `created_by`/`updated_by` | Multiple | Add FK columns |
| 🔴 CRITICAL | Missing `deleted_at` | Multiple models | Add soft-delete columns |
| 🟠 HIGH | Missing `version` column | Most models | Add INTEGER for optimistic locking |
| 🟠 HIGH | String PKs in infrastructure | `background_jobs` etc. | Standardize to UUID |
| 🟡 MEDIUM | Missing `search_vector` | contacts, prompts | Add TSVECTOR + GIN index |
| 🟡 MEDIUM | Missing HNSW index on embeddings | `document_chunks` | Separate embeddings table |
| 🟢 LOW | SafeVector Text fallback | `document_chunks` | pgvector only in production |

## Zero Tenant Leakage

```sql
-- Row-Level Security (RLS) — Mandatory
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON prompts
  FOR ALL TO app_user
  USING (organization_id = current_setting('app.organization_id')::uuid);
```

Every API endpoint MUST inject `organization_id` from JWT before any query executes.

## Databricks CDC Architecture

```
PostgreSQL (Operational)
    └── Debezium CDC Connector
         └── Kafka Topic per Table
              └── Databricks Auto Loader
                   ├── Bronze Layer (Raw CDC events)
                   ├── Silver Layer (Cleaned, typed, deduplicated)
                   └── Gold Layer (Business aggregations, ML features)
```

---

*EAIMOS Enterprise Database Design v1.0.0*  
*DO NOT start backend implementation until all 15 sprints are reviewed and approved*
