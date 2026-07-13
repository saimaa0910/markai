# Sprint 2: CRM (Leads, Contacts, Companies, Activities) - Implementation Plan

This plan details the implementation of the CRM module for EAIMOS. The CRM module manages sales pipelines, business relationships, individual contacts, and client engagement histories, partitioned by organization.

## User Review Required

> [!IMPORTANT]
> **Multi-Tenant Isolation:**
> - All CRM tables (`leads`, `contacts`, `companies`, `activities`) will include an `organization_id` column to guarantee complete logical tenant isolation.
> - API routers will query items matching the active tenant identifier supplied in the request header (`X-Organization-ID`).

## Proposed Changes

### 1. Database Schema

We will define four new database models under `apps/api/src/api/models/`:

#### [NEW] [apps/api/src/api/models/company.py](file:///d:/markai/apps/api/src/api/models/company.py)
Represents a corporate entity.
- `name`: String (255)
- `domain`: String (255), optional
- `industry`: String (100), optional
- `size`: String (50), optional
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/contact.py](file:///d:/markai/apps/api/src/api/models/contact.py)
Represents a personal contact, optionally linked to a company.
- `first_name`: String (100)
- `last_name`: String (100)
- `email`: String (255), indexed
- `phone`: String (50), optional
- `job_title`: String (100), optional
- `company_id`: ForeignKey to companies, optional
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/lead.py](file:///d:/markai/apps/api/src/api/models/lead.py)
Represents a sales prospect.
- `title`: String (255)
- `status`: Enum (`NEW`, `CONTACTED`, `QUALIFIED`, `LOST`)
- `value`: Numeric (10, 2), default 0.00
- `contact_id`: ForeignKey to contacts, optional
- `company_id`: ForeignKey to companies, optional
- `organization_id`: ForeignKey to organizations

#### [NEW] [apps/api/src/api/models/activity.py](file:///d:/markai/apps/api/src/api/models/activity.py)
Log of communications or meetings.
- `type`: Enum (`CALL`, `EMAIL`, `MEETING`, `NOTE`)
- `title`: String (255)
- `description`: Text
- `lead_id`: ForeignKey to leads, optional
- `contact_id`: ForeignKey to contacts, optional
- `organization_id`: ForeignKey to organizations

---

### 2. API Endpoints

We will create CRUD routers under `/api/v1/crm/`:
- **Companies:** `/api/v1/crm/companies/` (`GET`, `POST`, `PUT`, `DELETE`)
- **Contacts:** `/api/v1/crm/contacts/` (`GET`, `POST`, `PUT`, `DELETE`)
- **Leads:** `/api/v1/crm/leads/` (`GET`, `POST`, `PUT`, `DELETE`)
- **Activities:** `/api/v1/crm/activities/` (`GET`, `POST`, `DELETE`)

All endpoints will validate role permissions (e.g. `MEMBER` minimum access) for the active organization.

---

### 3. Frontend UI

We will implement a responsive CRM workspace dashboard in Next.js:
- **`apps/web/src/app/dashboard/crm/page.tsx`**: Tabbed layout showing Leads list, Contacts list, and Companies. Includes forms to create leads, update statuses, and log activities.

---

## Verification Plan

### Automated Tests
- Write test file `apps/api/tests/test_crm.py` to assert companies, contacts, and leads creation, and verify multi-tenant isolation (confirming users cannot access CRM records from other organizations).
- Run: `poetry run pytest tests/test_crm.py`
