# Sprint 5: Campaigns (A/B Testing, Templates, Execution) - Implementation Plan

This plan details the implementation of the Campaigns module for Viptant. The Campaigns module manages marketing campaigns, A/B creative templates (Variant A and Variant B content), simulated delivery executions, and granular event tracking metrics, isolated by tenant.

## User Review Required

> [!IMPORTANT]
> **Multi-Tenant Isolation:**
> - All campaign tables (`campaigns`, `campaign_templates`, `campaign_analytics`) include an `organization_id` column to guarantee complete logical tenant isolation.
> - API routers validate membership scopes and query items matching the active tenant identifier supplied in the request header (`X-Organization-ID`).

## Proposed Changes

### 1. Database Schema

We define three new database models under `apps/api/src/api/models/campaign.py`:

#### [NEW] [campaign.py](file:///d:/markai/apps/api/src/api/models/campaign.py)
*   **`campaigns`**: Tracks campaign attributes, status (`DRAFT`, `SCHEDULED`, `ACTIVE`, `COMPLETED`, `ARCHIVED`), budgets, and target channel.
*   **`campaign_templates`**: Configures A/B template details (Variant A vs Variant B marketing copy content).
*   **`campaign_analytics`**: Aggregates impressions, clicks, conversions, and revenue per variant.

---

### 2. Repositories

We define database access logic in `apps/api/src/api/repositories/`:

#### [NEW] [base.py](file:///d:/markai/apps/api/src/api/repositories/base.py)
*   Provides a generic base repository handling CRUD actions, soft deletes, and organization filtering context.

#### [NEW] [campaign.py](file:///d:/markai/apps/api/src/api/repositories/campaign.py)
*   Extends base repository for campaign-specific lookup constraints.

---

### 3. API Endpoints

We create CRUD and metrics tracking routers under `/api/v1/campaigns/`:
*   `POST /api/v1/campaigns/` - Create a new campaign, template, and analytics tracker.
*   `GET /api/v1/campaigns/` - List all active campaigns for organization.
*   `GET /api/v1/campaigns/{id}` - Retrieve campaign details.
*   `PUT /api/v1/campaigns/{id}` - Modify details and transition states.
*   `DELETE /api/v1/campaigns/{id}` - Soft-delete campaign.
*   `POST /api/v1/campaigns/{id}/execute` - Trigger simulated execution.
*   `POST /api/v1/campaigns/{id}/track` - Record clicks/impressions/conversions variant actions.

---

## Verification Plan

### Automated Tests
*   Write test suite `apps/api/tests/test_campaigns.py` verifying full lifecycle, validation rules, A/B performance tracking, and multi-tenant security blocks.
*   Run tests: `poetry run pytest tests/test_campaigns.py`
