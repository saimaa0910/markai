# Frontend Documentation: MarkAI Client Application

This document provides a comprehensive overview of the MarkAI frontend client application, details its architecture, core technologies, page structures, components, and key features built up to Sprint 4.

---

## 1. Technology Stack

The client application is a modern web application designed for high performance, type safety, and rich responsiveness:

- **Framework**: Next.js 16 (App Router architecture)
- **Styling**: Tailwind CSS v4 & Lucide React for consistent modern iconography
- **State Management**: 
  - **Zustand**: Handles global auth state, active tenant (organization) profiles, and token persistence (stored in `localStorage`).
  - **TanStack React Query**: Manages server state cache, mutations, queries, and auto-invalidation of data hooks.
- **Form Validation**: Standard React state integrated with schema-based input parsing.
- **HTTP Client**: Axios instance configured with dynamic request interceptors injecting JWT bearer tokens and tenant headers (`organization-id`).

---

## 2. Directory Architecture

The frontend follows a modular architecture under `apps/web/src/`:

```
apps/web/src/
├── app/                  # Next.js App Router (Layouts & Pages)
│   ├── auth/            # Auth pages (Login & Register)
│   ├── dashboard/       # Core dashboard app (CRM, AI, Campaigns, Generator, Settings)
│   ├── layout.tsx       # Root document layout
│   └── page.tsx         # Public marketing landing page
├── components/           # Reusable UI component blocks
│   ├── landing/         # Marketing homepage sections (Hero, Showcase, Pricing, etc.)
│   └── ui/              # Atom-level widgets (Button, Dialog, Input, Skeleton, Toast)
├── layouts/              # Specialized wrapper templates
├── providers/            # React context providers (QueryClient, Auth, etc.)
├── services/             # API request layer & integrations
│   └── api-client.ts    # Centralized HTTP Client configuration
└── store/                # Zustand client state stores
    ├── auth.ts          # Authentication & organization workspace state
    └── ui.ts            # Sidebar & UI controls state
```

---

## 3. Implemented Modules & Frontend Panels

### 🔑 Authentication & Signup (`/auth`)
- **Login (`/auth/login`)**: Secure username/password form with automatic credentials token resolution (Access & Refresh JWT validation).
- **Registration (`/auth/register`)**: Tenant auto-creation upon sign-up; registers the user and auto-generates the first organization namespace slug.
- **Tenant Management**: Persistent authentication store (`useAuthStore`) keeps the active workspace cookie/header synchronized.

### 📊 Dashboard & Workspace Home (`/dashboard`)
- Multi-tenant workspace switcher dropdown: allows fast contextual swapping of the active organization.
- Modular layout displaying overall tenant statistics and quick-access pathways.

### 👥 Multi-Tenant CRM Panel (`/dashboard/crm`)
- **Tab Layout**: Seamlessly toggles between **Leads**, **Contacts**, and **Companies**.
- **Interactive Forms**: Instant client insertion/modification.
- **KPI Dashcards**: Auto-computes vital metrics like:
  - **Total Pipeline Value** (aggregated from active leads).
  - **Active Leads Counter**.
- **Tenant Security**: All listing and creation payloads are implicitly isolated on the server using the client's current `organization-id` header.

### 🤖 AI Playground (`/dashboard/ai`)
- **Split-Screen Layout**:
  - **Left Panel**: Saved prompt templates library, session folder organization, and quick-variables selector.
  - **Right Panel**: Conversational streaming interface supporting message threads.
- **Variables Injector**: Dynamically extracts placeholder template variables (e.g. `{{company_name}}`) and builds user inputs for rendering structured prompts.
- **Model Selector**: Allows selection of provider endpoints (OpenAI, Gemini, Claude) through a centralized backend `LLMGateway`.

### ✍️ Playful Copy Generator (`/dashboard/generator`)
- **Prompt Engineering Sidebar**: Tone selector (Professional, Creative, Witty, Academic), copywriting template categories (Email templates, social posts, Google Ads campaigns), and custom target audience settings.
- **A/B Variant Cards**: Comparative side-by-side layout rendering generated drafts:
  - **Variant A**: Creative narrative hook.
  - **Variant B**: Direct CTA action hook.
- **Ratings & Scoring**: Interactive star rating (1-5 stars) to tag and rank successful copy variations.

### 📢 Multi-Channel Campaigns (`/dashboard/campaigns`)
- **Unified Campaign Wizard**: Interactive step-by-step creation flow for defining targeted outreach campaigns.
- **Channels Supported**: Email, LinkedIn Ads, Google AdWords, and Social Media posts.
- **Performance Analytics**: At-a-glance KPI cards tracking campaign delivery metrics:
  - Sent count
  - Open rates
  - Click-through-rates (CTR)
- **Controls**: In-line actions to pause, resume, or delete campaign sequences.

### ⚙️ Workspace Settings (`/dashboard/settings`)
- **Organization Settings**: Create secondary workspaces and edit organization metadata.
- **API Keys Workspace**: Provision and revoke custom developer tokens (`ea_live_...`) to access the system programmatically.
- **Integrations Tab**: Visual toggles to bind external applications:
  - Slack Webhooks (real-time performance alerts).
  - Gmail Connector (outbound mail synchronization).
  - Google Drive (knowledge base document ingestion).
  - OpenAI API developer bypass keys.
- **Billing**: Form interfaces and dashboard for subscription tier management.

---

## 4. Public Homepage Components (`src/components/landing/`)

The application features a premium, responsive landing page loaded with modular components for a modern marketing experience:
- **Hero & Header**: Vibrant typography, navigation links, and modern CTA pathways.
- **Showcase & Platform**: Visual breakdowns of the platform features with dynamic interactive mockups.
- **Comparison & Workflow**: Before/after breakdowns highlighting the value of collaborative AI workflows.
- **Integrations & Trust**: Partner logo grid and customer review stories.
- **Pricing**: Dynamic cards detailing individual vs. organization tier packages.
- **FAQ & Footer**: Accordion questions and structured sitemap links.
