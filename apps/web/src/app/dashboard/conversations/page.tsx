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
  Clock, ChevronRight, Archive, X
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
  updated_at?: string;
  message_count?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Thread List Item
// ─────────────────────────────────────────────────────────────────────────────
function ThreadItem({
  conv,
  isActive,
  onSelect,
  onDelete,
}: {
  conv: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  return (
    <motion.button
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-xl border transition-all group ${
        isActive
          ? 'border-violet-500/40 bg-violet-500/5'
          : 'border-white/5 bg-neutral-950/20 hover:border-violet-500/20 hover:bg-neutral-900/40'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className={`p-1.5 rounded-lg border shrink-0 ${isActive ? 'bg-violet-500/10 border-violet-500/20' : 'bg-neutral-900 border-white/5'}`}>
            <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-violet-400' : 'text-neutral-500'}`} />
          </div>
          <div className="min-w-0">
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
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="opacity-0 group-hover:opacity-100 p-1 text-neutral-500 hover:text-rose-400 transition-all shrink-0"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </motion.button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Message Bubble
// ─────────────────────────────────────────────────────────────────────────────
function MessageBubble({ message, idx }: { message: Message; idx: number }) {
  const isUser = message.role === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.03 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div className={`shrink-0 p-1.5 rounded-lg border h-7 w-7 flex items-center justify-center ${
        isUser ? 'bg-violet-600/20 border-violet-500/30' : 'bg-neutral-900 border-white/5'
      }`}>
        {isUser ? <User className="w-3.5 h-3.5 text-violet-400" /> : <Bot className="w-3.5 h-3.5 text-neutral-400" />}
      </div>
      <div className={`max-w-[75%] flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-3 py-2 rounded-xl text-xs leading-relaxed ${
          isUser
            ? 'bg-violet-600/20 border border-violet-500/20 text-violet-100'
            : 'bg-neutral-900 border border-white/5 text-neutral-200'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="flex items-center gap-2 px-1">
          {message.model_name && !isUser && (
            <span className="text-[9px] text-neutral-600 font-mono">{message.model_name}</span>
          )}
          <span className="text-[9px] text-neutral-600">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function ConversationsPage() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedConvId, setSelectedConvId] = React.useState<string | null>(null);

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: conversations = [], isLoading: loadingConvs } = useQuery({
    queryKey: ['conversations', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/conversations/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: messages = [], isLoading: loadingMsgs } = useQuery({
    queryKey: ['messages', selectedConvId],
    queryFn: async () => {
      if (!selectedConvId) return [];
      const res = await apiClient.get(`/ai/conversations/${selectedConvId}/messages`);
      return res.data || [];
    },
    enabled: !!selectedConvId,
  });

  // ── Mutations ─────────────────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/ai/conversations/${id}`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (selectedConvId === id) setSelectedConvId(null);
      toast.success('Deleted', 'Conversation removed.');
    },
  });

  // ── Derived ───────────────────────────────────────────────────────────────
  const filtered = conversations.filter((c: any) =>
    !searchTerm || c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedConv = conversations.find((c: any) => c.id === selectedConvId);

  // ── Export ────────────────────────────────────────────────────────────────
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
    toast.success('Exported', 'Conversation saved as Markdown.');
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Conversations"
        description="Browse, search, and manage all AI conversation threads. Export or archive sessions."
        icon={<MessageSquare className="w-5 h-5" />}
        badge={<Badge variant="violet">{conversations.length} Threads</Badge>}
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 h-[calc(100vh-280px)] overflow-hidden">
        {/* ── Thread list ── */}
        <div className="xl:col-span-1 flex flex-col gap-3 overflow-hidden">
          <Input
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="h-8 text-xs"
          />

          <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-1.5">
            {loadingConvs ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-16 rounded-xl bg-neutral-900/40 border border-white/5 animate-pulse" />
              ))
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={<MessageSquare className="w-6 h-6" />}
                title="No conversations"
                description="Start an AI chat to create threads."
                compact
              />
            ) : (
              <AnimatePresence mode="popLayout">
                {filtered.map((conv: any) => (
                  <ThreadItem
                    key={conv.id}
                    conv={conv}
                    isActive={selectedConvId === conv.id}
                    onSelect={() => setSelectedConvId(conv.id)}
                    onDelete={() => deleteMutation.mutate(conv.id)}
                  />
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>

        {/* ── Message viewer ── */}
        <div className="xl:col-span-2 rounded-xl border border-white/5 bg-neutral-950/20 flex flex-col overflow-hidden">
          {selectedConvId ? (
            <>
              {/* Thread header */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-neutral-900/40 shrink-0">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-violet-400" />
                  <span className="text-sm font-semibold text-white">{selectedConv?.title}</span>
                  <Badge variant="neutral" size="sm">{messages.length} messages</Badge>
                </div>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExport}
                    className="h-7 text-[11px]"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export MD
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedConvId(null)}
                    className="h-7 w-7 p-0"
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
                {loadingMsgs ? (
                  <div className="flex flex-col gap-4">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className={`flex gap-3 ${i % 2 === 0 ? '' : 'flex-row-reverse'}`}>
                        <div className="w-7 h-7 rounded-lg bg-neutral-800 animate-pulse" />
                        <div className={`h-14 rounded-xl bg-neutral-800 animate-pulse ${i % 2 === 0 ? 'w-2/3' : 'w-1/2'}`} />
                      </div>
                    ))}
                  </div>
                ) : messages.length === 0 ? (
                  <EmptyState
                    icon={<MessageSquare className="w-6 h-6" />}
                    title="No messages"
                    description="This conversation has no messages yet."
                    compact
                  />
                ) : (
                  messages.map((m: Message, idx: number) => (
                    <MessageBubble key={m.id} message={m} idx={idx} />
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState
                icon={<MessageSquare className="w-8 h-8" />}
                title="Select a conversation"
                description="Click any thread on the left to view its messages."
                compact
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
