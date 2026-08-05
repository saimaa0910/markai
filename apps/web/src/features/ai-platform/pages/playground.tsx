import * as React from 'react';
import { useModels, useProviders } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Textarea, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Terminal, Sparkles, RefreshCw, Play, Square, Download, Upload,
  Copy, Save, FileText, Code, Table, Eye, Settings2, Sliders, Info, Activity,
  Plus, Trash2, Edit3, Check, X, ChevronDown, ChevronUp, Cpu, Bot, Settings,
  MessageSquare, User, Loader2, Send, Bookmark, BarChart2
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '@/services/api-client';
import { useAuthStore } from '@/store/auth';

interface AgentLogEvent {
  type: string;
  message: string;
  data?: any;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  isAgent?: boolean;
  agentLogs?: AgentLogEvent[];
  latencyMs?: number;
  tokensUsed?: number;
  costUsd?: number;
}

interface PlaygroundSession {
  id: string;
  name: string;
  provider: string;
  model: string;
  temperature: number;
  system_prompt?: string;
  created_at: string;
}

export function PlaygroundPage() {
  const queryClient = useQueryClient();
  const { models } = useModels();
  const { providers } = useProviders();

  // Active Workspace / Org state
  const { activeOrg, accessToken } = useAuthStore();
  const orgId = activeOrg?.id || '';

  // Mode tab: 'models' | 'agents'
  const [activeTab, setActiveTab] = React.useState<'models' | 'agents'>('models');

  // Selected Agent definitions
  const { data: agentsData, isLoading: loadingAgents } = useQuery<any>({
    queryKey: ['agents-definitions', orgId],
    queryFn: async () => {
      const res = await apiClient.get('/agents/definitions');
      return res.data;
    },
    enabled: !!orgId,
  });

  const agents = React.useMemo(() => {
    if (!agentsData) return [];
    if (Array.isArray(agentsData)) return agentsData;
    return agentsData.items || agentsData.results || [];
  }, [agentsData]);

  const [selectedAgentId, setSelectedAgentId] = React.useState('');

  // Selected Provider & Model keys
  const [selProv, setSelProv] = React.useState('openai');
  const [selModel, setSelModel] = React.useState('');

  // Settings Panel State
  const [temperature, setTemperature] = React.useState(0.7);
  const [topP, setTopP] = React.useState(0.9);
  const [maxTokens, setMaxTokens] = React.useState(2048);
  const [systemPrompt, setSystemPrompt] = React.useState('You are a helpful AI assistant.');
  const [userPrompt, setUserPrompt] = React.useState('');

  // Sessions and Messages History
  const [sessions, setSessions] = React.useState<PlaygroundSession[]>([]);
  const [activeSession, setActiveSession] = React.useState<PlaygroundSession | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [loadingSessions, setLoadingSessions] = React.useState(false);
  const [loadingMessages, setLoadingMessages] = React.useState(false);
  
  // Inline rename session state
  const [renamingSessionId, setRenamingSessionId] = React.useState<string | null>(null);
  const [renameValue, setRenameValue] = React.useState('');

  // Stream States
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [liveStreamOutput, setLiveStreamOutput] = React.useState('');
  const [liveAgentLogs, setLiveAgentLogs] = React.useState<AgentLogEvent[]>([]);
  
  // AbortController reference
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const chatEndRef = React.useRef<HTMLDivElement | null>(null);

  // Set default model on provider load
  React.useEffect(() => {
    const provModels = models.filter((m) => m.provider === selProv);
    if (provModels.length > 0) {
      setSelModel(provModels[0].model_name);
    }
  }, [selProv, models]);

  // Set default agent on agents load
  React.useEffect(() => {
    if (agents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgentId]);

  // Scroll to bottom on new messages
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, liveStreamOutput, liveAgentLogs]);

  // Load playground sessions from backend
  const loadSessions = async () => {
    if (!orgId) return;
    setLoadingSessions(true);
    try {
      const res = await apiClient.get('/ai/playground/sessions');
      const loaded: PlaygroundSession[] = res.data || [];
      setSessions(loaded);
      if (loaded.length > 0 && !activeSession) {
        handleSelectSession(loaded[0]);
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  React.useEffect(() => {
    loadSessions();
  }, [orgId]);

  // Select a session and fetch messages
  const handleSelectSession = async (session: PlaygroundSession) => {
    setActiveSession(session);
    setLoadingMessages(true);
    setLiveStreamOutput('');
    setLiveAgentLogs([]);
    try {
      const res = await apiClient.get(`/ai/playground/sessions/${session.id}/messages`);
      setMessages(res.data || []);
      
      // Sync parameters from active session settings
      setSelProv(session.provider);
      setSelModel(session.model);
      setTemperature(Number(session.temperature));
      if (session.system_prompt) {
        setSystemPrompt(session.system_prompt);
      }
    } catch (err) {
      console.error('Failed to load messages', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  // Create new session
  const handleCreateSession = async () => {
    try {
      const name = activeTab === 'models' ? `Chat via ${selModel}` : `Agent: ${agents.find((a: any) => a.id === selectedAgentId)?.name || 'Session'}`;
      const res = await apiClient.post('/ai/playground/sessions', {
        name,
        provider: selProv,
        model: activeTab === 'models' ? selModel : 'agent-preferred',
        temperature,
        system_prompt: systemPrompt
      });
      const newSess: PlaygroundSession = res.data;
      setSessions((prev) => [newSess, ...prev]);
      setActiveSession(newSess);
      setMessages([]);
      setLiveStreamOutput('');
      setLiveAgentLogs([]);
      toast.success('Session Created', 'New playground sandbox initialized.');
    } catch (err) {
      toast.error('Error', 'Could not create new playground session.');
    }
  };

  // Delete session
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/ai/playground/sessions/${id}`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSession?.id === id) {
        setActiveSession(null);
        setMessages([]);
      }
      toast.success('Session Deleted', 'Sandbox history deleted successfully.');
    } catch (err) {
      toast.error('Error', 'Could not delete playground session.');
    }
  };

  // Rename session
  const handleRenameSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!renameValue.trim()) return;
    try {
      await apiClient.patch(`/ai/playground/sessions/${id}`, { name: renameValue });
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, name: renameValue } : s))
      );
      if (activeSession?.id === id) {
        setActiveSession((prev) => prev ? { ...prev, name: renameValue } : null);
      }
      setRenamingSessionId(null);
      toast.success('Session Renamed', 'Session settings updated.');
    } catch (err) {
      toast.error('Error', 'Could not rename session.');
    }
  };

  // Import chat session from JSON
  const handleImportSession = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        if (data.messages && Array.isArray(data.messages)) {
          // Create session
          const sessionName = data.name || `Imported: ${data.model || 'Chat'}`;
          const sessRes = await apiClient.post('/ai/playground/sessions', {
            name: sessionName,
            provider: data.provider || 'openai',
            model: data.model || 'gpt-4o-mini',
            temperature: data.temperature || 0.7,
            system_prompt: data.system_prompt || 'You are a helpful assistant.'
          });
          
          const newSess: PlaygroundSession = sessRes.data;
          setSessions((prev) => [newSess, ...prev]);
          setActiveSession(newSess);
          
          // Add all messages
          for (const msg of data.messages) {
            await apiClient.post(`/ai/playground/sessions/${newSess.id}/messages`, {
              role: msg.role,
              content: msg.content
            });
          }
          
          handleSelectSession(newSess);
          toast.success('Chat Imported', 'Successfully restored chat configuration.');
        } else {
          toast.error('Invalid Format', 'JSON file must contain an array of messages.');
        }
      } catch (err) {
        toast.error('Import Failed', 'Could not parse JSON content.');
      }
    };
    reader.readAsText(file);
  };

  // Export current chat session as Markdown
  const handleExportMarkdown = () => {
    if (messages.length === 0) {
      toast.error('No Messages', 'Nothing to export.');
      return;
    }
    
    let content = `# AI Playground Session: ${activeSession?.name || 'Transcript'}\n`;
    content += `*Date: ${new Date().toLocaleDateString()}*\n`;
    content += `*Model: ${activeSession?.model} (${activeSession?.provider})*\n`;
    content += `*System Prompt:* \`${activeSession?.system_prompt || 'None'}\`\n\n---\n\n`;

    messages.forEach((msg) => {
      content += `### **${msg.role.toUpperCase()}**\n\n${msg.content}\n\n`;
      if (msg.agentLogs && msg.agentLogs.length > 0) {
        content += `> **Agent Execution Summary:**\n`;
        msg.agentLogs.forEach((log) => {
          content += `> - *[${log.type}]* ${log.message}\n`;
        });
        content += `\n`;
      }
    });

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activeSession?.name || 'playground'}_transcript.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Markdown Exported', 'Chat transcript downloaded.');
  };

  // Stop Generation
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    toast.info('Generation Stopped', 'Output pipeline suspended.');
  };

  // Send message and run inferences (Raw Stream or Agent Runtime SSE)
  const handleGenerate = async () => {
    if (isGenerating) return;
    if (!userPrompt.trim()) {
      toast.error('Validation Error', 'Please enter a message prompt.');
      return;
    }

    let session = activeSession;
    if (!session) {
      // Create session on-the-fly if none exists
      try {
        const name = activeTab === 'models' ? `Chat via ${selModel}` : `Agent Run`;
        const res = await apiClient.post('/ai/playground/sessions', {
          name,
          provider: selProv,
          model: activeTab === 'models' ? selModel : 'agent-preferred',
          temperature,
          system_prompt: systemPrompt
        });
        session = res.data;
        setSessions((prev) => [res.data, ...prev]);
        setActiveSession(res.data);
      } catch (err) {
        toast.error('Error', 'Could not create chat session.');
        return;
      }
    }

    if (!session) return;

    const currentPrompt = userPrompt;
    setUserPrompt('');
    setIsGenerating(true);
    setLiveStreamOutput('');
    setLiveAgentLogs([]);

    // Update messages local state with user input
    const userMsg: Message = { role: 'user', content: currentPrompt };
    setMessages((prev) => [...prev, userMsg]);

    // Save user message to database
    try {
      await apiClient.post(`/ai/playground/sessions/${session.id}/messages`, {
        role: 'user',
        content: currentPrompt
      });
    } catch (err) {
      console.error('Failed to save user message to database', err);
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Define endpoint based on models/agents tab
    const urlPath = activeTab === 'models' 
      ? '/ai/playground/stream'
      : `/agents/definitions/${selectedAgentId}/stream`;

    const bodyPayload = activeTab === 'models'
      ? {
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          model_name: selModel,
          temperature,
          system_prompt: systemPrompt
        }
      : {
          user_input: currentPrompt,
          session_id: session.id,
          conversation_history: messages.map(m => ({ role: m.role, content: m.content })),
          run_reflection: true,
          run_evaluation: true
        };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1${urlPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken || ''}`,
          'X-Organization-ID': orgId,
        },
        body: JSON.stringify(bodyPayload),
        signal: controller.signal
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
      let currentEvent = '';
      let textAccumulator = '';
      let metaLatency = 0;
      let metaTokens = 0;
      let metaCost = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const cleanLine = line.trim();
          if (cleanLine.startsWith('event: ')) {
            currentEvent = cleanLine.slice(7).trim();
          } else if (cleanLine.startsWith('data: ')) {
            const dataStr = cleanLine.slice(6).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                
                if (activeTab === 'models') {
                  // Direct models streaming parsing
                  if (parsed.error) {
                    toast.error('Error', parsed.error);
                  } else {
                    const token = parsed.content || parsed.token || '';
                    textAccumulator += token;
                    setLiveStreamOutput(textAccumulator);
                  }
                } else {
                  // Agents SSE Pipeline events parsing
                  if (currentEvent === 'token') {
                    textAccumulator += parsed.token || '';
                    setLiveStreamOutput(textAccumulator);
                  } else if (currentEvent === 'plan') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Plan', message: parsed.thought, data: parsed.steps }
                    ]);
                  } else if (currentEvent === 'tool_call') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Tool Invoke', message: `Calling tool: ${parsed.tool_name}`, data: parsed.params }
                    ]);
                  } else if (currentEvent === 'tool_result') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Tool Result', message: `Output: ${parsed.success ? 'Success' : 'Failure'}`, data: parsed.output || parsed.error }
                    ]);
                  } else if (currentEvent === 'reflection') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Self Reflection', message: parsed.critique, data: parsed.scores }
                    ]);
                  } else if (currentEvent === 'evaluation') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Evaluation Check', message: `Score: ${parsed.correctness_score || 0}`, data: parsed }
                    ]);
                  } else if (currentEvent === 'status') {
                    setLiveAgentLogs((prev) => [
                      ...prev,
                      { type: 'Status', message: parsed.message }
                    ]);
                  } else if (currentEvent === 'done') {
                    metaLatency = parsed.latency_ms || 0;
                    metaTokens = parsed.total_tokens || 0;
                  } else if (currentEvent === 'error') {
                    toast.error('Agent Execution Failed', parsed.message);
                    setLiveAgentLogs((prev) => [...prev, { type: 'Error', message: parsed.message }]);
                  }
                }
              } catch (e) {
                // Ignore partial JSON blocks
              }
            }
          }
        }
      }

      // Generation successful. Add Assistant message to chat history
      const assistantMsg: Message = {
        role: 'assistant',
        content: textAccumulator || 'Run complete.',
        isAgent: activeTab === 'agents',
        agentLogs: liveAgentLogs,
        latencyMs: metaLatency || undefined,
        tokensUsed: metaTokens || undefined,
        costUsd: metaCost || undefined
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
      setLiveStreamOutput('');
      setLiveAgentLogs([]);

      // Save assistant message to database
      try {
        await apiClient.post(`/ai/playground/sessions/${session.id}/messages`, {
          role: 'assistant',
          content: assistantMsg.content
        });
      } catch (err) {
        console.error('Failed to save assistant response', err);
      }

      toast.success('Execution Complete', 'Output successfully synced to database.');
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      toast.error('Inference Failed', err.message || 'Gateway connection timeout.');
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied', 'Text copied to clipboard.');
  };

  return (
    <div className="flex h-[calc(100vh-140px)] gap-4 select-none relative">
      
      {/* 1. LEFT SIDEBAR: SANDBOX SESSION HISTORY */}
      <Card className="w-80 flex flex-col p-4 bg-zinc-950/60 backdrop-blur-xl border-white/5 h-full relative overflow-hidden">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <span className="text-xs text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4 text-violet-400" /> Sandboxes
          </span>
          <div className="flex items-center gap-1">
            <label htmlFor="import-chat" className="p-1.5 rounded bg-neutral-900 border border-white/5 text-neutral-400 hover:text-white cursor-pointer hover:bg-neutral-800 transition-colors">
              <Upload className="w-3.5 h-3.5" />
              <input id="import-chat" type="file" accept=".json" onChange={handleImportSession} className="hidden" />
            </label>
            <Button size="icon" variant="ghost" onClick={handleCreateSession} className="w-7 h-7 bg-violet-600/10 hover:bg-violet-600/20 text-violet-400 rounded">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto mt-3 flex flex-col gap-1.5 pr-1">
          {loadingSessions ? (
            <div className="flex items-center justify-center gap-2 py-20 text-neutral-500 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-violet-400" /> Loading sandboxes...
            </div>
          ) : sessions.length === 0 ? (
            <div className="py-20 text-center text-xs text-neutral-600">
              No sandboxes found. Click + to create one.
            </div>
          ) : (
            sessions.map((sess) => (
              <div
                key={sess.id}
                onClick={() => handleSelectSession(sess)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                  activeSession?.id === sess.id
                    ? 'bg-violet-600/10 border-violet-500/20 text-white'
                    : 'bg-neutral-900/40 border-transparent text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200'
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1">
                  {renamingSessionId === sess.id ? (
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-neutral-950 border border-white/10 text-white text-[11px] rounded px-1.5 py-0.5 w-full focus:outline-none focus:border-violet-500"
                      autoFocus
                    />
                  ) : (
                    <>
                      <Bookmark className={`w-3.5 h-3.5 shrink-0 ${activeSession?.id === sess.id ? 'text-violet-400' : 'text-neutral-500'}`} />
                      <span className="truncate font-medium">{sess.name}</span>
                    </>
                  )}
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {renamingSessionId === sess.id ? (
                    <>
                      <button onClick={(e) => handleRenameSession(sess.id, e)} className="p-0.5 text-emerald-400 hover:text-emerald-300">
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); setRenamingSessionId(null); }} className="p-0.5 text-neutral-400 hover:text-white">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenamingSessionId(sess.id);
                          setRenameValue(sess.name);
                        }}
                        className="p-1 rounded hover:bg-neutral-800 text-neutral-500 hover:text-neutral-200"
                      >
                        <Edit3 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteSession(sess.id, e)}
                        className="p-1 rounded hover:bg-neutral-800 text-rose-500 hover:text-rose-400"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* 2. CENTER PANEL: ACTIVE CHAT SCREEN */}
      <Card className="flex-1 flex flex-col p-4 bg-zinc-950/60 backdrop-blur-xl border-white/5 h-full relative overflow-hidden">
        
        {/* Workspace Mode select */}
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-0.5 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('models')}
              className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded transition-all cursor-pointer ${
                activeTab === 'models' ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
              }`}
            >
              <Cpu className="w-4 h-4" /> Raw Inference Gateway
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded transition-all cursor-pointer ${
                activeTab === 'agents' ? 'bg-violet-600 text-white shadow' : 'text-neutral-400 hover:text-white'
              }`}
            >
              <Bot className="w-4 h-4" /> Agent Runtime IDE
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleExportMarkdown} className="h-8 text-[11px] border-white/5">
              <Download className="w-3.5 h-3.5 mr-1" /> Export Markdown
            </Button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto mt-4 pr-1 flex flex-col gap-4">
          {loadingMessages ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-neutral-500 text-xs">
              <Loader2 className="w-6 h-6 animate-spin text-violet-400" /> Restoring message state...
            </div>
          ) : messages.length === 0 && !liveStreamOutput && liveAgentLogs.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 max-w-sm mx-auto text-neutral-600">
              <Bot className="w-10 h-10 text-violet-500/30" />
              <span className="text-xs font-bold text-neutral-400">Universal Playground Console</span>
              <p className="text-[11px] text-neutral-500 leading-relaxed">
                Configure your routing options in the right pane, type your prompt query below, and run the Gateway pipeline.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col gap-1.5 ${
                    msg.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  <div className={`flex items-center gap-1 text-[10px] text-neutral-500 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    {msg.role === 'user' ? (
                      <>
                        <User className="w-3 h-3 text-neutral-400" />
                        <span>You</span>
                      </>
                    ) : (
                      <>
                        {msg.isAgent ? (
                          <Bot className="w-3.5 h-3.5 text-violet-400" />
                        ) : (
                          <Cpu className="w-3 h-3 text-emerald-400" />
                        )}
                        <span>{msg.isAgent ? 'Agent Runtime' : 'LLM Provider'}</span>
                      </>
                    )}
                  </div>

                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl border text-xs leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-violet-600 border-violet-500/20 text-white rounded-tr-sm font-sans'
                        : 'bg-neutral-900/40 border-white/5 text-neutral-200 rounded-tl-sm font-sans'
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                    {/* Rendering Agent step summary logs */}
                    {msg.agentLogs && msg.agentLogs.length > 0 && (
                      <div className="mt-4 border-t border-white/5 pt-3 flex flex-col gap-2 w-full">
                        <span className="text-[9px] text-neutral-500 uppercase font-bold tracking-wider">Agent Step Logs</span>
                        <div className="flex flex-col gap-1.5">
                          {msg.agentLogs.map((log, lIdx) => (
                            <details key={lIdx} className="group border border-white/5 rounded bg-black/20 p-2 text-[10px]">
                              <summary className="cursor-pointer font-medium text-neutral-400 hover:text-neutral-200 flex items-center justify-between select-none">
                                <span className="flex items-center gap-1.5">
                                  <Sparkles className="w-3 h-3 text-violet-400 shrink-0" />
                                  <strong>[{log.type}]</strong> {log.message}
                                </span>
                                <ChevronDown className="w-3.5 h-3.5 text-neutral-500 group-open:rotate-180 transition-transform" />
                              </summary>
                              {log.data && (
                                <pre className="mt-2 p-2 rounded bg-black text-[9px] font-mono text-neutral-400 border border-white/5 overflow-x-auto whitespace-pre-wrap max-w-full">
                                  {JSON.stringify(log.data, null, 2)}
                                </pre>
                              )}
                            </details>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming placeholder bubble */}
              {(liveStreamOutput || liveAgentLogs.length > 0) && (
                <div className="flex flex-col gap-1.5 items-start">
                  <div className="flex items-center gap-1 text-[10px] text-neutral-500">
                    {activeTab === 'agents' ? (
                      <Bot className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                    ) : (
                      <Cpu className="w-3 h-3 text-emerald-400 shrink-0" />
                    )}
                    <span>Generating output...</span>
                  </div>

                  <div className="max-w-[85%] px-4 py-3 rounded-2xl border border-white/5 bg-neutral-900/40 text-neutral-200 rounded-tl-sm font-sans">
                    <div className="whitespace-pre-wrap font-sans">{liveStreamOutput || 'Initializing connection...'}</div>

                    {liveAgentLogs.length > 0 && (
                      <div className="mt-4 border-t border-white/5 pt-3 flex flex-col gap-2 w-full">
                        <span className="text-[9px] text-neutral-500 uppercase font-bold tracking-wider">Runtime Pipeline Logs</span>
                        <div className="flex flex-col gap-1.5">
                          {liveAgentLogs.map((log, lIdx) => (
                            <details key={lIdx} className="group border border-white/5 rounded bg-black/20 p-2 text-[10px]" open>
                              <summary className="cursor-pointer font-medium text-neutral-400 hover:text-neutral-200 flex items-center justify-between select-none">
                                <span className="flex items-center gap-1.5">
                                  <Loader2 className="w-3 h-3 text-violet-400 animate-spin shrink-0" />
                                  <strong>[{log.type}]</strong> {log.message}
                                </span>
                                <ChevronDown className="w-3.5 h-3.5 text-neutral-500 group-open:rotate-180 transition-transform" />
                              </summary>
                              {log.data && (
                                <pre className="mt-2 p-2 rounded bg-black text-[9px] font-mono text-neutral-400 border border-white/5 overflow-x-auto whitespace-pre-wrap max-w-full">
                                  {JSON.stringify(log.data, null, 2)}
                                </pre>
                              )}
                            </details>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input prompt area */}
        <div className="mt-4 border-t border-white/5 pt-4 flex gap-2 items-end">
          <div className="flex-1 relative">
            <Textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Ask anything or request agent operations..."
              className="bg-neutral-950/60 border-white/5 text-xs h-12 pr-12 focus:outline-none focus:border-violet-500/50 rounded-xl resize-none py-3"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
            />
          </div>

          <div className="flex gap-2">
            {isGenerating ? (
              <Button onClick={handleStop} variant="outline" className="h-10 px-4 text-rose-400 border-rose-500/10 hover:bg-rose-500/10">
                <Square className="w-4 h-4 mr-1 text-rose-400 fill-rose-500/20" /> Stop
              </Button>
            ) : (
              <Button onClick={handleGenerate} variant="violet" className="h-10 px-4">
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* 3. RIGHT PANEL: INFRASTRUCTURE CONFIGURATION */}
      <Card className="w-80 flex flex-col p-4 bg-zinc-950/60 backdrop-blur-xl border-white/5 h-full relative overflow-y-auto">
        <span className="text-xs text-neutral-400 font-bold uppercase tracking-wider flex items-center gap-1.5 pb-3 border-b border-white/5">
          <Settings className="w-4 h-4 text-violet-400" /> Sandbox Parameters
        </span>

        {activeTab === 'models' ? (
          // Models configuration
          <div className="flex flex-col gap-4 mt-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">AI Provider</label>
              <Select
                value={selProv}
                onChange={(e) => setSelProv(e.target.value)}
                className="bg-neutral-900 border-white/5 h-9 text-xs"
                options={providers.map((p) => ({ label: p.name, value: p.key }))}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Model Selector</label>
              <Select
                value={selModel}
                onChange={(e) => setSelModel(e.target.value)}
                className="bg-neutral-900 border-white/5 h-9 text-xs"
                options={models
                  .filter((m) => m.provider === selProv)
                  .map((m) => ({ label: `${m.name} (${m.model_name})`, value: m.model_name }))}
              />
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">System Instructions</label>
              <Textarea 
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="bg-neutral-950/40 border-white/5 text-xs h-24 placeholder-neutral-600 resize-none rounded-lg"
                placeholder="E.g. You are a code generator assistant..."
              />
            </div>
          </div>
        ) : (
          // Agents configuration
          <div className="flex flex-col gap-4 mt-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Active Agent</label>
              {loadingAgents ? (
                <div className="text-xs text-neutral-500 flex items-center gap-1.5 py-1">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-violet-400" /> Loading Agent catalog...
                </div>
              ) : agents.length === 0 ? (
                <div className="text-xs text-rose-400 py-1">
                  No agents created. Add them to Organization settings.
                </div>
              ) : (
                <Select
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="bg-neutral-900 border-white/5 h-9 text-xs"
                  options={agents.map((a: any) => ({ label: a.name, value: a.id }))}
                />
              )}
            </div>

            {selectedAgentId && (
              <div className="p-3 rounded-lg bg-black/30 border border-white/5 text-[11px] text-neutral-400 flex flex-col gap-2 leading-relaxed">
                <div>
                  <strong>Agent Type:</strong> <span className="font-mono text-violet-400 text-[10px]">{agents.find((a: any) => a.id === selectedAgentId)?.agent_type || 'Custom'}</span>
                </div>
                <div>
                  <strong>Preferred model:</strong> <span className="font-mono text-[10px]">{agents.find((a: any) => a.id === selectedAgentId)?.preferred_model || 'auto'}</span>
                </div>
                <div>
                  <strong>Tools allowed:</strong> <span className="font-mono text-[10px]">{agents.find((a: any) => a.id === selectedAgentId)?.allowed_tools?.join(', ') || 'none'}</span>
                </div>
                <div>
                  <strong>Memory bank:</strong> <span className="text-[10px]">{agents.find((a: any) => a.id === selectedAgentId)?.memory_enabled ? 'Active' : 'Disabled'}</span>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="w-full h-px bg-white/5 my-4" />

        {/* Universal Hyperparameters */}
        <div className="flex flex-col gap-4">
          <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
            <Sliders className="w-3.5 h-3.5 text-neutral-600" /> Hyperparameters
          </span>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-neutral-400 font-semibold">Temperature: {temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full accent-violet-600 h-1 rounded-lg"
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-neutral-400 font-semibold">Top P: {topP}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={topP}
              onChange={(e) => setTopP(Number(e.target.value))}
              className="w-full accent-violet-600 h-1 rounded-lg"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Max Completion length</label>
            <Input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              className="bg-neutral-950/40 border-white/5 h-8 text-xs focus:border-violet-500"
            />
          </div>
        </div>
      </Card>

    </div>
  );
}
