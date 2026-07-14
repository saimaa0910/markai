import { apiClient } from '@/services/api-client';
import { Prompt, PromptVersion } from '../types';

export const PromptsAPI = {
  // List latest prompt families
  listPrompts: async (): Promise<Prompt[]> => {
    const res = await apiClient.get('/ai/prompts/');
    const data = res.data || [];
    return data.map((p: any) => ({
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: false, // Synced with Zustand store favorites
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    }));
  },

  // Get prompt latest version
  getPrompt: async (name: string): Promise<Prompt> => {
    const res = await apiClient.get(`/ai/prompts/${name}`);
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Get prompt version history
  getPromptHistory: async (name: string): Promise<PromptVersion[]> => {
    const res = await apiClient.get(`/ai/prompts/${name}/history`);
    const data = res.data || [];
    return data.map((p: any) => ({
      id: p.id,
      name: p.name,
      content: p.content,
      version: p.version,
      comment: `Released version v${p.version}`,
      created_by: 'system@viptant.com',
      created_at: p.created_at || new Date().toISOString(),
    }));
  },

  // Create or register new prompt family/version
  createPrompt: async (prompt: Omit<Prompt, 'id' | 'created_at' | 'organization_id' | 'variables' | 'is_favorite'>): Promise<Prompt> => {
    const res = await apiClient.post('/ai/prompts/', {
      name: prompt.name,
      content: prompt.content,
      category: prompt.category,
      tags: prompt.tags ? prompt.tags.join(',') : undefined,
      is_shared: prompt.is_shared,
      version: prompt.version,
    });
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Update prompt version (which increments version number or modifies family attributes)
  updatePrompt: async (
    name: string,
    prompt: { content?: string; category?: string; tags?: string[]; is_shared?: boolean }
  ): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}`, {
      content: prompt.content,
      category: prompt.category,
      tags: prompt.tags ? prompt.tags.join(',') : undefined,
      is_shared: prompt.is_shared,
    });
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Delete prompt family
  deletePrompt: async (name: string): Promise<void> => {
    await apiClient.delete(`/ai/prompts/${name}`);
  },
};

// Internal utility helper
function extractVariables(content: string): string[] {
  const matches = content.match(/\{\{([^}]+)\}\}/g);
  return matches ? [...new Set(matches.map((m) => m.replace(/[{}]/g, '').trim()))] : [];
}
export { extractVariables };
