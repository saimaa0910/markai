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
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import {
  MessageSquare, Trash2, Download, Search, Bot, User,
  Clock, X, Edit2, Plus, Send, Cpu, Sparkles, StopCircle,
  RefreshCw, Sliders, Database, Check, Pin, Star, Archive,
  FolderOpen, Paperclip, Mic, UserPlus, Users, Share2, Clipboard,
  BarChart2, Play, CircleDot
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
  is_pinned: boolean;
  is_favorite: boolean;
  is_archived: boolean;
  model_name?: string;
  provider_name?: string;
  temperature?: number;
  system_prompt?: string;
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
}

interface PromptTemplate {
  id: string;
  name: string;
  content: string;
}

interface Participant {
  id: string;
  conversation_id: string;
  user_id: string;
  user_email?: string;
  role: string;
  created_at: string;
}

interface AttachedFile {
  id: string;
  name: string;
  size: number;
  url: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Native High-Fidelity Markdown Parser
// ─────────────────────────────────────────────────────────────────────────────
function Markdown({ text }: { text: string }) {
  if (!text) return null;

  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2 text-xs text-neutral-200">
      {parts.map((part, idx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
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
                  className="hover:text-white transition-all text-violet-400 flex items-center gap-1 bg-transparent border-0 cursor-pointer"
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

              if (trimmed.startsWith('# ')) {
                return <h1 key={lIdx} className="text-sm font-bold text-white mt-3 mb-1.5 border-b border-white/5 pb-1">{trimmed.slice(2)}</h1>;
              }
              if (trimmed.startsWith('## ')) {
                return <h2 key={lIdx} className="text-xs font-semibold text-white mt-2.5 mb-1">{trimmed.slice(3)}</h2>;
              }
              if (trimmed.startsWith('### ')) {
                return <h3 key={lIdx} className="text-[11px] font-semibold text-white mt-2 mb-1">{trimmed.slice(4)}</h3>;
              }

              if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                return (
                  <ul key={lIdx} className="list-disc list-inside pl-2 text-neutral-300">
                    <li className="mt-0.5">{trimmed.slice(2)}</li>
                  </ul>
                );
              }

              const renderBoldText = (str: string) => {
                const boldParts = str.split(/(\*\*.*?\*\*)/g);
                return boldParts.map((bp, bIdx) => {
                  if (bp.startsWith('**') && bp.endsWith('**')) {
                    return <strong key={bIdx} className="font-bold text-violet-300">{bp.slice(2, -2)}</strong>;
                  }
                  return bp;
                });
              };

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
// Thread List Item
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
  onTogglePin,
  onToggleFavorite,
  onToggleArchive,
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
  onTogglePin: () => void;
  onToggleFavorite: () => void;
  onToggleArchive: () => void;
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
          <button onClick={onRenameSave} className="p-1 hover:text-emerald-400 text-neutral-400 transition-all shrink-0 bg-transparent border-0 cursor-pointer">
            <Check className="w-3.5 h-3.5" />
          </button>
          <button onClick={onRenameCancel} className="p-1 hover:text-rose-400 text-neutral-400 transition-all shrink-0 bg-transparent border-0 cursor-pointer">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0 cursor-pointer flex-1" onClick={onSelect}>
            <div className={`p-1.5 rounded-lg border shrink-0 ${isActive ? 'bg-violet-500/10 border-violet-500/20' : 'bg-neutral-900 border-white/5'}`}>
              <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-violet-400' : 'text-neutral-500'}`} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1 min-w-0">
                {conv.is_pinned && <Pin className="w-3 h-3 text-violet-400 shrink-0 fill-violet-400" />}
                {conv.is_favorite && <Star className="w-3 h-3 text-amber-400 shrink-0 fill-amber-400" />}
                <p className={`text-xs font-semibold truncate ${isActive ? 'text-violet-300' : 'text-white'}`}>
                  {conv.title}
                </p>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <Clock className="w-2.5 h-2.5 text-neutral-600" />
                <span className="text-[10px] text-neutral-500">
                  {new Date(conv.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center opacity-0 group-hover:opacity-100 transition-all shrink-0 gap-0.5">
            <button
              onClick={(e) => { e.stopPropagation(); onTogglePin(); }}
              className={`p-1 hover:text-violet-400 transition-all bg-transparent border-0 cursor-pointer ${conv.is_pinned ? 'text-violet-400' : 'text-neutral-500'}`}
              title="Pin Chat"
            >
              <Pin className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onToggleFavorite(); }}
              className={`p-1 hover:text-amber-400 transition-all bg-transparent border-0 cursor-pointer ${conv.is_favorite ? 'text-amber-400' : 'text-neutral-500'}`}
              title="Favorite Chat"
            >
              <Star className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onToggleArchive(); }}
              className={`p-1 hover:text-cyan-400 transition-all bg-transparent border-0 cursor-pointer ${conv.is_archived ? 'text-cyan-400' : 'text-neutral-500'}`}
              title="Archive Chat"
            >
              <Archive className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onRenameClick(); }}
              className="p-1 text-neutral-500 hover:text-violet-400 transition-all bg-transparent border-0 cursor-pointer"
              title="Rename Chat"
            >
              <Edit2 className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="p-1 text-neutral-500 hover:text-rose-400 transition-all bg-transparent border-0 cursor-pointer"
              title="Delete Chat"
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
// Message Bubble
// ─────────────────────────────────────────────────────────────────────────────
function MessageBubble({ message, idx, onDelete }: { message: Message; idx: number; onDelete: () => void }) {
  const isUser = message.role === 'user';
  const hasTelemetry = !isUser && (message.latency_ms || message.prompt_tokens || message.cost_usd);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.02 }}
      className={`flex gap-3 group/msg ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div className={`shrink-0 p-1.5 rounded-lg border h-7 w-7 flex items-center justify-center ${
        isUser ? 'bg-violet-600/20 border-violet-500/30' : 'bg-neutral-900 border-white/5'
      }`}>
        {isUser ? <User className="w-3.5 h-3.5 text-violet-400" /> : <Bot className="w-3.5 h-3.5 text-neutral-400" />}
      </div>
      
      <div className={`max-w-[78%] flex flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-xl border leading-relaxed relative ${
          isUser
            ? 'bg-violet-600/10 border-violet-500/20 text-violet-100'
            : 'bg-neutral-900/60 border-white/5 text-neutral-200'
        }`}>
          <Markdown text={message.content} />
          
          <button
            onClick={onDelete}
            className="absolute top-2 right-2 opacity-0 group-hover/msg:opacity-100 p-1 text-neutral-500 hover:text-rose-400 bg-neutral-950 border border-white/10 rounded transition-all cursor-pointer shrink-0"
            title="Delete Message"
          >
            <Trash2 className="w-3 h-3" />
          </button>
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
  
  // UI Tab navigation: 'chat' | 'analytics'
  const [activeView, setActiveView] = React.useState<'chat' | 'analytics'>('chat');
  
  // Sidebar tabs: 'recent' | 'pinned' | 'favorite' | 'archived'
  const [sidebarTab, setSidebarTab] = React.useState<'recent' | 'pinned' | 'favorite' | 'archived'>('recent');

  // Search & Navigation
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedConvId, setSelectedConvId] = React.useState<string | null>(null);
  const [inputMessage, setInputMessage] = React.useState('');
  
  // Playgound parameters overrides
  const [selectedModel, setSelectedModel] = React.useState('openai/gpt-oss-120b');
  const [selectedPromptId, setSelectedPromptId] = React.useState<string>('');
  const [systemPrompt, setSystemPrompt] = React.useState('');
  const [temperature, setTemperature] = React.useState<number>(0.7);
  const [topP, setTopP] = React.useState<number>(0.9);
  const [maxTokens, setMaxTokens] = React.useState<number>(1024);
  const [ragEnabled, setRagEnabled] = React.useState(false);
  const [jsonMode, setJsonMode] = React.useState(false);
  const [showSettings, setShowSettings] = React.useState(false);
  const [showRightPanel, setShowRightPanel] = React.useState(true);

  // Rename states
  const [editingConvId, setEditingConvId] = React.useState<string | null>(null);
  const [renameValue, setRenameValue] = React.useState('');

  // Attachments State
  const [attachedFiles, setAttachedFiles] = React.useState<AttachedFile[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  // Voice recording state
  const [isRecording, setIsRecording] = React.useState(false);
  const [recordingSeconds, setRecordingSeconds] = React.useState(0);
  const [mediaRecorder, setMediaRecorder] = React.useState<MediaRecorder | null>(null);
  const recordingIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Collaboration Invitation
  const [inviteEmail, setInviteEmail] = React.useState('');
  const [inviteRole, setInviteRole] = React.useState('member');
  const [inviting, setInviting] = React.useState(false);

  // Sharing Links
  const [shareLink, setShareLink] = React.useState('');

  // Generation & streaming simulator states
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [streamingText, setStreamingText] = React.useState('');
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const messageEndRef = React.useRef<HTMLDivElement>(null);

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: conversations = [], isLoading: loadingConvs } = useQuery<Conversation[]>({
    queryKey: ['conversations', activeOrg?.id, sidebarTab, searchTerm],
    queryFn: async () => {
      const res = await apiClient.get('/chat/conversations/', {
        params: { tab: sidebarTab, query: searchTerm || undefined }
      });
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

  const { data: promptTemplates = [] } = useQuery<PromptTemplate[]>({
    queryKey: ['prompts'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/');
      return res.data || [];
    },
  });

  const { data: participants = [] } = useQuery<Participant[]>({
    queryKey: ['participants', selectedConvId],
    queryFn: async () => {
      if (!selectedConvId) return [];
      const res = await apiClient.get(`/chat/conversations/${selectedConvId}/participants`);
      return res.data || [];
    },
    enabled: !!selectedConvId,
  });

  const { data: analyticsData } = useQuery({
    queryKey: ['chat-analytics', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/chat/conversations/analytics');
      return res.data;
    },
    enabled: activeView === 'analytics' && !!activeOrg,
  });

  // Filter dynamic lists
  const activeModels = React.useMemo(() => {
    return (models as AIModel[]).filter((m) => {
      const isEnabled = m.supports_streaming ?? true;
      return isEnabled;
    });
  }, [models]);

  const modelsByProvider = React.useMemo(() => {
    const groups: Record<string, AIModel[]> = {};
    activeModels.forEach((m) => {
      const p = m.provider || 'unknown';
      if (!groups[p]) groups[p] = [];
      groups[p].push(m);
    });
    return groups;
  }, [activeModels]);

  const selectedConv = React.useMemo(() => {
    return conversations.find((c: Conversation) => c.id === selectedConvId);
  }, [conversations, selectedConvId]);

  // Sync parameters when conversation changes
  React.useEffect(() => {
    if (selectedConv) {
      setSelectedModel(selectedConv.model_name || 'openai/gpt-oss-120b');
      setTemperature(selectedConv.temperature ?? 0.7);
      setSystemPrompt(selectedConv.system_prompt || '');
    }
  }, [selectedConv]);

  // ── Auto Scroll ───────────────────────────────────────────────────────────
  React.useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText, isGenerating]);

  // ── Mutations ─────────────────────────────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/chat/conversations/', {
        title: `Chat Session ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
        model_name: selectedModel,
        temperature: temperature,
        system_prompt: systemPrompt || undefined
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setSelectedConvId(data.id);
      setInputMessage('');
      setAttachedFiles([]);
      toast.success('Created', 'New conversation started.');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/chat/conversations/${id}`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (selectedConvId === id) setSelectedConvId(null);
      toast.success('Deleted', 'Conversation thread removed.');
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

  const togglePinMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/chat/conversations/${id}/pin`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      toast.success('Updated', 'Conversation pinning updated.');
    }
  });

  const toggleFavoriteMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/chat/conversations/${id}/favorite`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      toast.success('Updated', 'Favorite preference saved.');
    }
  });

  const toggleArchiveMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/chat/conversations/${id}/archive`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      toast.success('Updated', 'Conversation archived/restored.');
    }
  });

  // ── Drag & Drop and File Handler ──────────────────────────────────────────
  const handleFileUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        await uploadFile(files[i]);
      }
    }
  };

  const handlePaste = async (e: React.ClipboardEvent<HTMLDivElement>) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          await uploadFile(file);
        }
      }
    }
  };

  const uploadFile = async (file: File) => {
    if (!selectedConvId) {
      toast.info('Warning', 'Start a conversation thread before attaching files.');
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post(`/chat/conversations/${selectedConvId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const fileAsset = res.data;
      setAttachedFiles(prev => [...prev, {
        id: fileAsset.id,
        name: fileAsset.filename,
        size: fileAsset.file_size,
        url: fileAsset.storage_url
      }]);
      toast.success('Uploaded', `${file.name} attached successfully.`);
    } catch (err: any) {
      toast.error('Upload Error', err.response?.data?.detail || 'Could not upload attachment.');
    } finally {
      setIsUploading(false);
    }
  };

  const removeAttachment = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // ── Voice Recorder ───────────────────────────────────────────────────────
  const startRecording = async () => {
    if (!selectedConvId) {
      toast.info('Warning', 'Start a conversation thread before speaking.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await uploadVoice(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingSeconds(0);
      recordingIntervalRef.current = setInterval(() => {
        setRecordingSeconds(s => s + 1);
      }, 1000);
      toast.info('Recording', 'Microphone active. Speak now.');
    } catch (err) {
      toast.error('Microphone Error', 'Could not open microphone capture device.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      if (recordingIntervalRef.current) clearInterval(recordingIntervalRef.current);
    }
  };

  const uploadVoice = async (blob: Blob) => {
    setIsGenerating(true);
    toast.info('Transcribing', 'Sending voice message to Whisper speech-to-text...');
    const formData = new FormData();
    formData.append('file', blob, 'voice_input.wav');

    try {
      await apiClient.post(`/chat/conversations/${selectedConvId}/voice`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConvId] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    } catch (err: any) {
      toast.error('Transcription Error', err.response?.data?.detail || 'Could not transcribe voice recording.');
    } finally {
      setIsGenerating(false);
    }
  };

  // ── Collaboration & Invitation ───────────────────────────────────────────
  const handleInviteCollaborator = async () => {
    if (!inviteEmail.trim() || !selectedConvId) return;
    setInviting(true);
    try {
      await apiClient.post(`/chat/conversations/${selectedConvId}/participants`, {
        user_email: inviteEmail.trim(),
        role: inviteRole
      });
      toast.success('Collaborator Invited', `Successfully added ${inviteEmail} as ${inviteRole}.`);
      setInviteEmail('');
      queryClient.invalidateQueries({ queryKey: ['participants', selectedConvId] });
    } catch (err: any) {
      toast.error('Invitation Failed', err.response?.data?.detail || 'Could not add collaborator.');
    } finally {
      setInviting(false);
    }
  };

  const handleUpdateParticipantRole = async (userId: string, newRole: string) => {
    try {
      await apiClient.patch(`/chat/conversations/${selectedConvId}/participants/${userId}?role=${newRole}`);
      toast.success('Updated', 'Collaborator role saved.');
      queryClient.invalidateQueries({ queryKey: ['participants', selectedConvId] });
    } catch (err: any) {
      toast.error('Failed', 'Could not update role.');
    }
  };

  const handleRemoveParticipant = async (userId: string) => {
    try {
      await apiClient.delete(`/chat/conversations/${selectedConvId}/participants/${userId}`);
      toast.success('Removed', 'Collaborator removed.');
      queryClient.invalidateQueries({ queryKey: ['participants', selectedConvId] });
    } catch (err: any) {
      toast.error('Failed', 'Could not delete collaborator.');
    }
  };

  const handleGenerateShareToken = async () => {
    if (!selectedConvId) return;
    try {
      const res = await apiClient.post(`/chat/conversations/${selectedConvId}/share`, { permission: 'viewer' });
      const fullUrl = `${window.location.origin}/share/${res.data.share_token}`;
      setShareLink(fullUrl);
      toast.success('Share Token Ready', 'Token generated successfully.');
    } catch (err: any) {
      toast.error('Failed', 'Could not create share link.');
    }
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(shareLink);
    toast.success('Copied', 'Share link copied to clipboard.');
  };

  // ── Chat Actions ──────────────────────────────────────────────────────────
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!inputMessage.trim() && attachedFiles.length === 0) || !selectedConvId || isGenerating) return;

    const userQuery = inputMessage.trim();
    const fileIds = attachedFiles.map(f => f.id);
    
    setInputMessage('');
    setAttachedFiles([]);
    setIsGenerating(true);
    setStreamingText('');
    
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Optimistically update message query state
    queryClient.setQueryData<Message[]>(['messages', selectedConvId], (old = []) => [
      ...old,
      {
        id: `temp-user-${Date.now()}`,
        role: 'user',
        content: userQuery || `Uploaded ${fileIds.length} file(s)`,
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
          content: userQuery || `Files attached: ${fileIds.length}`,
          model_name: selectedModel,
          system_prompt: systemPrompt || null,
          rag_enabled: ragEnabled,
          temperature: temperature,
          top_p: topP,
          max_tokens: maxTokens,
          json_mode: jsonMode,
          attachment_ids: fileIds.length > 0 ? fileIds : null
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
                // Ignore partial json parse errors
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
  };

  const handleRegenerate = async () => {
    if (!messages.length || isGenerating || !selectedConvId) return;

    const reversed = [...messages].reverse();
    const lastUserMsg = reversed.find(m => m.role === 'user');
    if (!lastUserMsg) return;

    setInputMessage(lastUserMsg.content);
    // Optimistically remove last assistant message from display
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') {
      queryClient.setQueryData<Message[]>(['messages', selectedConvId], (old = []) => 
        old.filter(m => m.id !== lastMsg.id)
      );
    }
    toast.info('Regenerating', 'Re-submitting last prompt...');
  };

  const handleDeleteMessage = async (msgId: string) => {
    if (!selectedConvId) return;
    try {
      await apiClient.delete(`/chat/conversations/${selectedConvId}/messages/${msgId}`);
      toast.success('Deleted', 'Message deleted.');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConvId] });
    } catch (err) {
      toast.error('Error', 'Could not delete message.');
    }
  };

  const handleExport = (format: 'markdown' | 'json' | 'txt') => {
    if (!messages.length || !selectedConvId) return;
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/chat/conversations/${selectedConvId}/export?format=${format}`);
    toast.success('Export Triggered', `Exporting file as ${format.toUpperCase()}`);
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1500px] mx-auto pb-12" onPaste={handlePaste}>
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <PageHeader
          title="AI Conversations Command Center"
          description="Launch real-time conversations, invite team members, attach workspace spreadsheets, and monitor pipeline token costs."
          icon={<MessageSquare className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">{conversations.length} Threads</Badge>}
        />
        
        <div className="flex bg-neutral-900/60 p-1 border border-white/5 rounded-lg shrink-0">
          <Button
            variant={activeView === 'chat' ? 'violet' : 'ghost'}
            onClick={() => setActiveView('chat')}
            className="text-[11px] h-7 px-3 gap-1"
          >
            <MessageSquare className="w-3 h-3" />
            Chat Room
          </Button>
          <Button
            variant={activeView === 'analytics' ? 'violet' : 'ghost'}
            onClick={() => setActiveView('analytics')}
            className="text-[11px] h-7 px-3 gap-1"
          >
            <BarChart2 className="w-3 h-3" />
            Usage Analytics
          </Button>
        </div>
      </div>

      {activeView === 'analytics' ? (
        // ── Analytics dashboard view ──
        <div className="flex flex-col gap-6 animate-fadeIn">
          {analyticsData ? (
            <>
              {/* Telemetry Cards Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
                {[
                  { label: 'Conversations', value: analyticsData.total_conversations, icon: <MessageSquare className="w-4 h-4 text-violet-400" /> },
                  { label: 'Total Messages', value: analyticsData.total_messages, icon: <Bot className="w-4 h-4 text-emerald-400" /> },
                  { label: 'Active Users', value: analyticsData.active_users, icon: <Users className="w-4 h-4 text-cyan-400" /> },
                  { label: 'Avg Tokens/Chat', value: Math.round(analyticsData.average_tokens_per_session), icon: <Database className="w-4 h-4 text-amber-400" /> },
                  { label: 'Avg Latency', value: `${Math.round(analyticsData.average_latency_ms)}ms`, icon: <Clock className="w-4 h-4 text-pink-400" /> },
                  { label: 'Avg Session Cost', value: `$${Number(analyticsData.average_cost_per_session).toFixed(4)}`, icon: <Sparkles className="w-4 h-4 text-green-400" /> }
                ].map((card, i) => (
                  <div key={i} className="bg-neutral-950/40 border border-white/5 p-4 rounded-xl flex flex-col gap-1.5">
                    <div className="flex justify-between items-center text-[10px] text-neutral-500 font-semibold uppercase">
                      {card.label}
                      {card.icon}
                    </div>
                    <div className="text-xl font-bold text-white tracking-tight">{card.value}</div>
                  </div>
                ))}
              </div>

              {/* Charts Display Panel */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Cost Trend Chart */}
                <div className="xl:col-span-2 bg-neutral-950/20 border border-white/5 p-5 rounded-xl flex flex-col gap-4">
                  <div>
                    <h3 className="text-xs font-semibold text-white">Daily Cost & Token Spending Trend</h3>
                    <p className="text-[10px] text-neutral-500">Pipeline spending coordinate telemetry over the past 7 days.</p>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={analyticsData.daily_stats}>
                        <defs>
                          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                        <XAxis dataKey="date" stroke="#6b7280" fontSize={10} />
                        <YAxis stroke="#6b7280" fontSize={10} />
                        <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #262626', fontSize: '10px' }} />
                        <Area type="monotone" dataKey="cost_usd" name="Cost ($)" stroke="#8b5cf6" fillOpacity={1} fill="url(#costGrad)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Model & Provider breakdown statistics */}
                <div className="bg-neutral-950/20 border border-white/5 p-5 rounded-xl flex flex-col gap-5">
                  <div>
                    <h3 className="text-xs font-semibold text-white">LLM Provider & Model Usage Share</h3>
                    <p className="text-[10px] text-neutral-500">Percentage distribution of execution tokens.</p>
                  </div>
                  <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1">
                    {/* Model Progress Bars */}
                    <div>
                      <h4 className="text-[10px] text-neutral-500 font-bold uppercase mb-2">Model Token Share</h4>
                      <div className="flex flex-col gap-2">
                        {analyticsData.model_usage.map((mu: any, idx: number) => (
                          <div key={idx} className="flex flex-col gap-1 text-[10px]">
                            <div className="flex justify-between font-semibold text-neutral-300">
                              <span>{mu.model}</span>
                              <span>{mu.percentage}%</span>
                            </div>
                            <div className="w-full bg-neutral-900 rounded-full h-1.5 overflow-hidden border border-white/5">
                              <div className="bg-violet-500 h-1.5 rounded-full" style={{ width: `${mu.percentage}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    {/* Provider Progress Bars */}
                    <div>
                      <h4 className="text-[10px] text-neutral-500 font-bold uppercase mb-2 mt-2">Provider Share</h4>
                      <div className="flex flex-col gap-2">
                        {analyticsData.provider_usage.map((pu: any, idx: number) => (
                          <div key={idx} className="flex flex-col gap-1 text-[10px]">
                            <div className="flex justify-between font-semibold text-neutral-300">
                              <span>{pu.provider.toUpperCase()}</span>
                              <span>{pu.percentage}%</span>
                            </div>
                            <div className="w-full bg-neutral-900 rounded-full h-1.5 overflow-hidden border border-white/5">
                              <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${pu.percentage}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="h-64 flex items-center justify-center border border-white/5 rounded-xl bg-neutral-950/20">
              <span className="text-xs text-neutral-500 animate-pulse">Calculating usage aggregates...</span>
            </div>
          )}
        </div>
      ) : (
        // ── Main workspace Chat view ──
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 h-[calc(100vh-230px)] overflow-hidden">
          
          {/* ── Left Sidebar (Sessions List) ── */}
          <div className="xl:col-span-1 flex flex-col gap-3 overflow-hidden bg-neutral-950/20 border border-white/5 rounded-xl p-4">
            <Button
              onClick={() => createMutation.mutate()}
              className="w-full bg-violet-600 hover:bg-violet-700 text-xs font-semibold py-2 h-9 flex items-center justify-center gap-1.5 shrink-0"
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
              className="h-8 text-xs bg-neutral-900 border-white/5 shrink-0"
            />

            {/* Sidebar Tabs Switcher */}
            <div className="flex border-b border-white/5 pb-1 gap-1 shrink-0 text-[10px]">
              {[
                { id: 'recent', label: 'Recent', icon: <Clock className="w-2.5 h-2.5" /> },
                { id: 'pinned', label: 'Pinned', icon: <Pin className="w-2.5 h-2.5" /> },
                { id: 'favorite', label: 'Favs', icon: <Star className="w-2.5 h-2.5" /> },
                { id: 'archived', label: 'Archived', icon: <Archive className="w-2.5 h-2.5" /> }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSidebarTab(tab.id as any)}
                  className={`flex-1 flex items-center justify-center gap-1 py-1 rounded transition-all bg-transparent border-0 cursor-pointer ${
                    sidebarTab === tab.id
                      ? 'text-violet-400 bg-white/5 font-semibold'
                      : 'text-neutral-500 hover:text-neutral-300'
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Thread listing */}
            <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-1.5 mt-1">
              {loadingConvs ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-14 rounded-xl bg-neutral-900/40 border border-white/5 animate-pulse" />
                ))
              ) : conversations.length === 0 ? (
                <EmptyState
                  icon={<MessageSquare className="w-6 h-6" />}
                  title="No threads"
                  description="Start a chat to seed history."
                  compact
                />
              ) : (
                <AnimatePresence mode="popLayout">
                  {conversations.map((conv: Conversation) => (
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
                        setAttachedFiles([]);
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
                      onTogglePin={() => togglePinMutation.mutate(conv.id)}
                      onToggleFavorite={() => toggleFavoriteMutation.mutate(conv.id)}
                      onToggleArchive={() => toggleArchiveMutation.mutate(conv.id)}
                    />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </div>

          {/* ── Main Chat Area ── */}
          <div className={`xl:col-span-3 rounded-xl border border-white/5 bg-neutral-950/20 flex overflow-hidden relative ${showRightPanel ? 'grid grid-cols-1 md:grid-cols-4' : 'flex flex-col'}`}>
            
            {/* Left Hand Chat Column */}
            <div className={`flex flex-col h-full overflow-hidden ${showRightPanel ? 'md:col-span-3 border-r border-white/5' : 'w-full'}`}>
              {selectedConvId ? (
                <>
                  {/* Top telemetric banner */}
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
                        className={`h-7 text-[10px] gap-1 px-2.5 border-white/5 ${showSettings ? 'border-violet-500 text-violet-400 bg-violet-500/5' : ''}`}
                      >
                        <Sliders className="w-3 h-3" />
                        Parameters
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowRightPanel(!showRightPanel)}
                        className={`h-7 text-[10px] gap-1 px-2.5 border-white/5 ${showRightPanel ? 'border-violet-500 text-violet-400 bg-violet-500/5' : ''}`}
                      >
                        <Users className="w-3 h-3" />
                        Details Panel
                      </Button>
                    </div>
                  </div>

                  {/* Overrides parameters dashboard */}
                  <AnimatePresence>
                    {showSettings && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden border-b border-white/5 bg-neutral-900/20 shrink-0"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 text-[11px]">
                          {/* Model selection */}
                          <div className="flex flex-col gap-1.5">
                            <label className="text-neutral-400 font-semibold flex items-center gap-1">
                              <Cpu className="w-3.5 h-3.5" /> AI LLM Model
                            </label>
                            <select
                              value={selectedModel}
                              onChange={(e) => setSelectedModel(e.target.value)}
                              className="bg-neutral-950 border border-white/5 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500/50"
                            >
                              {activeModels.length === 0 ? (
                                <option value="openai/gpt-oss-120b">openai/gpt-oss-120b</option>
                              ) : (
                                Object.entries(modelsByProvider).map(([provider, providerModels]) => (
                                  <optgroup key={provider} label={provider.toUpperCase()}>
                                    {providerModels.map((m) => (
                                      <option key={m.id} value={m.model_name}>
                                        {m.name || m.model_name}
                                      </option>
                                    ))}
                                  </optgroup>
                                ))
                              )}
                            </select>
                          </div>

                          {/* Prompt templates override */}
                          <div className="flex flex-col gap-1.5">
                            <label className="text-neutral-400 font-semibold flex items-center gap-1">
                              <Sparkles className="w-3.5 h-3.5" /> Prompt Template
                            </label>
                            <select
                              value={selectedPromptId}
                              onChange={(e) => {
                                const val = e.target.value;
                                setSelectedPromptId(val);
                                if (val) {
                                  const prompt = promptTemplates.find(p => p.id === val);
                                  setSystemPrompt(prompt?.content ?? '');
                                } else {
                                  setSystemPrompt('');
                                }
                              }}
                              className="bg-neutral-950 border border-white/5 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500/50"
                            >
                              <option value="">No Template (Default Prompt)</option>
                              {promptTemplates.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                              ))}
                            </select>
                          </div>

                          {/* Temperature Slider */}
                          <div className="flex flex-col gap-1.5">
                            <label className="text-neutral-400 font-semibold flex justify-between">
                              <span>Temperature</span>
                              <span className="font-mono">{temperature}</span>
                            </label>
                            <input
                              type="range"
                              min="0"
                              max="2"
                              step="0.1"
                              value={temperature}
                              onChange={(e) => setTemperature(parseFloat(e.target.value))}
                              className="w-full accent-violet-500"
                            />
                          </div>

                          {/* Parameter Toggles */}
                          <div className="md:col-span-3 flex flex-wrap gap-4 mt-1 border-t border-white/5 pt-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={ragEnabled}
                                onChange={(e) => setRagEnabled(e.target.checked)}
                                className="rounded border-neutral-800 text-violet-600 focus:ring-violet-500 bg-neutral-900 w-3.5 h-3.5"
                              />
                              <span className="text-neutral-300">Run RAG Document Search</span>
                            </label>

                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={jsonMode}
                                onChange={(e) => setJsonMode(e.target.checked)}
                                className="rounded border-neutral-800 text-violet-600 focus:ring-violet-500 bg-neutral-900 w-3.5 h-3.5"
                              />
                              <span className="text-neutral-300">JSON Output Mode</span>
                            </label>
                          </div>

                          {/* System Prompt Custom instructions */}
                          <div className="md:col-span-3 flex flex-col gap-1 mt-1">
                            <label className="text-neutral-400 font-semibold">Custom System Prompt Override</label>
                            <textarea
                              placeholder="Inject guidelines to shape AI agent behavior..."
                              value={systemPrompt}
                              onChange={(e) => setSystemPrompt(e.target.value)}
                              className="w-full bg-neutral-950 border border-white/5 rounded p-2 text-xs text-white focus:outline-none focus:border-violet-500/50 h-16 resize-none"
                            />
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Messages list viewport */}
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
                        description="Send a message below, toggle prompt overrides, or record your voice."
                        compact
                      />
                    ) : (
                      <>
                        {messages.map((m: Message, idx: number) => (
                          <MessageBubble key={m.id} message={m} idx={idx} onDelete={() => handleDeleteMessage(m.id)} />
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
                            onDelete={() => {}}
                          />
                        )}

                        {/* Typing Animation */}
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

                  {/* Attached Files previews above input */}
                  {attachedFiles.length > 0 && (
                    <div className="px-4 py-2 border-t border-white/5 bg-neutral-900/20 flex flex-wrap gap-2 shrink-0">
                      {attachedFiles.map((file) => (
                        <div key={file.id} className="flex items-center gap-2 bg-neutral-950 border border-white/10 px-2.5 py-1 rounded-lg text-[10px] text-neutral-300">
                          <Paperclip className="w-3 h-3 text-violet-400 shrink-0" />
                          <span className="truncate max-w-[120px] font-semibold">{file.name}</span>
                          <span className="text-[8px] text-neutral-500 font-mono shrink-0">({Math.round(file.size / 1024)} KB)</span>
                          <button
                            onClick={() => removeAttachment(file.id)}
                            className="p-0.5 hover:text-rose-400 text-neutral-500 transition-all shrink-0 bg-transparent border-0 cursor-pointer"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Input form footer */}
                  <div className="p-4 border-t border-white/5 bg-neutral-900/20 shrink-0">
                    {isRecording ? (
                      // Voice Recording active layout
                      <div className="flex justify-between items-center bg-violet-950/10 border border-violet-500/20 rounded-xl p-3 animate-pulse">
                        <div className="flex items-center gap-3">
                          <CircleDot className="w-4 h-4 text-rose-500 animate-ping" />
                          <span className="text-xs font-semibold text-neutral-300">Capturing audio stream:</span>
                          <span className="font-mono text-xs text-white">{recordingSeconds}s</span>
                        </div>
                        <Button
                          type="button"
                          onClick={stopRecording}
                          className="bg-rose-600 hover:bg-rose-700 h-8 px-4 text-xs font-semibold"
                        >
                          Stop & Transcribe
                        </Button>
                      </div>
                    ) : (
                      // Standard text input
                      <form onSubmit={handleSendMessage} className="flex gap-2 items-center">
                        <input
                          type="file"
                          ref={fileInputRef}
                          onChange={handleFileChange}
                          className="hidden"
                          multiple
                        />
                        <button
                          type="button"
                          onClick={handleFileUploadClick}
                          className="p-2 border border-white/5 bg-neutral-950/40 hover:border-violet-500/20 text-neutral-400 hover:text-white rounded-lg transition-all cursor-pointer shrink-0"
                          title="Attach Files"
                          disabled={isUploading}
                        >
                          <Paperclip className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={startRecording}
                          className="p-2 border border-white/5 bg-neutral-950/40 hover:border-violet-500/20 text-neutral-400 hover:text-white rounded-lg transition-all cursor-pointer shrink-0"
                          title="Voice Message"
                        >
                          <Mic className="w-4 h-4" />
                        </button>

                        <Input
                          placeholder="Ask Viptant AI anything... (supports dragging files / pasting clipboard images)"
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
                                className="border-white/5 h-9 w-9 p-0 shrink-0 text-neutral-400 hover:text-white bg-neutral-950"
                                title="Regenerate response"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                            )}
                            <Button
                              type="submit"
                              className="bg-violet-600 hover:bg-violet-700 h-9 px-4 text-xs font-semibold shrink-0 gap-1.5"
                              disabled={!inputMessage.trim() && attachedFiles.length === 0}
                            >
                              <Send className="w-3.5 h-3.5" />
                              Send
                            </Button>
                          </>
                        )}
                      </form>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <EmptyState
                    icon={<MessageSquare className="w-8 h-8 text-neutral-600" />}
                    title="AI Conversations Platform"
                    description="Select a discussion thread from the sidebar or click 'New Chat Session' to start."
                  />
                </div>
              )}
            </div>

            {/* Right Collaboration & Telemetry panel */}
            {showRightPanel && selectedConvId && (
              <div className="h-full overflow-y-auto p-4 flex flex-col gap-5 bg-neutral-950/30">
                {/* Telemetry Detail Info */}
                <div className="flex flex-col gap-2.5">
                  <h4 className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <Sliders className="w-3 h-3" /> Telemetry Info
                  </h4>
                  <div className="bg-neutral-950 border border-white/5 p-3 rounded-lg flex flex-col gap-2 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-neutral-400">Provider</span>
                      <span className="font-semibold text-white font-mono uppercase">{selectedConv?.provider_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-400">Active Model</span>
                      <span className="font-semibold text-white font-mono truncate max-w-[120px]">{selectedConv?.model_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-400">Created Date</span>
                      <span className="font-semibold text-white font-mono">
                        {selectedConv ? new Date(selectedConv.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Collaboration section */}
                <div className="flex flex-col gap-3">
                  <h4 className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <Users className="w-3 h-3" /> Collaborative Team
                  </h4>
                  
                  {/* Participants list */}
                  <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto pr-1">
                    {participants.map((p: Participant) => (
                      <div key={p.id} className="flex justify-between items-center text-[10px] bg-neutral-950 border border-white/5 p-2 rounded-lg gap-2">
                        <span className="truncate text-neutral-300 font-semibold">{p.user_email}</span>
                        {p.role === 'owner' ? (
                          <Badge variant="violet" size="sm">Owner</Badge>
                        ) : (
                          <div className="flex items-center gap-1.5 shrink-0">
                            <select
                              value={p.role}
                              onChange={(e) => handleUpdateParticipantRole(p.user_id, e.target.value)}
                              className="bg-neutral-900 border border-white/5 rounded text-[8px] text-white p-0.5 focus:outline-none"
                            >
                              <option value="member">Member</option>
                              <option value="editor">Editor</option>
                              <option value="viewer">Viewer</option>
                            </select>
                            <button
                              onClick={() => handleRemoveParticipant(p.user_id)}
                              className="text-neutral-500 hover:text-rose-400 p-0.5 bg-transparent border-0 cursor-pointer"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Invite form */}
                  <div className="flex flex-col gap-1.5 border-t border-white/5 pt-2.5">
                    <Input
                      placeholder="Collaborator email..."
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="h-7 text-[10px] bg-neutral-950 border-white/5"
                    />
                    <div className="flex gap-1.5">
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="bg-neutral-950 border border-white/5 rounded text-[10px] text-white px-2 py-1 flex-1 focus:outline-none"
                      >
                        <option value="member">Member</option>
                        <option value="editor">Editor</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      <Button
                        onClick={handleInviteCollaborator}
                        disabled={inviting || !inviteEmail.trim()}
                        className="h-7 text-[9px] px-2.5 font-bold"
                      >
                        Invite
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Sharing section */}
                <div className="flex flex-col gap-2.5 border-t border-white/5 pt-4">
                  <h4 className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <Share2 className="w-3 h-3" /> Sharing & Export
                  </h4>
                  
                  {shareLink ? (
                    <div className="flex items-center gap-1 bg-neutral-950 border border-white/5 p-1 rounded-lg">
                      <input
                        type="text"
                        readOnly
                        value={shareLink}
                        className="flex-1 bg-transparent border-0 font-mono text-[8px] text-violet-400 px-1 focus:outline-none"
                      />
                      <button
                        onClick={handleCopyShareLink}
                        className="p-1 hover:text-violet-400 text-neutral-500 transition-all shrink-0 bg-transparent border-0 cursor-pointer"
                        title="Copy Link"
                      >
                        <Clipboard className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateShareToken}
                      className="w-full text-[10px] h-7 border-white/5"
                    >
                      Create Shareable link
                    </Button>
                  )}

                  {/* Export Options */}
                  <div className="grid grid-cols-3 gap-1.5 mt-1.5">
                    {(['markdown', 'json', 'txt'] as const).map((format) => (
                      <button
                        key={format}
                        onClick={() => handleExport(format)}
                        className="py-1 rounded bg-neutral-950 hover:bg-neutral-900 border border-white/5 text-[9px] font-semibold text-neutral-300 uppercase transition-all cursor-pointer"
                      >
                        {format}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
