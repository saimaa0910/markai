# EAIMOS Information Architecture & Navigation Audit

## Executive Summary
This document provides the comprehensive audit of the EAIMOS frontend Information Architecture (IA) and navigation system, detailing the before-and-after state, route hierarchy, feature ownership rules, and integration alignment across the platform.

---

## 1. Information Architecture Comparison

### Before Restructuring (Legacy Navigation)
```
EAIMOS (Unconsolidated)
├── Dashboard (/dashboard)
├── CRM Module (/dashboard/crm)
├── Campaigns (/dashboard/campaigns)
├── Conversations (/dashboard/conversations) [Isolated Top-Level]
├── Analytics (/dashboard/analytics)
├── Integrations (/dashboard/integrations) [Isolated Top-Level]
├── Users & Teams (/dashboard/users) [Isolated Top-Level]
├── Files (/dashboard/files) [Isolated Top-Level]
├── Settings (/dashboard/settings)
├── AI Platform Group (/dashboard/ai/*)
│   ├── Providers, Models, Compare Lab, Health, Admin, Usage, Analytics, Router, Security, Infrastructure, Observability, Settings
├── Playground Group (/dashboard/playground, /dashboard/image-studio, /dashboard/social-studio)
├── Agents Platform Group (/dashboard/agents/*)
│   └── Agent Sandbox (/dashboard/agents/playground)
├── Workflow Studio Group (/dashboard/workflows/*)
├── Knowledge Platform Group (/dashboard/knowledge/*)
└── Prompt Platform Group (/dashboard/prompts/*)
```

### After Restructuring (Target Standardized Architecture)
```
EAIMOS
│
├── Core Platform
│   └── Dashboard (/dashboard)
│
├── AI Platform / AI Gateway
│   ├── Providers (/dashboard/ai/providers)
│   ├── Models (/dashboard/ai/models)
│   ├── Health Center (/dashboard/ai/health)
│   ├── Admin Console (/dashboard/ai/admin)
│   ├── Usage (/dashboard/ai/usage)
│   ├── Analytics (/dashboard/ai/analytics)
│   ├── Router (/dashboard/ai/router)
│   ├── Security Center (/dashboard/ai/security)
│   ├── Infrastructure (/dashboard/ai/infrastructure)
│   └── Observability (/dashboard/ai/observability)
│
├── Playground
│   ├── AI Workspace (/dashboard/playground/workspace)
│   ├── AI Playground / Sandbox (/dashboard/playground/sandbox)
│   ├── Agent Sandbox (/dashboard/playground/agent-sandbox)
│   ├── Conversations (/dashboard/playground/conversations)
│   ├── Compare Lab (/dashboard/playground/compare)
│   ├── Image Studio (/dashboard/playground/image-studio)
│   └── Social Studio (/dashboard/playground/social-studio)
│
├── Prompt Platform
│   └── Prompts (/dashboard/prompts)
│
├── Knowledge Platform
│   ├── Dashboard (/dashboard/knowledge)
│   ├── Documents (/dashboard/knowledge/documents)
│   ├── Files (/dashboard/knowledge/files)
│   ├── Collections (/dashboard/knowledge/collections)
│   ├── Semantic Search (/dashboard/knowledge/search)
│   ├── Upload Center (/dashboard/knowledge/upload)
│   ├── Vector Embeddings (/dashboard/knowledge/embeddings)
│   ├── Analytics (/dashboard/knowledge/analytics)
│   └── Settings (/dashboard/knowledge/settings)
│
├── AI Agents
│   └── Agent Management (/dashboard/agents)
│
├── Workflow Engine
│   └── Workflows (/dashboard/workflows)
│
├── Marketing Platform
│   └── Campaigns (/dashboard/campaigns)
│
├── CRM
│   └── CRM (/dashboard/crm)
│
└── Settings
    ├── Users & Teams (/dashboard/settings/users)
    ├── Integrations (/dashboard/settings/integrations)
    └── Platform Settings (/dashboard/settings)
```

---

## 2. Detailed Audit of Affected Features

| Feature Name | Previous UI Parent | Target UI Parent | Canonical Route | Backward Compatible Route | Backend Domain Ownership |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compare Lab** | AI Platform (Root Submenu) | Playground | `/dashboard/playground/compare` | `/dashboard/ai/compare` | AI Gateway (`/ai/completions/`, `/ai/models/`) |
| **Agent Sandbox** | Agents Platform | Playground | `/dashboard/playground/agent-sandbox` | `/dashboard/agents/playground` | AI Agents (`/agents/`, `/agents/sessions/`) |
| **AI Workspace** | AI Playground | Playground | `/dashboard/playground/workspace` | `/dashboard/playground` | AI Gateway Unified Execution |
| **Conversations** | Standalone Top-Level | Playground | `/dashboard/playground/conversations` | `/dashboard/conversations` | AI Gateway / Chat (`/ai/conversations/`) |
| **Files** | Standalone Top-Level | Knowledge Platform | `/dashboard/knowledge/files` | `/dashboard/files` | Knowledge Platform (`/files/`, RAG Storage) |
| **Users & Teams** | Standalone Top-Level | Settings | `/dashboard/settings/users` | `/dashboard/users` | IAM / Core (`/users/`, `/organizations/`) |
| **Integrations** | Standalone Top-Level | Settings | `/dashboard/settings/integrations` | `/dashboard/integrations` | Integrations Platform (`/integrations/`) |

---

## 3. UI Component Updates

1. **Sidebar Navigation ([dashboard-layout.tsx](file:///d:/markai/apps/web/src/layouts/dashboard-layout.tsx))**:
   - Consolidated 9 clean top-level platforms/groups.
   - Organized Playground submenu with Workspace, Sandbox, Agent Sandbox, Conversations, Compare Lab.
   - Moved Files under Knowledge Platform.
   - Moved Users & Teams and Integrations under Settings.
   - Removed duplicate root navigation items.

2. **Breadcrumbs System ([breadcrumbs.tsx](file:///d:/markai/apps/web/src/components/ui/breadcrumbs.tsx))**:
   - Added complete label mapping for all canonical routes and nested segments.

3. **Command Palette ([command-palette.tsx](file:///d:/markai/apps/web/src/components/ui/command-palette.tsx))**:
   - Updated quick-search items, dynamic conversation links, and file references to route to canonical URLs.
