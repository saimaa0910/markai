'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/ui/empty-state';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare, Trash2, Download, Search, Bot, User,
  Clock, X, Edit2, Plus, Send, Cpu, Sparkles, StopCircle,
  RefreshCw, Sliders, Database, Check
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
  provider_used?: string;
  latency_ms?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  cost_usd?: number;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string;
  message_count?: number;
}

interface AIModel {
  id: string;
  name?: string;
  model_name: string;
  provider: string;
  context_window: number;
  input_token_price: number;
  output_token_price: number;
  supports_streaming: boolean;
  supports_vision: boolean;
  supports_tool_calling: boolean;
  supports_json: boolean;
  is_active?: boolean;
  is_healthy?: boolean;
  is_favorite?: boolean;
}

interface PromptTemplate {
  id: string;
  name: string;
  content: string;
  description?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Native High-Fidelity Markdown Parser
// ─────────────────────────────────────────────────────────────────────────────
function Markdown({ text }: { text: string }) {
  if (!text) return null;

  // Split content by code blocks (```)
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2 text-xs text-neutral-200">
      {parts.map((part, idx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          // Parse language and code
          const codeLines = part.slice(3, -3).trim().split('\n');
          const firstLine = codeLines[0] || '';
          const lang = firstLine.length < 15 && !firstLine.includes(' ') ? firstLine : '';
          const code = lang ? codeLines.slice(1).join('\n') : codeLines.join('\n');
          
          return (
            <div key={idx} className="my-3 rounded-lg border border-white/10 bg-neutral-950 overflow-hidden font-mono text-[11px]">
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/5 bg-neutral-900 text-neutral-400 text-[10px]">
                <span>{lang ? lang.toUpperCase() : 'CODE'}</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(code);
                    toast.success('Copied', 'Code copied to clipboard.');
                  }}
                  className="hover:text-white transition-all text-violet-400 flex items-center gap-1"
                >
                  Copy
                </button>
              </div>
              <pre className="p-3 overflow-x-auto text-neutral-300">
                <code>{code}</code>
              </pre>
            </div>
          );
        }

        const lines = part.split('\n');
        return (
          <div key={idx} className="space-y-1.5">
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();
              if (!trimmed) return <div key={lIdx} className="h-2" />;

              // Headers
              if (trimmed.startsWith('# ')) {
                return <h1 key={lIdx} className="text-sm font-bold text-white mt-3 mb-1.5 border-b border-white/5 pb-1">{trimmed.slice(2)}</h1>;
              }
              if (trimmed.startsWith('## ')) {
                return <h2 key={lIdx} className="text-xs font-semibold text-white mt-2.5 mb-1">{trimmed.slice(3)}</h2>;
              }
              if (trimmed.startsWith('### ')) {
                return <h3 key={lIdx} className="text-[11px] font-semibold text-white mt-2 mb-1">{trimmed.slice(4)}</h3>;
              }

              // Bullet lists
              if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                return (
                  <ul key={lIdx} className="list-disc list-inside pl-2 text-neutral-300">
                    <li className="mt-0.5">{trimmed.slice(2)}</li>
                  </ul>
                );
              }

              // Bold text parser
              const renderBoldText = (str: string) => {
                const boldParts = str.split(/(\*\*.*?\*\*)/g);
                return boldParts.map((bp, bIdx) => {
                  if (bp.startsWith('**') && bp.endsWith('**')) {
                    return <strong key={bIdx} className="font-bold text-violet-300">{bp.slice(2, -2)}</strong>;
                  }
                  return bp;
                });
              };

              // Check for table lines
              if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
                if (trimmed.replace(/[\s\-|\|]/g, '') === '') return null;
                const cells = trimmed.split('|').slice(1, -1).map(c => c.trim());
                return (
                  <div key={lIdx} className="overflow-x-auto my-1 border border-white/5 rounded">
                    <table className="min-w-full border-collapse text-[10px]">
                      <tbody>
                        <tr className="bg-white/5">
                          {cells.map((cell, cIdx) => (
                            <td key={cIdx} className="border-r border-white/5 last:border-r-0 px-2 py-1 text-neutral-300">
                              {renderBoldText(cell)}
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                );
              }

              return <p key={lIdx} className="text-neutral-300 leading-relaxed text-[11px]">{renderBoldText(line)}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Thread List Item with Inline Rename
// ─────────────────────────────────────────────────────────────────────────────
function ThreadItem({
  conv,
  isActive,
  isEditing,
  renameValue,
  onSelect,
  onDelete,
  onRenameClick,
  onRenameSave,
  onRenameCancel,
  setRenameValue,
}: {
  conv: Conversation;
  isActive: boolean;
  isEditing: boolean;
  renameValue: string;
  onSelect: () => void;
  onDelete: () => void;
  onRenameClick: () => void;
  onRenameSave: () => void;
  onRenameCancel: () => void;
  setRenameValue: (val: string) => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={`w-full p-3 rounded-xl border transition-all group flex flex-col gap-2 ${
        isActive
          ? 'border-violet-500/40 bg-violet-500/5'
          : 'border-white/5 bg-neutral-950/20 hover:border-violet-500/20 hover:bg-neutral-900/40'
      }`}
    >
      {isEditing ? (
        <div className="flex items-center gap-1.5 w-full">
          <input
            type="text"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            className="flex-1 bg-neutral-900 border border-violet-500/30 rounded px-2 py-0.5 text-xs text-white focus:outline-none focus:border-violet-500"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') onRenameSave();
              if (e.key === 'Escape') onRenameCancel();
            }}
          />
          <button onClick={onRenameSave} className="p-1 hover:text-emerald-400 text-neutral-400 transition-all shrink-0">
            <Check className="w-3.5 h-3.5" />
          </button>
          <button onClick={onRenameCancel} className="p-1 hover:text-rose-400 text-neutral-400 transition-all shrink-0">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex items-start justify-between gap-2" onClick={onSelect}>
          <div className="flex items-center gap-2.5 min-w-0 cursor-pointer flex-1">
            <div className={`p-1.5 rounded-lg border shrink-0 ${isActive ? 'bg-violet-500/10 border-violet-500/20' : 'bg-neutral-900 border-white/5'}`}>
              <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-violet-400' : 'text-neutral-500'}`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className={`text-xs font-semibold truncate ${isActive ? 'text-violet-300' : 'text-white'}`}>
                {conv.title}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <Clock className="w-2.5 h-2.5 text-neutral-600" />
                <span className="text-[10px] text-neutral-500">
                  {new Date(conv.created_at).toLocaleDateString()}
                </span>
                {conv.message_count !== undefined && (
                  <Badge variant="neutral" size="sm">{conv.message_count} msgs</Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center opacity-0 group-hover:opacity-100 transition-all shrink-0 gap-0.5">
            <button
              onClick={(e) => { e.stopPropagation(); onRenameClick(); }}
              className="p-1 text-neutral-500 hover:text-violet-400 transition-all"
            >
              <Edit2 className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="p-1 text-neutral-500 hover:text-rose-400 transition-all"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Message Bubble with Metadata telemetry badges
// ─────────────────────────────────────────────────────────────────────────────
function MessageBubble({ message, idx }: { message: Message; idx: number }) {
  const isUser = message.role === 'user';
  const hasTelemetry = !isUser && (message.latency_ms || message.prompt_tokens || message.cost_usd);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.02 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div className={`shrink-0 p-1.5 rounded-lg border h-7 w-7 flex items-center justify-center ${
        isUser ? 'bg-violet-600/20 border-violet-500/30' : 'bg-neutral-900 border-white/5'
      }`}>
        {isUser ? <User className="w-3.5 h-3.5 text-violet-400" /> : <Bot className="w-3.5 h-3.5 text-neutral-400" />}
      </div>
      
      <div className={`max-w-[78%] flex flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-xl border leading-relaxed ${
          isUser
            ? 'bg-violet-600/10 border-violet-500/20 text-violet-100'
            : 'bg-neutral-900/60 border-white/5 text-neutral-200'
        }`}>
          <Markdown text={message.content} />
        </div>

        <div className="flex flex-wrap items-center gap-1.5 px-1 text-[9px] text-neutral-500 font-mono">
          {!isUser && message.model_used && (
            <span className="bg-neutral-900 border border-white/5 px-1.5 py-0.5 rounded text-neutral-400">{message.model_used}</span>
          )}
          {!isUser && message.provider_used && (
            <span className="bg-neutral-900 border border-white/5 px-1.5 py-0.5 rounded text-violet-400/80">{message.provider_used.toUpperCase()}</span>
          )}
          {hasTelemetry && (
            <>
              {message.latency_ms && <span>• {message.latency_ms}ms</span>}
              {message.prompt_tokens && (
                <span>• {message.prompt_tokens + (message.completion_tokens || 0)} tokens</span>
              )}
              {message.cost_usd !== undefined && message.cost_usd > 0 && (
                <span className="text-emerald-400/80">• ${Number(message.cost_usd).toFixed(5)}</span>
              )}
            </>
          )}
          <span>• {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Interactive Chat page
// ─────────────────────────────────────────────────────────────────────────────
export default function ConversationsPage() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();
  
  // UI states
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedConvId, setSelectedConvId] = React.useState<string | null>(null);
  const [inputMessage, setInputMessage] = React.useState('');
  
  // Settings & overrides states
  const [selectedModel, setSelectedModel] = React.useState('openai/gpt-oss-120b');
  const [selectedPromptId, setSelectedPromptId] = React.useState<string>('');
  const [systemPrompt, setSystemPrompt] = React.useState('');
  const [ragEnabled, setRagEnabled] = React.useState(false);
  const [showSettings, setShowSettings] = React.useState(false);

  // Rename states
  const [editingConvId, setEditingConvId] = React.useState<string | null>(null);
  const [renameValue, setRenameValue] = React.useState('');

  // Generation & streaming simulator states
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [streamingText, setStreamingText] = React.useState('');
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const messageEndRef = React.useRef<HTMLDivElement>(null);

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: conversations = [], isLoading: loadingConvs } = useQuery<Conversation[]>({
    queryKey: ['conversations', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/chat/conversations/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: messages = [], isLoading: loadingMsgs } = useQuery<Message[]>({
    queryKey: ['messages', selectedConvId],
    queryFn: async () => {
      if (!selectedConvId) return [];
      const res = await apiClient.get(`/chat/conversations/${selectedConvId}/messages`);
      return res.data || [];
    },
    enabled: !!selectedConvId,
  });

  const { data: models = [] } = useQuery<AIModel[]>({
    queryKey: ['models'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/models/');
      return res.data || [];
    },
  });

  const activeModels = React.useMemo(() => {
    return (models as AIModel[]).filter((m) => {
      const isEnabled = m.is_active ?? m.is_healthy ?? true;
      return isEnabled && (m.supports_streaming ?? true);
    });
  }, [models]);

  const effectiveSelectedModel = React.useMemo(() => {
    if (!activeModels.length) {
      return selectedModel || 'openai/gpt-oss-120b';
    }

    const exists = activeModels.some((m) => m.model_name === selectedModel);
    if (exists) {
      return selectedModel;
    }

    return activeModels.find((m) => m.model_name === 'openai/gpt-oss-120b')?.model_name || activeModels[0].model_name;
  }, [activeModels, selectedModel]);

  const modelsByProvider = React.useMemo(() => {
    const groups: Record<string, AIModel[]> = {};
    activeModels.forEach((m) => {
      const p = m.provider || 'unknown';
      if (!groups[p]) groups[p] = [];
      groups[p].push(m);
    });
    return groups;
  }, [activeModels]);


  const { data: promptTemplates = [] } = useQuery<PromptTemplate[]>({
    queryKey: ['prompts'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/');
      return res.data || [];
    },
  });

  // ── Auto Scroll ───────────────────────────────────────────────────────────
  React.useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText, isGenerating]);

  // ── Mutations ─────────────────────────────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: async () => {
      const providerName = activeModels.find((model) => model.model_name === effectiveSelectedModel)?.provider || 'groq';
      const res = await apiClient.post('/chat/conversations/', {
        title: `Chat Session ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
        model_name: effectiveSelectedModel,
        provider_name: providerName,
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setSelectedConvId(data.id);
      setInputMessage('');
      toast.success('Created', 'New chat session started.');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/chat/conversations/${id}`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (selectedConvId === id) setSelectedConvId(null);
      toast.success('Deleted', 'Conversation removed.');
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      apiClient.patch(`/chat/conversations/${id}`, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setEditingConvId(null);
      toast.success('Renamed', 'Conversation title updated.');
    },
  });

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || !selectedConvId || isGenerating) return;

    const userQuery = inputMessage.trim();
    setInputMessage('');
    setIsGenerating(true);
    setStreamingText('');
    
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Instantly refresh queries to show user message in UI
    queryClient.setQueryData<Message[]>(['messages', selectedConvId], (old = []) => [
      ...old,
      {
        id: `temp-user-${Date.now()}`,
        role: 'user',
        content: userQuery,
        created_at: new Date().toISOString(),
      }
    ]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat/conversations/${selectedConvId}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore.getState().accessToken || ''}`,
          'X-Organization-ID': useAuthStore.getState().activeOrg?.id || '',
        },
        body: JSON.stringify({
          content: userQuery,
          model_name: effectiveSelectedModel,
          prompt_id: selectedPromptId || null,
          system_prompt: systemPrompt || null,
          rag_enabled: ragEnabled
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize stream: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');

      if (!reader) {
        throw new Error('No readable stream body.');
      }

      let buffer = '';
      let fullText = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.error) {
                  toast.error('Stream Error', parsed.error);
                } else if (parsed.content) {
                  fullText += parsed.content;
                  setStreamingText(fullText);
                }
              } catch {
                // Ignore partial JSON parsing errors
              }
            }
          }
        }
      }

      setIsGenerating(false);
      setStreamingText('');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConvId] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });

    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        toast.info('Stopped', 'Generation aborted by user.');
      } else {
        const message = err instanceof Error ? err.message : 'Failed to complete message request.';
        toast.error('Failure', message);
      }
      setIsGenerating(false);
      setStreamingText('');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConvId] });
    } finally {
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsGenerating(false);
    setStreamingText('');
  };  const handleRegenerate = async () => {
    if (!messages.length || isGenerating || !selectedConvId) return;

    // Find last user message
    const reversed = [...messages].reverse();
    const lastUserMsg = reversed.find(m => m.role === 'user');

    if (!lastUserMsg) return;

    // Delete last assistant message if exists
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') {
      // Re-trigger using last user message content
      setInputMessage(lastUserMsg.content);
      // Clean last messages in state
      queryClient.setQueryData<Message[]>(['messages', selectedConvId], (old = []) => 
        old.filter(m => m.id !== lastMsg.id)
      );
      toast.info('Regenerating', 'Re-submitting last prompt...');
    }
  };

  // ── Derived List ──────────────────────────────────────────────────────────
  const filtered = conversations.filter((c: Conversation) =>
    !searchTerm || c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedConv = conversations.find((c: Conversation) => c.id === selectedConvId);

  // Markdown Export
  const handleExport = () => {
    if (!messages.length) return;
    const md = messages
      .map((m: Message) => `**${m.role === 'user' ? 'You' : 'AI'}**: ${m.content}`)
      .join('\n\n---\n\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${selectedConv?.title ?? 'conversation'}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Exported', 'Saved conversation thread as Markdown.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="AI Playground & Chat"
        description="Launch real-time conversations, trigger RAG workspace search, apply custom prompt overrides, and analyze gateway token executions."
        icon={<MessageSquare className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">{conversations.length} Active Sessions</Badge>}
      />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 h-[calc(100vh-220px)] overflow-hidden">
        {/* ── Left Sidebar (Sessions List) ── */}
        <div className="xl:col-span-1 flex flex-col gap-3 overflow-hidden bg-neutral-950/20 border border-white/5 rounded-xl p-4">
          <Button
            onClick={() => createMutation.mutate()}
            className="w-full bg-violet-600 hover:bg-violet-700 text-xs font-semibold py-2 h-9 flex items-center justify-center gap-1.5"
            disabled={createMutation.isPending}
          >
            <Plus className="w-4 h-4" />
            New Chat Session
          </Button>

          <Input
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="h-8 text-xs bg-neutral-900 border-white/5"
          />

          <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-1.5 mt-2">
            {loadingConvs ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-14 rounded-xl bg-neutral-900/40 border border-white/5 animate-pulse" />
              ))
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={<MessageSquare className="w-6 h-6" />}
                title="No threads"
                description="Start a chat to seed history."
                compact
              />
            ) : (
              <AnimatePresence mode="popLayout">
                {filtered.map((conv: Conversation) => (
                  <ThreadItem
                    key={conv.id}
                    conv={conv}
                    isActive={selectedConvId === conv.id}
                    isEditing={editingConvId === conv.id}
                    renameValue={renameValue}
                    setRenameValue={setRenameValue}
                    onSelect={() => {
                      setSelectedConvId(conv.id);
                      setInputMessage('');
                    }}
                    onDelete={() => deleteMutation.mutate(conv.id)}
                    onRenameClick={() => {
                      setEditingConvId(conv.id);
                      setRenameValue(conv.title);
                    }}
                    onRenameSave={() => {
                      if (renameValue.trim()) {
                        renameMutation.mutate({ id: conv.id, title: renameValue.trim() });
                      }
                    }}
                    onRenameCancel={() => setEditingConvId(null)}
                  />
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>

        {/* ── Right Panel (Chat Screen) ── */}
        <div className="xl:col-span-3 rounded-xl border border-white/5 bg-neutral-950/20 flex flex-col overflow-hidden relative">
          {selectedConvId ? (
            <>
              {/* Top Banner (Session Telemetry Details) */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 px-5 py-3 border-b border-white/5 bg-neutral-900/40 shrink-0">
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="w-4 h-4 text-violet-400 shrink-0" />
                  <span className="text-xs font-semibold text-white truncate">{selectedConv?.title}</span>
                  <Badge variant="neutral" size="sm" className="font-mono text-[9px] shrink-0">
                    {messages.length + (isGenerating ? 1 : 0)} messages
                  </Badge>
                </div>

                <div className="flex items-center gap-2 self-end md:self-auto">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowSettings(!showSettings)}
                    className={`h-7 text-[10px] gap-1 px-2.5 ${showSettings ? 'border-violet-500 text-violet-400 bg-violet-500/5' : ''}`}
                  >
                    <Sliders className="w-3 h-3" />
                    Parameters
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExport}
                    className="h-7 text-[10px] gap-1 px-2.5 border-white/5"
                  >
                    <Download className="w-3 h-3" />
                    Export
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedConvId(null)}
                    className="h-7 w-7 p-0 shrink-0"
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>

              {/* Dynamic Override Parameter Settings Panel */}
              <AnimatePresence>
                {showSettings && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden border-b border-white/5 bg-neutral-900/20 shrink-0"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 text-[11px]">
                      {/* Model Selector */}
                      <div className="flex flex-col gap-1.5">
                        <label className="text-neutral-400 font-semibold flex items-center gap-1">
                          <Cpu className="w-3.5 h-3.5" /> AI LLM Model
                        </label>
                        <select
                          value={effectiveSelectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="bg-neutral-950 border border-white/5 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500/50"
                        >
                          {activeModels.length === 0 ? (
                            <option value="openai/gpt-oss-120b">openai/gpt-oss-120b</option>
                          ) : (
                            Object.entries(modelsByProvider).map(([provider, providerModels]) => (
                              <optgroup key={provider} label={provider.toUpperCase()}>
                                {providerModels.map((m) => {
                                   const formattedName = m.name || m.model_name;
                                   const ctxDisplay = m.context_window ? `${Math.round(m.context_window / 1000)}k ctx` : '';
                                   const streamingDisplay = m.supports_streaming ? '⚡' : '';
                                   const visionDisplay = m.supports_vision ? '👁️' : '';
                                   const toolsDisplay = m.supports_tool_calling ? '🛠️' : '';
                                   const jsonDisplay = m.supports_json ? 'JSON' : '';
                                   const favoriteDisplay = m.is_favorite ? '★' : '';
                                   const costDisplay = m.input_token_price ? `$${m.input_token_price}/$${m.output_token_price} per 1M` : '';
                                   
                                   const label = `${formattedName} (${ctxDisplay}) ${streamingDisplay}${visionDisplay}${toolsDisplay}${jsonDisplay} ${costDisplay} ${favoriteDisplay}`.trim();
                                   return (
                                     <option key={m.id} value={m.model_name}>
                                       {label}
                                     </option>
                                   );
                                 })}
                              </optgroup>
                            ))
                          )}
                        </select>
                      </div>

                      {/* Prompt Template Selector */}
                      <div className="flex flex-col gap-1.5">
                        <label className="text-neutral-400 font-semibold flex items-center gap-1">
                          <Sparkles className="w-3.5 h-3.5" /> Prompt Template
                        </label>
                        <select
                          value={selectedPromptId}
                          onChange={(e) => {
                            const value = e.target.value;
                            setSelectedPromptId(value);
                            if (value) {
                              const selected = promptTemplates.find((p) => p.id === value);
                              setSystemPrompt(selected?.content ?? '');
                            } else {
                              setSystemPrompt('');
                            }
                          }}
                          className="bg-neutral-950 border border-white/5 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500/50"
                        >
                          <option value="">No Template (Default System Prompt)</option>
                          {promptTemplates.map(p => (
                            <option key={p.id} value={p.id}>
                              {p.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* RAG Knowledge Engine Enablement */}
                      <div className="flex flex-col gap-1.5 justify-center">
                        <span className="text-neutral-400 font-semibold flex items-center gap-1 mb-1">
                          <Database className="w-3.5 h-3.5" /> RAG Knowledge Integration
                        </span>
                        <label className="flex items-center gap-2 cursor-pointer bg-neutral-950/40 border border-white/5 hover:border-violet-500/20 px-3 py-1.5 rounded transition-all">
                          <input
                            type="checkbox"
                            checked={ragEnabled}
                            onChange={(e) => setRagEnabled(e.target.checked)}
                            className="rounded border-neutral-800 text-violet-600 focus:ring-violet-500 bg-neutral-900 w-3.5 h-3.5"
                          />
                          <span className="text-xs text-neutral-300">Run Vector Search on Documents</span>
                        </label>
                      </div>

                      {/* Custom System Prompt Override */}
                      <div className="md:col-span-3 flex flex-col gap-1 mt-1">
                        <label className="text-neutral-400 font-semibold">Custom System Prompt Override</label>
                        <textarea
                          placeholder="Inject system guidelines to shape LLM responses..."
                          value={systemPrompt}
                          onChange={(e) => setSystemPrompt(e.target.value)}
                          className="w-full bg-neutral-950 border border-white/5 rounded p-2 text-xs text-white focus:outline-none focus:border-violet-500/50 h-16 resize-none"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Chat Viewport Messages */}
              <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
                {loadingMsgs ? (
                  <div className="flex flex-col gap-4">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className={`flex gap-3 ${i % 2 === 0 ? '' : 'flex-row-reverse'}`}>
                        <div className="w-7 h-7 rounded-lg bg-neutral-850 animate-pulse shrink-0" />
                        <div className={`h-14 rounded-xl bg-neutral-850 animate-pulse shrink-0 ${i % 2 === 0 ? 'w-2/3' : 'w-1/2'}`} />
                      </div>
                    ))}
                  </div>
                ) : messages.length === 0 ? (
                  <EmptyState
                    icon={<MessageSquare className="w-8 h-8 text-neutral-600" />}
                    title="Start Chatting"
                    description="Send a message below. Seed system prompts or connect RAG search under parameters."
                    compact
                  />
                ) : (
                  <>
                    {messages.map((m: Message, idx: number) => (
                      <MessageBubble key={m.id} message={m} idx={idx} />
                    ))}

                    {/* Local Streaming simulated state */}
                    {isGenerating && streamingText && (
                      <MessageBubble
                        message={{
                          id: 'streaming-assistant',
                          role: 'assistant',
                          content: streamingText,
                          model_used: selectedModel,
                          created_at: new Date().toISOString(),
                        }}
                        idx={messages.length}
                      />
                    )}

                    {/* Typing Indicator */}
                    {isGenerating && !streamingText && (
                      <div className="flex gap-3">
                        <div className="shrink-0 p-1.5 rounded-lg border h-7 w-7 flex items-center justify-center bg-neutral-900 border-white/5">
                          <Bot className="w-3.5 h-3.5 text-neutral-400" />
                        </div>
                        <div className="bg-neutral-900/60 border border-white/5 px-4 py-3 rounded-xl flex items-center gap-1">
                          <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    )}
                  </>
                )}
                <div ref={messageEndRef} />
              </div>

              {/* Chat Input Footer Panel */}
              <div className="p-4 border-t border-white/5 bg-neutral-900/20 shrink-0">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Input
                    placeholder="Ask Viptant AI anything..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={isGenerating}
                    className="flex-1 bg-neutral-950 border-white/5 text-xs h-9 focus:border-violet-500/50"
                  />

                  {isGenerating ? (
                    <Button
                      type="button"
                      onClick={handleStopGeneration}
                      className="bg-rose-600 hover:bg-rose-700 h-9 px-4 text-xs font-semibold shrink-0 gap-1.5"
                    >
                      <StopCircle className="w-4 h-4" />
                      Stop
                    </Button>
                  ) : (
                    <>
                      {messages.length > 0 && (
                        <Button
                          type="button"
                          onClick={handleRegenerate}
                          variant="outline"
                          className="border-white/5 h-9 w-9 p-0 shrink-0 text-neutral-400 hover:text-white"
                          title="Regenerate Last Response"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        type="submit"
                        className="bg-violet-600 hover:bg-violet-700 h-9 px-4 text-xs font-semibold shrink-0 gap-1.5"
                        disabled={!inputMessage.trim()}
                      >
                        <Send className="w-3.5 h-3.5" />
                        Send
                      </Button>
                    </>
                  )}
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState
                icon={<MessageSquare className="w-8 h-8 text-neutral-600" />}
                title="AI Command Center"
                description="Select an existing discussion thread from the sidebar or click 'New Chat Session' to start a new chat."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
