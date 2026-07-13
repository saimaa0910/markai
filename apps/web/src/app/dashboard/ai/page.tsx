'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import {
  MessageSquare,
  Sparkles,
  Plus,
  Send,
  Loader2,
  ArrowLeft,
  Trash2,
  Terminal,
  BookOpen,
  Bot
} from 'lucide-react';

export default function AIPayground() {
  const router = useRouter();
  const { token, activeOrgId } = useAuthStore();

  // Sessions and Prompts Lists
  const [conversations, setConversations] = React.useState<any[]>([]);
  const [prompts, setPrompts] = React.useState<any[]>([]);
  const [activeConvId, setActiveConvId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<any[]>([]);

  // Configurations
  const [selectedModel, setSelectedModel] = React.useState('gemini-1.5-flash');
  const [selectedPromptId, setSelectedPromptId] = React.useState('');

  // UI state
  const [loading, setLoading] = React.useState(true);
  const [messagesLoading, setMessagesLoading] = React.useState(false);
  const [sending, setSending] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Forms
  const [newPromptName, setNewPromptName] = React.useState('');
  const [newPromptContent, setNewPromptContent] = React.useState('');
  const [inputMessage, setInputMessage] = React.useState('');

  // Guard routing
  React.useEffect(() => {
    if (!token) {
      router.push('/auth/login');
    }
  }, [token, router]);

  // Load baseline sessions & prompt library
  const fetchBaseData = React.useCallback(async () => {
    if (!token || !activeOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': activeOrgId,
      };

      const [convsRes, promptsRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/ai/conversations/', { headers }),
        fetch('http://localhost:8000/api/v1/ai/prompts/', { headers }),
      ]);

      if (!convsRes.ok || !promptsRes.ok) {
        throw new Error('Failed to retrieve AI platform datasets.');
      }

      const convsData = await convsRes.json();
      const promptsData = await promptsRes.json();

      setConversations(convsData);
      setPrompts(promptsData);

      // Auto-select first conversation session if available and none selected
      if (convsData.length > 0 && !activeConvId) {
        setActiveConvId(convsData[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred loading the playground.');
    } finally {
      setLoading(false);
    }
  }, [token, activeOrgId, activeConvId]);

  React.useEffect(() => {
    fetchBaseData();
  }, [fetchBaseData]);

  // Load message logs when active conversation changes
  const fetchMessages = React.useCallback(async (convId: string) => {
    if (!token || !activeOrgId) return;
    setMessagesLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/ai/conversations/${convId}/messages`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId,
        },
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages(data);
    } catch {
      setError('Failed to fetch message history.');
    } finally {
      setMessagesLoading(false);
    }
  }, [token, activeOrgId]);

  React.useEffect(() => {
    if (activeConvId) {
      fetchMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId, fetchMessages]);

  // Actions
  const handleCreateSession = async () => {
    if (!token || !activeOrgId) return;
    setSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/ai/conversations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId,
        },
        body: JSON.stringify({ title: `Chat Session ${conversations.length + 1}` }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setConversations([data, ...conversations]);
      setActiveConvId(data.id);
    } catch {
      setError('Failed to initialize chat session.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPromptName.trim() || !newPromptContent.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/ai/prompts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify({ name: newPromptName, content: newPromptContent }),
      });
      if (!res.ok) throw new Error();
      setNewPromptName('');
      setNewPromptContent('');
      await fetchBaseData();
    } catch {
      setError('Failed to register prompt template.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeConvId || sending) return;
    setSending(true);
    const contentToSend = inputMessage;
    setInputMessage('');
    
    // Optimistic user bubble append
    const tempUserMessage = {
      id: Math.random().toString(),
      role: 'user',
      content: contentToSend,
      model_used: selectedModel,
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/ai/conversations/${activeConvId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify({
          content: contentToSend,
          model_name: selectedModel,
          prompt_id: selectedPromptId || null,
        }),
      });
      if (!res.ok) throw new Error();
      const assistantMsg = await res.json();
      // Remove the optimistic message and append real database synced logs
      await fetchMessages(activeConvId);
    } catch {
      setError('Failed to generate AI response.');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteConversation = async (convId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/ai/conversations/${convId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
      });
      if (!res.ok) throw new Error();
      if (activeConvId === convId) {
        setActiveConvId(null);
      }
      await fetchBaseData();
    } catch {
      setError('Failed to delete chat session.');
    }
  };

  const activeConv = conversations.find((c) => c.id === activeConvId);

  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col">
      {/* Background glow */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[160px] pointer-events-none" />

      {/* Main Header */}
      <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/dashboard')}
            className="p-2 rounded text-neutral-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-violet-500" /> AI Playground
            </h1>
            <p className="text-xs text-neutral-400">Develop system prompts and route chat workflows.</p>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-6 mt-4 p-4 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Split Screen Panel */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 overflow-hidden">
        
        {/* Left Panel - Sessions & Prompt Library */}
        <div className="border-r border-white/10 bg-zinc-950/40 p-6 space-y-8 overflow-y-auto">
          {/* Chat Sessions */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-2">
                <MessageSquare className="w-3.5 h-3.5" /> Sessions
              </h3>
              <button
                onClick={handleCreateSession}
                disabled={submitting}
                className="p-1 rounded text-violet-400 hover:bg-violet-500/10 transition-colors cursor-pointer"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-neutral-500" />
            ) : (
              <div className="space-y-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`flex items-center justify-between p-2 rounded text-sm transition-colors cursor-pointer group ${
                      activeConvId === conv.id ? 'bg-violet-500/10 text-violet-300' : 'hover:bg-white/5 text-neutral-300'
                    }`}
                    onClick={() => setActiveConvId(conv.id)}
                  >
                    <span className="truncate">{conv.title}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-neutral-500 hover:text-rose-400 transition-opacity cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Prompt Library */}
          <div className="space-y-4 border-t border-white/10 pt-6">
            <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5" /> Prompt Templates
            </h3>

            {/* Prompt List */}
            <div className="space-y-2">
              {prompts.map((p) => (
                <div
                  key={p.id}
                  className={`p-2.5 rounded bg-white/5 border border-white/5 text-xs cursor-pointer hover:border-violet-500/20 transition-all ${
                    selectedPromptId === p.id ? 'border-violet-500/50 bg-violet-500/5' : ''
                  }`}
                  onClick={() => setSelectedPromptId(selectedPromptId === p.id ? '' : p.id)}
                >
                  <div className="flex justify-between font-bold text-neutral-300">
                    <span>{p.name}</span>
                    <span className="text-[10px] text-violet-400">v{p.version}</span>
                  </div>
                  <p className="text-[10px] text-neutral-500 mt-1 line-clamp-2">{p.content}</p>
                </div>
              ))}
            </div>

            {/* Prompt Creator Form */}
            <form onSubmit={handleCreatePrompt} className="space-y-3 pt-2">
              <input
                type="text"
                required
                value={newPromptName}
                onChange={(e) => setNewPromptName(e.target.value)}
                placeholder="Template Name (e.g. Ad Copy)"
                className="w-full px-2.5 py-1.5 rounded bg-white/5 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
              />
              <textarea
                required
                rows={3}
                value={newPromptContent}
                onChange={(e) => setNewPromptContent(e.target.value)}
                placeholder="Template Instructions (e.g. Write a marketing message...)"
                className="w-full px-2.5 py-1.5 rounded bg-white/5 border border-white/10 text-xs focus:border-violet-500 focus:outline-none resize-none"
              />
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-1.5 rounded bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-xs cursor-pointer disabled:opacity-50"
              >
                Save to Library
              </button>
            </form>
          </div>
        </div>

        {/* Right Panel - Playground Chat Stream */}
        <div className="lg:col-span-3 flex flex-col h-full bg-zinc-950/20 overflow-hidden">
          {activeConvId ? (
            <>
              {/* Context bar */}
              <div className="border-b border-white/10 px-6 py-3 bg-zinc-950/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-violet-400" />
                  <span className="font-bold text-sm">{activeConv?.title}</span>
                </div>

                {/* Gateway config parameters */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Model Selector */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Gateway Model:</span>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="px-2 py-1 text-xs rounded bg-neutral-900 border border-white/10 focus:border-violet-500 focus:outline-none text-white cursor-pointer"
                    >
                      <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                      <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      <option value="gpt-4o">OpenAI GPT-4o</option>
                      <option value="gpt-4-turbo">OpenAI GPT-4 Turbo</option>
                      <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                    </select>
                  </div>

                  {/* Active Prompt Injector indicator */}
                  {selectedPromptId && (
                    <span className="px-2 py-1 text-[10px] font-semibold bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded">
                      Prompt Template Linked
                    </span>
                  )}
                </div>
              </div>

              {/* Chat Stream Bubble area */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4">
                {messagesLoading ? (
                  <div className="h-full flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto">
                    <Sparkles className="w-8 h-8 text-neutral-500 mb-3 animate-pulse" />
                    <h4 className="font-bold text-sm text-neutral-300">Prompt Sandbox Ready</h4>
                    <p className="text-xs text-neutral-500 mt-1">Configure your LLM provider on the top bar and submit a question to query the LLM gateway.</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                    >
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                        msg.role === 'user' ? 'bg-violet-600' : 'bg-neutral-800'
                      }`}>
                        {msg.role === 'user' ? 'U' : 'AI'}
                      </div>
                      
                      <div className={`p-3.5 rounded-lg text-sm relative group ${
                        msg.role === 'user' ? 'bg-violet-600/10 border border-violet-500/20 text-neutral-100' : 'bg-white/5 border border-white/5 text-neutral-300'
                      }`}>
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        
                        {msg.role === 'assistant' && (
                          <span className="absolute bottom-1 right-2 text-[9px] text-neutral-600 select-none">
                            {msg.model_used}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Message Input box */}
              <div className="border-t border-white/10 p-4 bg-zinc-950/40">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="text"
                    required
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Enter your prompt or request..."
                    className="flex-1 px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={sending || !inputMessage.trim()}
                    className="px-5 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors flex items-center justify-center cursor-pointer disabled:opacity-50"
                  >
                    {sending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
              <Sparkles className="w-12 h-12 text-neutral-600 mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-neutral-300">No Chat Session Active</h3>
              <p className="text-sm text-neutral-500 mt-2 max-w-sm">Create a new chat session from the left sidebar to initialize the LLM gateway playground.</p>
              <button
                onClick={handleCreateSession}
                className="mt-6 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm cursor-pointer"
              >
                Create First Session
              </button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
