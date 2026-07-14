'use client';

import * as React from 'react';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import { 
  MessageSquare, Sparkles, Plus, Send, Trash2, BookOpen, Bot, 
  ChevronRight, UploadCloud, Copy, RefreshCw, BarChart2, Star
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Dialog } from '@/components/ui/dialog';
import { apiClient } from '@/services/api-client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';

export default function AIPayground() {
  const queryClient = useQueryClient();
  const { activeOrg } = useAuthStore();
  const [activeTab, setActiveTab] = React.useState<'chat' | 'variants' | 'knowledge'>('chat');

  // Chat settings
  const [selectedModel, setSelectedModel] = React.useState('gemini-1.5-flash');
  const [selectedPromptId, setSelectedPromptId] = React.useState('');
  const [activeConvId, setActiveConvId] = React.useState<string | null>(null);
  const [inputMessage, setInputMessage] = React.useState('');
  
  // Custom Prompt Templates form
  const [newPromptName, setNewPromptName] = React.useState('');
  const [newPromptContent, setNewPromptContent] = React.useState('');

  // Variants generator form
  const [variantForm, setVariantForm] = React.useState({
    title: '',
    topic: '',
    copyType: 'EMAIL',
    tone: 'PROFESSIONAL',
    audience: '',
    keywords: '',
    modelName: 'gemini-1.5-flash'
  });

  // Mock streaming animation status
  const [streamingText, setStreamingText] = React.useState('');
  const [isStreaming, setIsStreaming] = React.useState(false);

  // ----------------------------------------------------
  // React Query Queries
  // ----------------------------------------------------
  const { data: conversations = [], isLoading: loadingConvs } = useQuery({
    queryKey: ['conversations', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/conversations/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: prompts = [], isLoading: loadingPrompts } = useQuery({
    queryKey: ['prompts', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/ai/prompts/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  const { data: messages = [], isLoading: loadingMsgs, refetch: refetchMessages } = useQuery({
    queryKey: ['messages', activeConvId],
    queryFn: async () => {
      if (!activeConvId) return [];
      const res = await apiClient.get(`/ai/conversations/${activeConvId}/messages`);
      return res.data || [];
    },
    enabled: !!activeConvId,
  });

  const { data: copies = [], refetch: refetchCopies } = useQuery({
    queryKey: ['generated-copies', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/generator/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  // ----------------------------------------------------
  // Mutations Hooks
  // ----------------------------------------------------
  const createConvMutation = useMutation({
    mutationFn: (data: { title: string }) => apiClient.post('/ai/conversations/', data),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setActiveConvId(res.data.id);
      toast.success('Session Initialized', 'A new AI chat thread has been created.');
    }
  });

  const deleteConvMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/ai/conversations/${id}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (activeConvId === variables) setActiveConvId(null);
      toast.success('Session Removed', 'Chat history has been cleared.');
    }
  });

  const createPromptMutation = useMutation({
    mutationFn: (data: { name: string; content: string }) => apiClient.post('/ai/prompts/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setNewPromptName('');
      setNewPromptContent('');
      toast.success('Prompt Saved', 'Added to organizational templates library.');
    }
  });

  const deletePromptMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/ai/prompts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      setSelectedPromptId('');
      toast.success('Prompt Deleted', 'Template removed.');
    }
  });

  const postMessageMutation = useMutation({
    mutationFn: (data: { content: string; model_name: string; prompt_id: string | null }) => 
      apiClient.post(`/ai/conversations/${activeConvId}/messages`, data),
    onSuccess: (res) => {
      // Simulate typing/streaming animation for premium effect
      const reply = res.data.content || '';
      animateStreamingResponse(reply);
    },
    onError: () => {
      setIsStreaming(false);
      toast.error('Error', 'Failed to generate model response.');
    }
  });

  const generateCopyMutation = useMutation({
    mutationFn: (data: typeof variantForm) => apiClient.post('/generator/', {
      title: data.title,
      topic: data.topic,
      copy_type: data.copyType,
      tone: data.tone,
      audience: data.audience,
      keywords: data.keywords,
      model_name: data.modelName
    }),
    onSuccess: () => {
      refetchCopies();
      toast.success('A/B Copy Created', 'AI has generated Variants A (creative) and B (CTA).');
    },
    onError: () => toast.error('Error', 'Failed to generate variants.')
  });

  // ----------------------------------------------------
  // Action Handlers
  // ----------------------------------------------------
  const animateStreamingResponse = (fullText: string) => {
    setIsStreaming(true);
    setStreamingText('');
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < fullText.length) {
        setStreamingText((prev) => prev + fullText.charAt(idx));
        idx += 3; // stream 3 chars at a time for smooth quick rendering
      } else {
        clearInterval(interval);
        setIsStreaming(false);
        queryClient.invalidateQueries({ queryKey: ['messages', activeConvId] });
      }
    }, 15);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeConvId || isStreaming) return;
    
    postMessageMutation.mutate({
      content: inputMessage,
      model_name: selectedModel,
      prompt_id: selectedPromptId || null
    });
    
    setInputMessage('');
  };

  const handleCreatePrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPromptName.trim() || !newPromptContent.trim()) return;
    createPromptMutation.mutate({ name: newPromptName, content: newPromptContent });
  };

  const handleGenerateCopy = (e: React.FormEvent) => {
    e.preventDefault();
    if (!variantForm.title || !variantForm.topic) {
      toast.error('Details Required', 'Please specify topic description and a title.');
      return;
    }
    generateCopyMutation.mutate(variantForm);
  };

  // Drag and drop documents setup
  const [uploadedDocs, setUploadedDocs] = React.useState<{ name: string; size: string; date: string }[]>([]);
  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      setUploadedDocs(prev => [
        { name: file.name, size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`, date: new Date().toLocaleDateString() },
        ...prev
      ]);
    });
    toast.success('Document Ingested', `${acceptedFiles.length} file(s) ingested to active organization Knowledge Base.`);
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  const activeConv = conversations.find((c: any) => c.id === activeConvId);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Title Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            AI Workspace <Bot className="w-6 h-6 text-violet-500" />
          </h1>
          <p className="text-neutral-400 mt-1">Develop templates, generate A/B variants, and chat with contextual model nodes.</p>
        </div>

        {/* Tab triggers */}
        <div className="flex rounded-lg bg-neutral-900 border border-white/5 p-1 text-xs self-start">
          {[
            { id: 'chat', label: 'AI Chat Sandbox' },
            { id: 'variants', label: 'A/B Content Variants' },
            { id: 'knowledge', label: 'Knowledge Base' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-1.5 rounded font-semibold transition-all cursor-pointer ${
                activeTab === tab.id ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Grid workspace */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 items-start h-[calc(100vh-200px)] overflow-hidden">
        
        {/* ================================================== */}
        {/* TAB 1: AI CHAT WORKSPACE */}
        {/* ================================================== */}
        {activeTab === 'chat' && (
          <>
            {/* Left Column: Chat threads & Templates */}
            <div className="xl:col-span-1 border border-white/5 bg-neutral-950/40 rounded-xl p-5 flex flex-col gap-6 h-full overflow-y-auto">
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Conversations</span>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => createConvMutation.mutate({ title: `Session ${conversations.length + 1}` })}
                    className="h-6 w-6 p-0"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </Button>
                </div>

                <div className="flex flex-col gap-1 max-h-40 overflow-y-auto pr-1">
                  {conversations.map((c: any) => (
                    <div
                      key={c.id}
                      onClick={() => setActiveConvId(c.id)}
                      className={`flex items-center justify-between p-2 rounded text-xs transition-colors cursor-pointer group ${
                        activeConvId === c.id ? 'bg-violet-500/10 text-violet-400 font-semibold border-l-2 border-violet-500' : 'text-neutral-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <span className="truncate">{c.title}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConvMutation.mutate(c.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-neutral-500 hover:text-rose-400 transition-opacity"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prompt Library */}
              <div className="flex flex-col gap-4 border-t border-white/5 pt-5">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" /> Prompt Templates
                </span>
                
                <div className="flex flex-col gap-2 max-h-44 overflow-y-auto pr-1">
                  {prompts.map((p: any) => (
                    <div
                      key={p.id}
                      onClick={() => setSelectedPromptId(selectedPromptId === p.id ? '' : p.id)}
                      className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all ${
                        selectedPromptId === p.id ? 'border-violet-500/50 bg-violet-500/5 text-violet-300' : 'border-white/5 bg-neutral-900/20 text-neutral-400 hover:text-white'
                      }`}
                    >
                      <div className="flex justify-between items-center text-xs font-bold">
                        <span>{p.name}</span>
                        <span className="text-[9px] text-violet-400">v{p.version}</span>
                      </div>
                      <p className="text-[10px] text-neutral-500 mt-1 truncate">{p.content}</p>
                    </div>
                  ))}
                </div>

                {/* Create template form */}
                <form onSubmit={handleCreatePrompt} className="flex flex-col gap-2 pt-2">
                  <Input
                    placeholder="Short Title"
                    required
                    value={newPromptName}
                    onChange={(e) => setNewPromptName(e.target.value)}
                    className="h-8 text-xs"
                  />
                  <textarea
                    placeholder="System prompt instructions..."
                    required
                    value={newPromptContent}
                    onChange={(e) => setNewPromptContent(e.target.value)}
                    rows={2}
                    className="w-full text-xs rounded-lg border border-white/10 bg-neutral-950/60 p-2 text-white placeholder-neutral-500 focus:outline-none focus:border-violet-500"
                  />
                  <Button type="submit" variant="violet" size="sm" className="h-8 text-xs">
                    Save Prompt Template
                  </Button>
                </form>
              </div>
            </div>

            {/* Right Column: Chat Screen */}
            <div className="xl:col-span-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col justify-between h-full overflow-hidden">
              {activeConvId ? (
                <>
                  {/* Context bar config */}
                  <div className="h-14 border-b border-white/5 px-6 flex items-center justify-between bg-neutral-900/20 shrink-0">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-violet-400" />
                      <span className="font-bold text-sm">{activeConv?.title}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Engine:</span>
                      <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="px-2.5 py-1 text-xs rounded bg-neutral-900 border border-white/15 text-white focus:outline-none focus:border-violet-500 cursor-pointer"
                      >
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                        <option value="gpt-4o">OpenAI GPT-4o</option>
                        <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                      </select>
                    </div>
                  </div>

                  {/* Messages Bubble Area */}
                  <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-4">
                    {messages.map((m: any) => (
                      <div
                        key={m.id}
                        className={`flex gap-3 max-w-[80%] ${m.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                      >
                        <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs select-none shrink-0 ${
                          m.role === 'user' ? 'bg-violet-600/10 border-violet-500/20 text-violet-400' : 'bg-neutral-800 border-white/5 text-neutral-300'
                        }`}>
                          {m.role === 'user' ? 'U' : 'AI'}
                        </div>

                        <div className={`p-3 rounded-xl border text-sm ${
                          m.role === 'user' ? 'bg-violet-600/5 border-violet-500/20 text-white' : 'bg-neutral-900/30 border-white/5 text-neutral-300'
                        }`}>
                          <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                          {m.model_used && (
                            <span className="block text-[8px] text-neutral-600 mt-2 tracking-wider uppercase font-semibold">
                              {m.model_used}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Stream mock bubble */}
                    {isStreaming && (
                      <div className="flex gap-3 max-w-[80%]">
                        <div className="w-8 h-8 rounded-full bg-neutral-800 border border-white/5 flex items-center justify-center font-bold text-xs text-neutral-300 shrink-0">
                          AI
                        </div>
                        <div className="p-3 rounded-xl border border-white/5 bg-neutral-900/30 text-sm text-neutral-300">
                          <p className="whitespace-pre-wrap leading-relaxed">{streamingText}</p>
                          <span className="w-1.5 h-4 bg-violet-400 inline-block animate-pulse ml-0.5 align-middle" />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Message Input Trigger */}
                  <div className="p-4 border-t border-white/5 bg-neutral-900/10 shrink-0">
                    <form onSubmit={handleSendMessage} className="flex gap-3">
                      <Input
                        placeholder="Ask the AI marketing agent to draft copy, refine strategy..."
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        disabled={postMessageMutation.isPending || isStreaming}
                        className="h-11"
                      />
                      <Button 
                        type="submit" 
                        variant="violet" 
                        isLoading={postMessageMutation.isPending || isStreaming}
                        className="px-6 h-11 shrink-0"
                      >
                        Send
                      </Button>
                    </form>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-4">
                  <MessageSquare className="w-12 h-12 text-neutral-600 animate-pulse" />
                  <h3 className="text-base font-bold text-neutral-300">No Active Chat Session</h3>
                  <p className="text-xs text-neutral-500 max-w-xs leading-relaxed">
                    Select an existing session from the sidebar or click the plus button to create a new thread.
                  </p>
                  <Button variant="violet" onClick={() => createConvMutation.mutate({ title: `Session ${conversations.length + 1}` })}>
                    Start New Chat Thread
                  </Button>
                </div>
              )}
            </div>
          </>
        )}

        {/* ================================================== */}
        {/* TAB 2: A/B CONTENT VARIANTS */}
        {/* ================================================== */}
        {activeTab === 'variants' && (
          <>
            {/* Left Column: Generator Configuration */}
            <div className="xl:col-span-1 border border-white/5 bg-neutral-950/40 rounded-xl p-5 flex flex-col gap-6 h-full overflow-y-auto">
              <h3 className="text-xs font-bold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-violet-400" /> Variant Config
              </h3>

              <form onSubmit={handleGenerateCopy} className="flex flex-col gap-4">
                <Input
                  label="Title/Label"
                  placeholder="Acme Summer Promo Ad"
                  required
                  value={variantForm.title}
                  onChange={(e) => setVariantForm({ ...variantForm, title: e.target.value })}
                />

                <Input
                  label="Topic / Description"
                  placeholder="SaaS platform summer subscription discounts"
                  required
                  value={variantForm.topic}
                  onChange={(e) => setVariantForm({ ...variantForm, topic: e.target.value })}
                />

                <Select
                  label="Copy Style Type"
                  options={[
                    { label: 'Email Outreach Body', value: 'EMAIL' },
                    { label: 'Social Ad Copy', value: 'AD' },
                    { label: 'Newsletter Blast', value: 'NEWSLETTER' }
                  ]}
                  value={variantForm.copyType}
                  onChange={(e) => setVariantForm({ ...variantForm, copyType: e.target.value })}
                />

                <Select
                  label="Brand Tone"
                  options={[
                    { label: 'Professional', value: 'PROFESSIONAL' },
                    { label: 'Casual / Friendly', value: 'CASUAL' },
                    { label: 'Excited / Bold', value: 'EXCITED' }
                  ]}
                  value={variantForm.tone}
                  onChange={(e) => setVariantForm({ ...variantForm, tone: e.target.value })}
                />

                <Input
                  label="Target Audience"
                  placeholder="Freelancers & Entrepreneurs"
                  value={variantForm.audience}
                  onChange={(e) => setVariantForm({ ...variantForm, audience: e.target.value })}
                />

                <Input
                  label="Focus Keywords (comma-sep)"
                  placeholder="AI, automation, save time"
                  value={variantForm.keywords}
                  onChange={(e) => setVariantForm({ ...variantForm, keywords: e.target.value })}
                />

                <Select
                  label="Model Engine"
                  options={[
                    { label: 'Gemini 1.5 Flash', value: 'gemini-1.5-flash' },
                    { label: 'GPT-4o', value: 'gpt-4o' }
                  ]}
                  value={variantForm.modelName}
                  onChange={(e) => setVariantForm({ ...variantForm, modelName: e.target.value })}
                />

                <Button type="submit" variant="violet" isLoading={generateCopyMutation.isPending} className="w-full mt-2">
                  Generate Variants
                </Button>
              </form>
            </div>

            {/* Right Column: Variant A/B ratings workspace */}
            <div className="xl:col-span-3 border border-white/5 bg-neutral-950/20 rounded-xl flex flex-col gap-6 p-6 h-full overflow-y-auto">
              <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <div>
                  <h3 className="font-bold text-base text-white">Generated Variant Hub</h3>
                  <p className="text-xs text-neutral-400 mt-1">Review copy outputs and rate them for performance tracking.</p>
                </div>
              </div>

              {copies.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-12">
                  <Copy className="w-12 h-12 text-neutral-600 mb-4" />
                  <h4 className="text-base font-bold text-neutral-300">No Variants Drafted</h4>
                  <p className="text-xs text-neutral-500 mt-1 max-w-xs">
                    Submit the form on the left to write Variant A (Creative Narrative) and Variant B (Direct CTA) side-by-side.
                  </p>
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {copies.map((copy: any) => (
                    <Card key={copy.id} className="glass p-5 flex flex-col gap-4 border-white/5">
                      <div className="flex justify-between items-start border-b border-white/5 pb-3">
                        <div>
                          <h4 className="font-bold text-sm text-white">{copy.title}</h4>
                          <p className="text-[10px] text-neutral-500 mt-0.5">Prompt used: {copy.prompt_used}</p>
                        </div>
                        <span className="text-[10px] text-neutral-500">{new Date(copy.created_at || '').toLocaleDateString()}</span>
                      </div>

                      {/* Display variants side-by-side */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {(copy.variants || []).map((v: any) => (
                          <div key={v.id} className="p-4 rounded-lg bg-neutral-900/60 border border-white/5 flex flex-col justify-between gap-4">
                            <div>
                              <div className="flex justify-between items-center text-[10px] uppercase font-bold text-violet-400 mb-3">
                                <span>{v.variant_label}</span>
                                <span className="text-neutral-500">{v.model_used}</span>
                              </div>
                              <p className="text-xs text-neutral-200 whitespace-pre-wrap leading-relaxed">{v.content}</p>
                            </div>
                            
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => {
                                toast.success('Vote Registered', 'Thank you! Your feedback helps train future generations.');
                              }}
                              className="h-8 gap-2 text-xs border-violet-500/20 text-violet-400 hover:bg-violet-500/10 self-start"
                            >
                              <Star className="w-3.5 h-3.5 fill-current" /> Vote Preferred
                            </Button>
                          </div>
                        ))}
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* ================================================== */}
        {/* TAB 3: KNOWLEDGE BASE UPLOAD */}
        {/* ================================================== */}
        {activeTab === 'knowledge' && (
          <div className="xl:col-span-4 border border-white/5 bg-neutral-950/20 rounded-xl p-8 flex flex-col gap-8 h-full overflow-y-auto">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Knowledge Base Ingest <UploadCloud className="w-5 h-5 text-violet-500" />
              </h2>
              <p className="text-xs text-neutral-400 mt-1">
                Upload business context documents (PDF, DOCX, TXT) to vectorize them automatically inside PostgreSQL PGVector.
              </p>
            </div>

            {/* Custom File Drop-zone */}
            <div 
              {...getRootProps()} 
              className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center gap-4 text-center cursor-pointer transition-all ${
                isDragActive ? 'border-violet-500 bg-violet-500/5' : 'border-white/10 hover:border-violet-500/30'
              }`}
            >
              <input {...getInputProps()} />
              <div className="p-4 rounded-full bg-neutral-900 border border-white/5 text-violet-400">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Drag & drop files here, or click to browse</p>
                <p className="text-xs text-neutral-500 mt-1">Supports PDF, DOCX, TXT up to 10MB each.</p>
              </div>
            </div>

            {/* Ingested Documents List */}
            <div className="flex flex-col gap-4">
              <h3 className="font-bold text-sm text-white">Ingested Document Libraries ({uploadedDocs.length})</h3>
              {uploadedDocs.length === 0 ? (
                <p className="text-xs text-neutral-500 py-6 text-center">No documents uploaded to this workspace yet.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {uploadedDocs.map((doc, idx) => (
                    <Card key={idx} className="glass p-4 border-white/5 flex flex-col justify-between gap-4">
                      <div>
                        <h4 className="font-bold text-xs truncate text-white">{doc.name}</h4>
                        <span className="text-[10px] text-neutral-500 mt-1 block">Vectorized on {doc.date} • {doc.size}</span>
                      </div>
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 self-start">
                        VECOTR INDEX ACTIVE
                      </span>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        
      </div>
    </div>
  );
}
