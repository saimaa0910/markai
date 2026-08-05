/**
 * @file index.ts
 * @description Knowledge Base Query Hooks.
 */

import { useQuery } from '@tanstack/react-query';

export function useKnowledgeDocumentsQuery() {
  return useQuery({
    queryKey: ['knowledge-documents'],
    queryFn: async () => {
      // TODO: Call API endpoint GET /api/knowledge/documents
      return [];
    },
  });
}
