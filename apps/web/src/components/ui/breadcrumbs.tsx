'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';

const segmentLabels: Record<string, string> = {
  dashboard: 'Home',
  crm: 'CRM Module',
  ai: 'AI Platform',
  providers: 'Providers',
  models: 'Models',
  health: 'Health Center',
  admin: 'Admin Console',
  usage: 'Usage',
  router: 'Router',
  security: 'Security Center',
  infrastructure: 'Infrastructure',
  observability: 'Observability',
  playground: 'Playground',
  workspace: 'AI Workspace',
  sandbox: 'AI Sandbox',
  'agent-sandbox': 'Agent Sandbox',
  conversations: 'Conversations',
  compare: 'Compare Lab',
  prompts: 'Prompt Platform',
  knowledge: 'Knowledge Platform',
  documents: 'Documents',
  files: 'Files',
  collections: 'Collections',
  search: 'Semantic Search',
  upload: 'Upload Center',
  embeddings: 'Vector Embeddings',
  agents: 'AI Agents',
  workflows: 'Workflow Engine',
  campaigns: 'Marketing Platform',
  settings: 'Settings',
  users: 'Users & Teams',
  integrations: 'Integrations',
  analytics: 'Analytics',
  'image-studio': 'Image Studio',
  'social-studio': 'Social Studio',
  generator: 'Content Generator',
  leads: 'Leads',
  companies: 'Companies',
  contacts: 'Contacts',
};

export function Breadcrumbs() {
  const pathname = usePathname();

  const segments = React.useMemo(() => {
    if (!pathname) return [];
    return pathname.split('/').filter(Boolean);
  }, [pathname]);

  if (segments.length <= 1) {
    return null; // Don't show breadcrumbs on the root /dashboard page
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-neutral-500 py-2 select-none">
      <Link
        href="/dashboard"
        className="flex items-center gap-1 hover:text-white transition-colors"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>

      {segments.map((segment, index) => {
        const isLast = index === segments.length - 1;
        const path = `/${segments.slice(0, index + 1).join('/')}`;
        const label = segmentLabels[segment.toLowerCase()] || segment.replace(/[-_]/g, ' ');

        return (
          <React.Fragment key={path}>
            <ChevronRight className="w-3 h-3 text-neutral-600 shrink-0" />
            {isLast ? (
              <span className="text-neutral-200 font-medium truncate max-w-[200px]">
                {label}
              </span>
            ) : (
              <Link
                href={path}
                className="hover:text-white transition-colors truncate max-w-[150px]"
              >
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
