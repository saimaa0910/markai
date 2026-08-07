import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { PromptsAPI } from '../services/prompts';
import { usePromptsStore } from '../store/prompts';
import { Prompt, PromptVersion, PromptTestingResult } from '../types';
import { toast } from '@/components/ui/toast';

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
import { apiClient } from '@/services/api-client';

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptTesting
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptTesting() {
  const { activeOrg, accessToken } = useAuthStore();
  const [isTesting, setIsTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState<PromptTestingResult | null>(null);
  const [streamOutput, setStreamOutput] = React.useState('');

  const test = React.useCallback(async ({
    provider,
    model,
    content,
    variables,
    systemPrompt,
  }: {
    provider: string;
    model: string;
    content: string;
    variables: Record<string, string>;
    systemPrompt?: string;
  }) => {
    setIsTesting(true);
    setTestResult(null);
    setStreamOutput('');

    let rendered = content;
    Object.entries(variables).forEach(([key, val]) => {
      rendered = rendered.replace(new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g'), val);
    });

    const apiBase = apiClient.defaults.baseURL || '/api/v1';
    
    try {
      const response = await fetch(`${apiBase}/ai/prompts/test/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken || ''}`,
          'X-Organization-ID': activeOrg?.id || '',
        },
        body: JSON.stringify({
          system_prompt: systemPrompt || 'You are a helpful AI assistant.',
          user_prompt: rendered,
          model_name: model,
        }),
      });

      if (!response.ok) {
        throw new Error(`Connection error: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      if (!reader) {
        throw new Error('Readable stream not supported.');
      }

      let buffer = '';
      let textAccumulator = '';
      let metaLatency = 0;
      let metaTokens = 0;
      let metaCost = 0;
      let resProvider = provider;
      let resModel = model;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const cleanLine = line.trim();
          if (cleanLine.startsWith('data: ')) {
            const dataStr = cleanLine.slice(6).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.error) {
                  throw new Error(parsed.error);
                }
                const token = parsed.content || parsed.token || '';
                textAccumulator += token;
                setStreamOutput(textAccumulator);

                if (parsed.latency_ms) metaLatency = parsed.latency_ms;
                if (parsed.prompt_tokens || parsed.completion_tokens) {
                  metaTokens = (parsed.prompt_tokens || 0) + (parsed.completion_tokens || 0);
                }
                if (parsed.cost_usd) metaCost = parsed.cost_usd;
                if (parsed.provider) resProvider = parsed.provider;
                if (parsed.model) resModel = parsed.model;
              } catch (e) {
                // Ignore partial JSON blocks
              }
            }
          }
        }
      }

      setTestResult({
        id: `test-${Date.now()}`,
        provider: resProvider,
        model: resModel,
        prompt_name: 'Sandbox Inferences',
        variables_used: variables,
        output: textAccumulator,
        latency_ms: metaLatency || 120,
        tokens_used: metaTokens || textAccumulator.split(' ').length,
        cost_usd: metaCost || 0.0,
        created_at: new Date().toISOString(),
      });
    } catch (err: any) {
      console.error(err);
      toast.error('Testing failed', err.message || 'Could not run sandbox completions.');
      throw err;
    } finally {
      setIsTesting(false);
    }
  }, [accessToken, activeOrg]);

  return {
    test,
    isTesting,
    testResult,
    streamOutput,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptTemplates
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptTemplates() {
  const templates = [
    { name: 'SaaS Email Welcome', content: 'Design a warm onboarding email message template for {{product_name}} targeting {{customer_name}} in the {{industry}} domain.', category: 'Email', tags: ['email', 'onboarding', 'marketing'] },
    { name: 'SEO Content Outliner', content: 'Generate a top-ranking SEO article outline with H1, H2, H3 tags, targeted keyword clusters for "{{target_keyword}}", and search intent for {{target_audience}}.', category: 'SEO', tags: ['seo', 'content', 'keywords'] },
    { name: 'Sales Cold Outreach', content: 'Draft a personalized, high-converting B2B cold email to {{contact_name}} at {{company}} highlighting how {{product}} solves {{pain_point}}.', category: 'Sales', tags: ['sales', 'outreach', 'b2b'] },
    { name: 'Customer Support Escalation', content: 'Formulate a professional and empathetic customer support resolution letter addressing issue {{ticket_issue}} for user {{user_name}}.', category: 'Customer Support', tags: ['support', 'resolution', 'tickets'] },
    { name: 'Social Media Viral Thread', content: 'Create a 5-part engage-focused social media thread discussing {{topic}} with punchy hooks, call-to-actions, and relevant hashtags.', category: 'Social Media', tags: ['social', 'twitter', 'linkedin'] },
    { name: 'Long-form Blog Generator', content: 'Write an authoritative 1000-word blog post section on {{topic}} using a {{tone}} tone of voice and clear markdown formatting.', category: 'Blog', tags: ['blog', 'writing', 'content'] },
    { name: 'Product Description Copywriter', content: 'Generate a compelling, benefit-focused product description for {{product_name}} highlighting key features {{feature_list}} for target market {{audience}}.', category: 'Product Description', tags: ['ecommerce', 'copywriting', 'product'] },
    { name: 'Meeting Executive Summary', content: 'Summarize the following meeting transcript notes for meeting {{meeting_title}}: extract key decisions, action items with assignees, and deadlines:\n\n{{transcript}}', category: 'Meeting Summary', tags: ['summary', 'productivity', 'meeting'] },
    { name: 'Multi-Language Translator', content: 'Accurately translate the following text from {{source_language}} to {{target_language}} preserving contextual nuances, technical vocabulary, and tone:\n\n{{input_text}}', category: 'Translation', tags: ['translation', 'localization', 'i18n'] },
    { name: 'Clean Code Generator', content: 'Write production-grade, well-commented {{language}} code implementing {{functionality}} following clean architecture, error handling, and type safety principles.', category: 'Code Generation', tags: ['code', 'programming', 'software'] },
    { name: 'SQL Query Architect', content: 'Formulate an optimized SQL query for database engine {{db_engine}} that joins tables {{table_list}} to solve requirement: {{query_requirement}}.', category: 'SQL', tags: ['sql', 'database', 'queries'] },
    { name: 'RAG Knowledge Synthesis', content: 'Synthesize a precise response to user query "{{query}}" strictly using the provided vector search context background:\n\nContext:\n{{knowledge}}\n\nIf answer is unavailable in context, politely decline.', category: 'RAG', tags: ['rag', 'vector', 'retrieval'] },
    { name: 'Enterprise Knowledge QA', content: 'Act as an enterprise AI policy bot. Answer user question "{{question}}" according to organization policy document context:\n\n{{policy_context}}', category: 'Knowledge QA', tags: ['qa', 'enterprise', 'policy'] },
    { name: 'Autonomous Agent System Prompt', content: 'You are an autonomous AI Agent specializing in {{specialty}}. Your goal is {{agent_goal}}. Execute step-by-step reasoning, plan tool invocations, and ensure validation.', category: 'Agent Prompt', tags: ['agent', 'system_prompt', 'autonomous'] },
    { name: 'Workflow Step Automation', content: 'Act as an execution node step in workflow {{workflow_name}}. Process input payload {{input_payload}} and format output JSON matching target schema {{output_schema}}.', category: 'Workflow Prompt', tags: ['workflow', 'automation', 'json'] },
    { name: 'Ad Campaign Copywriting', content: 'Generate 3 high-converting ad copy headline & description variants for {{product_name}} with emotional appeal tailored for {{audience}}.', category: 'Marketing', tags: ['ads', 'copywriting', 'conversion'] },
  ];

  return {
    templates,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
export function usePromptAnalytics() {
  const { activeOrg } = useAuthStore();

  const query = useQuery({
    queryKey: ['prompt-dashboard-stats', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/dashboard/stats');
      return res.data;
    },
    enabled: !!activeOrg,
  });

  const defaultStats = {
    totalPrompts: 0,
    totalExecutions: 0,
    avgLatencyMs: 0,
    avgCostUsd: 0.00045,
    successRate: 100.0,
    categoriesBreakdown: [],
  };

  return {
    stats: query.data || defaultStats,
    isLoading: query.isLoading,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook: usePromptProviders
// ─────────────────────────────────────────────────────────────────────────────
export function usePromptProviders(selectedProvider: string = 'groq') {
  const { activeOrg } = useAuthStore();

  const providersQuery = useQuery({
    queryKey: ['ai-providers', activeOrg?.id],
    queryFn: () => PromptsAPI.fetchProviders(),
    enabled: !!activeOrg,
  });

  const modelsQuery = useQuery({
    queryKey: ['ai-provider-models', selectedProvider, activeOrg?.id],
    queryFn: () => PromptsAPI.fetchProviderModels(selectedProvider),
    enabled: !!activeOrg && !!selectedProvider,
  });

  return {
    providers: providersQuery.data || [
      { name: 'groq', is_active: true },
      { name: 'openai', is_active: true },
      { name: 'google', is_active: true },
      { name: 'anthropic', is_active: true },
      { name: 'openrouter', is_active: true },
    ],
    models: modelsQuery.data || [],
    isLoadingProviders: providersQuery.isLoading,
    isLoadingModels: modelsQuery.isLoading,
  };
}
export type { PromptTestingResult };
export type { PromptVersion };
export type { Prompt };
