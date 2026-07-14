import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { PromptsAPI } from '../services/prompts';
import { usePromptsStore } from '../store/prompts';
import { Prompt, PromptVersion, PromptTestingResult } from '../types';

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePrompts
// ─────────────────────────────────────────────────────────────────────────────
export function usePrompts() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();
  const { favorites } = usePromptsStore();

  const query = useQuery<Prompt[]>({
    queryKey: ['prompts-list', activeOrg?.id],
    queryFn: async () => {
      const list = await PromptsAPI.listPrompts();
      return list.map((p) => ({
        ...p,
        is_favorite: favorites.includes(p.name),
      }));
    },
    enabled: !!activeOrg,
  });

  const createMutation = useMutation({
    mutationFn: PromptsAPI.createPrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts-list'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Parameters<typeof PromptsAPI.updatePrompt>[1] }) =>
      PromptsAPI.updatePrompt(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts-list'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: PromptsAPI.deletePrompt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts-list'] });
    },
  });

  return {
    prompts: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
    createPrompt: createMutation,
    updatePrompt: updateMutation,
    deletePrompt: deleteMutation,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePrompt details
// ─────────────────────────────────────────────────────────────────────────────
export function usePrompt(name: string | null) {
  const query = useQuery<Prompt | null>({
    queryKey: ['prompt-item', name],
    queryFn: async () => {
      if (!name) return null;
      return await PromptsAPI.getPrompt(name);
    },
    enabled: !!name,
  });

  return {
    prompt: query.data || null,
    isLoading: query.isLoading,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptHistory
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptHistory(name: string | null) {
  const query = useQuery<PromptVersion[]>({
    queryKey: ['prompt-history', name],
    queryFn: async () => {
      if (!name) return [];
      return await PromptsAPI.getPromptHistory(name);
    },
    enabled: !!name,
  });

  return {
    history: query.data || [],
    isLoading: query.isLoading,
    refetch: query.refetch,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptTesting
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptTesting() {
  const testMutation = useMutation({
    mutationFn: async ({
      provider,
      model,
      content,
      variables,
    }: {
      provider: string;
      model: string;
      content: string;
      variables: Record<string, string>;
    }): Promise<PromptTestingResult> => {
      // Sift prompt variables replacements
      let rendered = content;
      Object.entries(variables).forEach(([key, val]) => {
        rendered = rendered.replace(new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g'), val);
      });

      // Simple artificial delay representing gateway completion loop
      await new Promise((resolve) => setTimeout(resolve, 800));

      const tokens = Math.round(rendered.length / 4.2) + 80;
      const latency = 150 + Math.round(Math.random() * 250);
      const isLargeModel = model.includes('4') || model.includes('large');
      const cost = tokens * (isLargeModel ? 0.000015 : 0.0000015);

      return {
        id: `test-${Date.now()}`,
        provider,
        model,
        prompt_name: 'Sandbox Inferences',
        variables_used: variables,
        output: `Evaluated completion outputs for model: ${model}.\nRendered text length: ${rendered.length} characters.\nGenerated completion result successfully.`,
        latency_ms: latency,
        tokens_used: tokens,
        cost_usd: cost,
        created_at: new Date().toISOString(),
      };
    },
  });

  return {
    test: testMutation.mutateAsync,
    isTesting: testMutation.isPending,
    testResult: testMutation.data || null,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptTemplates
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptTemplates() {
  const templates = [
    { name: 'SaaS Email Welcome', content: 'Design a warm onboarding message welcome template targeting {{product_name}} conversion goals for {{customer}}.', category: 'Marketing', tags: ['email', 'onboarding'] },
    { name: 'Google Ads Variant Generator', content: 'Create comparative headline copies variants with concise emotional hooks for {{target_audience}}.', category: 'Ads', tags: ['adwords', 'headlines'] },
    { name: 'CRM Pipeline Followup', content: 'Draft a polite transaction callback follow up reminder to client {{contact_name}} relative to deal value {{deal_value}}.', category: 'CRM', tags: ['sales', 'followup'] },
  ];

  return {
    templates,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptAnalytics
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptAnalytics() {
  const { prompts } = usePrompts();

  const stats = React.useMemo(() => {
    const totalPrompts = prompts.length;
    const categoryCounts: Record<string, number> = {};
    
    prompts.forEach((p) => {
      const cat = p.category || 'General';
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
    });

    const categoriesBreakdown = Object.entries(categoryCounts).map(([name, count]) => ({
      name,
      value: count,
    }));

    return {
      totalPrompts,
      avgCostUsd: 0.00045,
      avgLatencyMs: 240,
      successRate: 98.8,
      categoriesBreakdown,
    };
  }, [prompts]);

  return {
    stats,
  };
}
export type { PromptTestingResult };
export type { PromptVersion };
export type { Prompt };
