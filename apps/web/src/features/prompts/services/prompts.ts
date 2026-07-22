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

  // Delete prompt family (soft archive)
  deletePrompt: async (name: string): Promise<void> => {
    await apiClient.delete(`/ai/prompts/${name}`);
  },

  // Permanent Delete
  permanentDeletePrompt: async (name: string): Promise<void> => {
    await apiClient.delete(`/ai/prompts/${name}/permanent`);
  },

  // Restore archived prompt
  restorePrompt: async (name: string): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}/restore`);
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: p.is_favorite || false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Clone prompt
  clonePrompt: async (name: string, new_name: string): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}/clone?new_name=${encodeURIComponent(new_name)}`);
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

  // List recent prompts
  listRecentPrompts: async (limit: number = 10): Promise<Prompt[]> => {
    const res = await apiClient.get(`/ai/prompts/recent?limit=${limit}`);
    const data = res.data || [];
    return data.map((p: any) => ({
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: p.is_favorite || false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    }));
  },

  // Bulk actions
  bulkAction: async (action: string, prompt_names: string[], payload?: any): Promise<any> => {
    const res = await apiClient.post('/ai/prompts/bulk-action', {
      action,
      prompt_names,
      payload,
    });
    return res.data;
  },

  // Share prompt link creation
  sharePrompt: async (name: string, visibility: string, expires_in_days?: number, is_editable?: boolean): Promise<any> => {
    const res = await apiClient.post(`/ai/prompts/${name}/share`, {
      visibility,
      expires_in_days,
      is_editable,
    });
    return res.data;
  },

  // Get shared prompt via token
  getSharedPrompt: async (token: string): Promise<Prompt> => {
    const res = await apiClient.get(`/ai/prompts/shared/${token}`);
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

  // Multi-modal search
  searchPrompts: async (params: { query?: string; category?: string; tag?: string; is_archived?: boolean }): Promise<Prompt[]> => {
    const res = await apiClient.post('/ai/prompts/search', params);
    const data = res.data || [];
    return data.map((p: any) => ({
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: p.is_shared !== false,
      is_favorite: p.is_favorite || false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    }));
  },
  // Fetch providers from AI Gateway
  fetchProviders: async (): Promise<any[]> => {
    const res = await apiClient.get('/ai/providers/');
    return res.data || [];
  },

  // Fetch models for provider from AI Gateway
  fetchProviderModels: async (providerName: string): Promise<any[]> => {
    const res = await apiClient.get(`/ai/providers/${providerName}/models`);
    return res.data || [];
  },

  // Save Draft
  saveDraft: async (name: string, prompt: { content: string; category?: string; tags?: string[] }): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}/draft`, prompt);
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: true,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Release Draft
  releaseDraft: async (name: string, notes?: string): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}/release?release_notes=${encodeURIComponent(notes || '')}`);
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: true,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },

  // Purge Prompt (Permanent Delete Cascade)
  purgePrompt: async (name: string): Promise<void> => {
    await apiClient.delete(`/ai/prompts/${name}/purge`);
  },

  // Rollback version
  rollbackPrompt: async (name: string, targetVersion: number): Promise<Prompt> => {
    const res = await apiClient.post(`/ai/prompts/${name}/rollback?target_version=${targetVersion}`);
    const p = res.data;
    return {
      id: p.id,
      name: p.name,
      content: p.content,
      category: p.category || 'General',
      tags: p.tags ? p.tags.split(',').map((t: string) => t.trim()) : [],
      version: p.version || 1,
      is_shared: true,
      is_favorite: false,
      created_at: p.created_at || new Date().toISOString(),
      organization_id: p.organization_id,
      variables: extractVariables(p.content),
    };
  },
};

// Internal utility helper
function extractVariables(content: string): string[] {
  const matches = content.match(/\{\{([^}]+)\}\}/g);
  return matches ? [...new Set(matches.map((m) => m.replace(/[{}]/g, '').trim()))] : [];
}
export { extractVariables };
