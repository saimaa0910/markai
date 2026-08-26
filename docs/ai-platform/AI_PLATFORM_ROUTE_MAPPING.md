# EAIMOS Route Mapping & Redirection Specification

## Overview
This specification details all route definitions, layout mappings, HTTP status, and backward-compatibility routing strategies to ensure zero broken bookmarks or deep links across the platform.

---

## 1. Route Table & Layout Hierarchy

| Route Path | Platform Group | Page Component | Layout | Status / Type |
| :--- | :--- | :--- | :--- | :--- |
| `/dashboard` | Core Platform | `Dashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/providers` | AI Platform | `ProvidersPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/models` | AI Platform | `ModelsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/health` | AI Platform | `HealthPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/admin` | AI Platform | `AdminPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/usage` | AI Platform | `UsagePage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/analytics` | AI Platform | `AnalyticsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/router` | AI Platform | `RouterPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/security` | AI Platform | `SecurityPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/infrastructure` | AI Platform | `InfrastructurePage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/ai/observability` | AI Platform | `ObservabilityPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/workspace` | Playground | `PlaygroundPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/sandbox` | Playground | `PlaygroundPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/agent-sandbox` | Playground | `AgentSandboxPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/conversations` | Playground | `ConversationsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/compare` | Playground | `ComparePage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/image-studio` | Playground | `ImageStudioPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/playground/social-studio` | Playground | `SocialStudioPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/prompts` | Prompt Platform | `PromptsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge` | Knowledge Platform | `KnowledgeDashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/documents` | Knowledge Platform | `DocumentsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/files` | Knowledge Platform | `FilesPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/collections` | Knowledge Platform | `CollectionsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/search` | Knowledge Platform | `SearchPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/upload` | Knowledge Platform | `UploadPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/embeddings` | Knowledge Platform | `EmbeddingsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/analytics` | Knowledge Platform | `AnalyticsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/knowledge/settings` | Knowledge Platform | `SettingsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/agents` | AI Agents | `AgentsDashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/workflows` | Workflow Engine | `WorkflowsDashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/campaigns` | Marketing Platform | `CampaignsDashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/crm` | CRM | `CRMDashboard` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/settings/users` | Settings | `UsersPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/settings/integrations` | Settings | `IntegrationsPage` | `DashboardLayout` | Canonical (Static) |
| `/dashboard/settings` | Settings | `SettingsDashboard` | `DashboardLayout` | Canonical (Static) |

---

## 2. Backward-Compatible Legacy Routes

To guarantee that old links, documentation references, and browser bookmarks never encounter a 404 error, legacy routes are maintained via thin shared-component wrappers:

| Legacy Route | Target Canonical Destination | Implementation Strategy |
| :--- | :--- | :--- |
| `/dashboard/files` | `/dashboard/knowledge/files` | Renders shared `FilesPage` |
| `/dashboard/conversations` | `/dashboard/playground/conversations` | Renders shared `ConversationsPage` |
| `/dashboard/ai/compare` | `/dashboard/playground/compare` | Renders shared `ComparePage` |
| `/dashboard/agents/playground` | `/dashboard/playground/agent-sandbox` | Renders shared `AgentSandboxPage` |
| `/dashboard/users` | `/dashboard/settings/users` | Renders shared `UsersPage` |
| `/dashboard/integrations` | `/dashboard/settings/integrations` | Renders shared `IntegrationsPage` |
| `/dashboard/playground` | `/dashboard/playground/workspace` | Renders shared `PlaygroundPage` |
| `/dashboard/ai/playground` | `/dashboard/playground/sandbox` | Renders shared `PlaygroundPage` |
