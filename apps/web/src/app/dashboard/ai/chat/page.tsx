'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/ui/empty-state';
import { CodeBlock } from '@/components/ui/code-block';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, User, Send, Plus, Trash2, Copy, RefreshCw,
  BookOpen, Brain, ChevronDown, Sparkles, Square,
  MessageSquare, Settings2, Check, Paperclip, Zap
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_name?: string;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Markdown-like renderer (lightweight, no lib dependency)
// ─────────────────────────────────────────────────────────────────────────────
function renderContent(content: string): React.ReactNode {
  // Split by code blocks first
  const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let keyIdx = 0;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Text before code block
    if (match.index > lastIndex) {
      parts.push(
        <span key={keyIdx++}>
          {renderInlineMarkdown(content.slice(lastIndex, match.index))}
        </span>
      );
    }
    // Code block
    parts.push(
      <CodeBlock
        key={keyIdx++}
        code={match[2].trim()}
        language={match[1] || 'text'}
        copyable
        showLineNumbers={match[2].split('\n').length > 3}
        className="my-2"
      />
    );
    lastIndex = match.index + match[0].length;
  }

  // Remaining text
  if (lastIndex < content.length) {
    parts.push(
      <span key={keyIdx++}>
        {renderInlineMarkdown(content.slice(lastIndex))}
      </span>
    );
  }

  return parts.length > 0 ? <>{parts}</> : renderInlineMarkdown(content);
}

function renderInlineMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  return lines.map((line, li) => {
    // Headings
    if (line.startsWith('### ')) return <h3 key={li} className="text-sm font-bold text-white mt-3 mb-1">{line.slice(4)}</h3>;
    if (line.startsWith('## '))  return <h2 key={li} className="text-base font-bold text-white mt-3 mb-1">{line.slice(3)}</h2>;
    if (line.startsWith('# '))   return <h1 key={li} className="text-lg font-bold text-white mt-3 mb-1">{line.slice(2)}</h1>;
    // Bullet list
    if (line.startsWith('- ') || line.startsWith('* ')) {
      return <li key={li} className="ml-4 text-xs text-neutral-300 leading-relaxed list-disc">{inlineStyles(line.slice(2))}</li>;
    }
    // Numbered list
    if (/^\d+\.\s/.test(line)) {
      return <li key={li} className="ml-4 text-xs text-neutral-300 leading-relaxed list-decimal">{inlineStyles(line.replace(/^\d+\.\s/, ''))}</li>;
    }
    // Empty line → spacer
    if (!line.trim()) return <span key={li} className="block h-2" />;
    // Regular paragraph
    return <span key={li} className="block text-xs text-neutral-200 leading-relaxed">{inlineStyles(line)}</span>;
  });
}

function inlineStyles(text: string): React.ReactNode {
  // Bold **text**
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="font-mono text-violet-300 bg-violet-500/10 px-1 py-0.5 rounded text-[11px]">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Message bubble component
// ─────────────────────────────────────────────────────────────────────────────
function MessageBubble({
  message,
  isStreaming,
  streamingText,
  onCopy,
  onRetry,
}: {
  message: Message | null;
  isStreaming?: boolean;
  streamingText?: string;
  onCopy?: () => void;
  onRetry?: () => void;
}) {
  const [copied, setCopied] = React.useState(false);
  const content = message?.content ?? streamingText ?? '';
  const isUser  = message?.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
    onCopy?.();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 group ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className={`shrink-0 w-8 h-8 rounded-xl flex items-center justify-center border ${
        isUser
          ? 'bg-violet-600/20 border-violet-500/30'
          : 'bg-neutral-900 border-white/5'
      }`}>
        {isUser
          ? <User className="w-4 h-4 text-violet-400" />
          : <Bot className="w-4 h-4 text-neutral-400" />
        }
      </div>

      {/* Bubble */}
      <div className={`flex flex-col gap-1.5 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-violet-600/20 border border-violet-500/20 text-violet-100 rounded-tr-sm'
            : 'bg-neutral-900/80 border border-white/5 text-neutral-200 rounded-tl-sm'
        }`}>
          {isUser
            ? <p className="text-xs whitespace-pre-wrap leading-relaxed">{content}</p>
            : <div className="flex flex-col gap-1">{renderContent(content)}</div>
          }
          {/* Streaming cursor */}
          {isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-violet-400 ml-1 animate-pulse rounded-sm align-text-bottom" />
          )}
        </div>

        {/* Action row */}
        <div className={`flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? 'flex-row-reverse' : ''}`}>
          {message?.model_name && !isUser && (
            <span className="text-[9px] font-mono text-neutral-600 mr-1">{message.model_name}</span>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[10px] text-neutral-600 hover:text-white transition-colors cursor-pointer px-1.5 py-0.5 rounded hover:bg-white/5"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          {!isUser && onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-1 text-[10px] text-neutral-600 hover:text-white transition-colors cursor-pointer px-1.5 py-0.5 rounded hover:bg-white/5"
            >
              <RefreshCw className="w-3 h-3" />
              Retry
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Model options
// ─────────────────────────────────────────────────────────────────────────────
const MODEL_OPTIONS = [
  { value: 'gemini-1.5-flash',          label: 'Gemini 1.5 Flash',       provider: 'Google'    },
  { value: 'gemini-1.5-pro',            label: 'Gemini 1.5 Pro',          provider: 'Google'    },
  { value: 'gpt-4o-mini',               label: 'GPT-4o Mini',             provider: 'OpenAI'    },
  { value: 'gpt-4o',                    label: 'GPT-4o',                  provider: 'OpenAI'    },
  { value: 'claude-3-haiku-20240307',   label: 'Claude 3 Haiku',          provider: 'Anthropic' },
  { value: 'claude-3-5-sonnet-20241022',label: 'Claude 3.5 Sonnet',       provider: 'Anthropic' },
  { value: 'llama3-70b-8192',           label: 'Llama3 70B (Groq)',        provider: 'Groq'      },
];

// ─────────────────────────────────────────────────────────────────────────────
// Main Chat 2.0 Page
// ─────────────────────────────────────────────────────────────────────────────
export default function AIChatPage() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();

  // Chat state
  const [selectedModel, setSelectedModel]         = React.useState('gemini-1.5-flash');
  const [selectedPromptId, setSelectedPromptId]   = React.useState('');
  const [activeConvId, setActiveConvId]           = React.useState<string | null>(null);
  const [inputMessage, setInputMessage]           = React.useState('');
  const [ragEnabled, setRagEnabled]               = React.useState(false);
  const [showSettings, setShowSettings]           = React.useState(false);
  const [showModelDropdown, setShowModelDropdown] = React.useState(false);

  // Streaming state
  const [streamingText, setStreamingText]   = React.useState('');
  const [isStreaming, setIsStreaming]        = React.useState(false);
  const [lastUserMessage, setLastUserMessage] = React.useState('');

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [streamingText, isStreaming]);

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: conversations = [], isLoading: loadingConvs } = useQuery({
    queryKey: ['conversations', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/conversations/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: prompts = [] } = useQuery({
    queryKey: ['prompts', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: messages = [], isLoading: loadingMsgs } = useQuery({
    queryKey: ['messages', activeConvId],
    queryFn: async () => {
      if (!activeConvId) return [];
      const res = await apiClient.get(`/ai/conversations/${activeConvId}/messages`);
      return res.data || [];
    },
    enabled: !!activeConvId,
  });

  const { data: knowledgeDocs = [] } = useQuery({
    queryKey: ['kb-documents', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/knowledge/');
      return res.data || [];
    },
    enabled: !!activeOrg && ragEnabled,
  });

  // ── Mutations ─────────────────────────────────────────────────────────────
  const createConvMutation = useMutation({
    mutationFn: (data: { title: string }) => apiClient.post('/ai/conversations/', data),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setActiveConvId(res.data.id);
      toast.success('New Chat', 'Thread initialized.');
    },
  });

  const deleteConvMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/ai/conversations/${id}`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (activeConvId === id) setActiveConvId(null);
    },
  });

  const postMessageMutation = useMutation({
    mutationFn: (data: { content: string; model_name: string; prompt_id: string | null }) =>
      apiClient.post(`/ai/conversations/${activeConvId}/messages`, data),
    onSuccess: (res) => {
      const reply = res.data.content || '';
      animateStream(reply);
    },
    onError: () => {
      setIsStreaming(false);
      toast.error('Error', 'Model failed to respond. Try again or switch models.');
    },
  });

  // ── Streaming animation ───────────────────────────────────────────────────
  const animateStream = (fullText: string) => {
    setIsStreaming(true);
    setStreamingText('');
    let idx = 0;
    const speed = Math.max(5, Math.min(20, Math.floor(2000 / fullText.length)));
    const chunkSize = fullText.length > 500 ? 4 : 2;
    const interval = setInterval(() => {
      if (idx < fullText.length) {
        setStreamingText(fullText.slice(0, idx + chunkSize));
        idx += chunkSize;
      } else {
        clearInterval(interval);
        setIsStreaming(false);
        setStreamingText('');
        queryClient.invalidateQueries({ queryKey: ['messages', activeConvId] });
      }
    }, speed);
  };

  // ── Send message ─────────────────────────────────────────────────────────
  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputMessage.trim() || !activeConvId || isStreaming) return;
    setLastUserMessage(inputMessage);
    setInputMessage('');
    postMessageMutation.mutate({
      content: inputMessage,
      model_name: selectedModel,
      prompt_id: selectedPromptId || null,
    });
  };

  const handleRetry = () => {
    if (!lastUserMessage || !activeConvId || isStreaming) return;
    postMessageMutation.mutate({
      content: lastUserMessage,
      model_name: selectedModel,
      prompt_id: selectedPromptId || null,
    });
  };

  // ── Textarea auto-grow ────────────────────────────────────────────────────
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeConv = conversations.find((c: any) => c.id === activeConvId);
  const selectedModelMeta = MODEL_OPTIONS.find((m) => m.value === selectedModel);
  const readyDocs = knowledgeDocs.filter((d: any) => d.status === 'ready');

  return (
    <div className="flex h-[calc(100vh-112px)] max-w-[1400px] mx-auto gap-0 overflow-hidden rounded-xl border border-white/5">

      {/* ── LEFT SIDEBAR ── */}
      <div className="w-64 shrink-0 bg-neutral-950/60 border-r border-white/5 flex flex-col overflow-hidden">
        {/* New chat button */}
        <div className="p-3 border-b border-white/5">
          <Button
            variant="violet"
            size="sm"
            onClick={() => createConvMutation.mutate({ title: `Chat ${conversations.length + 1}` })}
            isLoading={createConvMutation.isPending}
            className="w-full"
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </Button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
          {loadingConvs
            ? Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 rounded-lg bg-neutral-900/40 animate-pulse" />
              ))
            : conversations.length === 0
            ? (
              <div className="py-8 text-center">
                <MessageSquare className="w-6 h-6 text-neutral-700 mx-auto mb-2" />
                <p className="text-[11px] text-neutral-600">No conversations yet</p>
              </div>
            )
            : conversations.map((conv: any) => (
              <button
                key={conv.id}
                onClick={() => setActiveConvId(conv.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between group cursor-pointer ${
                  activeConvId === conv.id
                    ? 'bg-violet-600/15 text-violet-300 font-semibold border-l-2 border-violet-500'
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="truncate">{conv.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConvMutation.mutate(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 p-0.5 text-neutral-600 hover:text-rose-400 transition-all cursor-pointer shrink-0"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </button>
            ))
          }
        </div>

        {/* Sidebar settings */}
        <div className="p-3 border-t border-white/5 flex flex-col gap-2">
          {/* Prompt template selector */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
              <BookOpen className="w-3 h-3" /> Prompt Template
            </span>
            <select
              value={selectedPromptId}
              onChange={(e) => setSelectedPromptId(e.target.value)}
              className="w-full bg-neutral-900/60 border border-white/5 rounded-lg px-2 py-1.5 text-[11px] text-white appearance-none focus:outline-none focus:border-violet-500 cursor-pointer"
            >
              <option value="">No template</option>
              {prompts.map((p: any) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* RAG toggle */}
          <button
            onClick={() => setRagEnabled(!ragEnabled)}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold transition-all cursor-pointer ${
              ragEnabled
                ? 'border-violet-500/40 bg-violet-500/10 text-violet-300'
                : 'border-white/5 bg-neutral-900/40 text-neutral-500 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5" />
              RAG Context
            </div>
            <div className={`w-7 h-4 rounded-full transition-all relative ${ragEnabled ? 'bg-violet-600' : 'bg-neutral-700'}`}>
              <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${ragEnabled ? 'left-3.5' : 'left-0.5'}`} />
            </div>
          </button>

          {ragEnabled && (
            <div className="text-[10px] text-neutral-500 px-1">
              {readyDocs.length} document{readyDocs.length !== 1 ? 's' : ''} in context
            </div>
          )}
        </div>
      </div>

      {/* ── MAIN CHAT AREA ── */}
      <div className="flex-1 flex flex-col overflow-hidden bg-black/20">
        {/* Header */}
        <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between shrink-0 bg-neutral-950/40">
          <div className="flex items-center gap-3">
            {activeConvId ? (
              <>
                <Bot className="w-4 h-4 text-violet-400" />
                <span className="text-sm font-semibold text-white">{activeConv?.title ?? 'Chat'}</span>
                {isStreaming && (
                  <Badge variant="violet" dot size="sm">Generating...</Badge>
                )}
              </>
            ) : (
              <span className="text-sm text-neutral-500">Select or create a conversation</span>
            )}
          </div>

          {/* Model selector */}
          <div className="relative">
            <button
              onClick={() => setShowModelDropdown(!showModelDropdown)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 bg-neutral-900/60 text-xs text-white hover:border-violet-500/30 transition-all cursor-pointer"
            >
              <Zap className="w-3 h-3 text-violet-400" />
              <span className="max-w-[120px] truncate">{selectedModelMeta?.label}</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${showModelDropdown ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
              {showModelDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="absolute right-0 top-full mt-1 w-56 bg-neutral-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
                >
                  {MODEL_OPTIONS.map((model) => (
                    <button
                      key={model.value}
                      onClick={() => { setSelectedModel(model.value); setShowModelDropdown(false); }}
                      className={`w-full flex items-center justify-between px-3 py-2.5 text-xs text-left cursor-pointer transition-colors ${
                        selectedModel === model.value
                          ? 'bg-violet-600/10 text-violet-300'
                          : 'text-neutral-300 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <div>
                        <div className="font-semibold">{model.label}</div>
                        <div className="text-[10px] text-neutral-500">{model.provider}</div>
                      </div>
                      {selectedModel === model.value && <Check className="w-3.5 h-3.5 text-violet-400" />}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Messages area */}
        {!activeConvId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4 text-center max-w-md">
              <div className="p-6 rounded-2xl bg-violet-600/10 border border-violet-500/20">
                <Sparkles className="w-10 h-10 text-violet-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Viptant AI Chat</h2>
                <p className="text-sm text-neutral-400 mt-2 leading-relaxed">
                  Start a new conversation or select an existing thread.
                  Toggle RAG to ground responses in your knowledge base.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {['Draft a campaign email', 'Summarize CRM leads', 'Write ad copy for Q4', 'Analyze market trends'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      createConvMutation.mutate(
                        { title: suggestion.slice(0, 30) },
                        {
                          onSuccess: (res) => {
                            setActiveConvId(res.data.id);
                            setInputMessage(suggestion);
                          },
                        }
                      );
                    }}
                    className="px-3 py-1.5 rounded-full border border-white/10 text-xs text-neutral-400 hover:text-white hover:border-violet-500/30 transition-all cursor-pointer"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
              <Button
                variant="violet"
                size="sm"
                onClick={() => createConvMutation.mutate({ title: `Chat ${conversations.length + 1}` })}
                isLoading={createConvMutation.isPending}
              >
                <Plus className="w-3.5 h-3.5" />
                Start New Chat
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5" onClick={() => setShowModelDropdown(false)}>
              {loadingMsgs ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className={`flex gap-3 ${i % 2 === 0 ? '' : 'flex-row-reverse'}`}>
                    <div className="w-8 h-8 rounded-xl bg-neutral-800 animate-pulse shrink-0" />
                    <div className={`h-16 rounded-2xl bg-neutral-800/60 animate-pulse ${i % 2 === 0 ? 'w-2/3' : 'w-1/2'}`} />
                  </div>
                ))
              ) : (
                <>
                  <AnimatePresence initial={false}>
                    {messages.map((msg: Message) => (
                      <MessageBubble
                        key={msg.id}
                        message={msg}
                        onCopy={() => toast.success('Copied', 'Message text copied.')}
                        onRetry={msg.role === 'assistant' ? handleRetry : undefined}
                      />
                    ))}
                  </AnimatePresence>

                  {/* Streaming bubble */}
                  {(postMessageMutation.isPending || isStreaming) && (
                    <MessageBubble
                      message={null}
                      isStreaming={isStreaming || postMessageMutation.isPending}
                      streamingText={streamingText || (postMessageMutation.isPending && !isStreaming ? '…' : '')}
                    />
                  )}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="p-4 border-t border-white/5 bg-neutral-950/40 shrink-0">
              <form onSubmit={handleSend} className="flex flex-col gap-2">
                <div className={`flex items-end gap-3 rounded-xl border bg-neutral-900/60 px-4 py-3 transition-all focus-within:border-violet-500/40 ${isStreaming ? 'border-violet-500/20' : 'border-white/10'}`}>
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder={
                      isStreaming
                        ? 'AI is responding...'
                        : ragEnabled
                        ? 'Ask anything — AI will search your knowledge base...'
                        : 'Message AI (Enter to send, Shift+Enter for newline)...'
                    }
                    disabled={isStreaming}
                    rows={1}
                    className="flex-1 bg-transparent text-sm text-white placeholder-neutral-500 focus:outline-none resize-none disabled:opacity-50 leading-relaxed"
                    style={{ maxHeight: '160px' }}
                  />

                  <div className="flex items-center gap-2 shrink-0">
                    {isStreaming ? (
                      <button
                        type="button"
                        onClick={() => { setIsStreaming(false); setStreamingText(''); }}
                        className="p-2 rounded-lg bg-rose-600/20 border border-rose-500/30 text-rose-400 hover:bg-rose-600/30 transition-all cursor-pointer"
                      >
                        <Square className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={!inputMessage.trim() || isStreaming}
                        className="p-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-40 disabled:pointer-events-none transition-all cursor-pointer"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Status row */}
                <div className="flex items-center gap-2 px-1">
                  <span className="text-[10px] text-neutral-600">
                    {selectedModelMeta?.provider} · {selectedModelMeta?.label}
                  </span>
                  {ragEnabled && (
                    <Badge variant="violet" size="sm" dot>RAG Active · {readyDocs.length} docs</Badge>
                  )}
                  {selectedPromptId && (
                    <Badge variant="amber" size="sm">Prompt applied</Badge>
                  )}
                  <span className="ml-auto text-[10px] text-neutral-700">⏎ send · ⇧⏎ newline</span>
                </div>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
