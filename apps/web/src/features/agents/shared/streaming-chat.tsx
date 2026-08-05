/**
 * Streaming Chat Component — Sprint 7.1
 * =======================================
 * Real-time SSE streaming chat panel for Agent interaction.
 * Uses fetch-based SSE streaming (POST body) via streamAgentFetch().
 *
 * Features:
 *  - Token-by-token streaming display
 *  - Execution timeline (plan → tools → response)
 *  - Reflection & evaluation badges
 *  - Message history
 *  - Copy / retry actions
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { AgentDefinition, AgentRun, AgentStreamEvent, ToolExecution } from '../types';
import { streamAgentFetch } from '../services';

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  streaming?: boolean;
  runId?: string;
  plan?: any;
  toolCalls?: ToolExecution[];
  reflection?: any;
  evaluation?: any;
  latencyMs?: number;
  tokens?: number;
  error?: string;
}

interface StreamingChatProps {
  agent: AgentDefinition;
  sessionId?: string;
}

const getAuthToken = (): string | null => {
  try {
    const s = localStorage.getItem('eaimos-auth-storage');
    if (!s) return null;
    return JSON.parse(s)?.state?.accessToken ?? null;
  } catch { return null; }
};

const getOrgId = (): string | null => {
  try {
    const s = localStorage.getItem('eaimos-auth-storage');
    if (!s) return null;
    return JSON.parse(s)?.state?.activeOrg?.id ?? null;
  } catch { return null; }
};

export const StreamingChat: React.FC<StreamingChatProps> = ({ agent, sessionId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'agent',
      content: agent.welcome_message || `Hello! I'm ${agent.name}. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState('');
  const [activeToolCalls, setActiveToolCalls] = useState<ToolExecution[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addUserMessage = (content: string) => {
    const msg: Message = { id: `user-${Date.now()}`, role: 'user', content };
    setMessages(prev => [...prev, msg]);
    return msg;
  };

  const addAgentStreamMessage = (): string => {
    const id = `agent-${Date.now()}`;
    setMessages(prev => [...prev, { id, role: 'agent', content: '', streaming: true }]);
    return id;
  };

  const updateAgentMessage = (id: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(m => m.id === id ? { ...m, ...updates } : m));
  };

  const appendToken = (id: string, token: string) => {
    setMessages(prev =>
      prev.map(m => m.id === id ? { ...m, content: m.content + token } : m)
    );
  };

  const sendMessage = useCallback(async () => {
    const userInput = input.trim();
    if (!userInput || streaming) return;

    setInput('');
    setStreaming(true);
    setActiveToolCalls([]);
    addUserMessage(userInput);
    const agentMsgId = addAgentStreamMessage();

    try {
      const history = messages
        .filter(m => m.role !== 'system' && m.id !== 'welcome')
        .slice(-10)
        .map(m => ({ role: m.role === 'agent' ? 'assistant' : m.role, content: m.content }));

      const stream = streamAgentFetch(
        agent.id,
        {
          user_input: userInput,
          session_id: sessionId,
          conversation_history: history,
          run_reflection: true,
          run_evaluation: true,
        },
        getAuthToken,
        getOrgId,
      );

      let currentTools: ToolExecution[] = [];

      for await (const { event, data } of stream) {
        switch (event) {
          case 'agent_start':
            setStreamStatus('Starting...');
            updateAgentMessage(agentMsgId, { runId: data.run_id });
            break;
          case 'context_ready':
            setStreamStatus('Context built ✓');
            break;
          case 'plan':
            setStreamStatus(`Planning: ${data.step_count} step(s)`);
            updateAgentMessage(agentMsgId, { plan: data });
            break;
          case 'tool_call':
            setStreamStatus(`Running: ${data.tool_name}...`);
            currentTools = [...currentTools, { tool_name: data.tool_name, success: false, output: null, error: null }];
            setActiveToolCalls([...currentTools]);
            break;
          case 'tool_result':
            currentTools = currentTools.map((t, i) =>
              i === currentTools.length - 1
                ? { ...t, success: data.success, output: data.output, error: data.error }
                : t
            );
            setActiveToolCalls([...currentTools]);
            updateAgentMessage(agentMsgId, { toolCalls: currentTools });
            break;
          case 'token':
            setStreamStatus('Generating response...');
            appendToken(agentMsgId, data.token || '');
            break;
          case 'reflection':
            updateAgentMessage(agentMsgId, { reflection: data });
            break;
          case 'evaluation':
            updateAgentMessage(agentMsgId, { evaluation: data });
            break;
          case 'done':
            setStreamStatus('');
            updateAgentMessage(agentMsgId, {
              streaming: false,
              latencyMs: data.latency_ms,
              tokens: data.total_tokens,
            });
            break;
          case 'error':
            updateAgentMessage(agentMsgId, {
              streaming: false,
              error: data.message || 'An error occurred',
              content: data.message || 'Something went wrong.',
            });
            break;
          case 'status':
            setStreamStatus(data.message || '');
            break;
        }
      }
    } catch (err: any) {
      updateAgentMessage(agentMsgId, {
        streaming: false,
        error: err.message,
        content: `Error: ${err.message}`,
      });
    } finally {
      setStreaming(false);
      setStreamStatus('');
      setActiveToolCalls([]);
    }
  }, [input, streaming, messages, agent, sessionId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const agentColor = agent.avatar_color || 'violet';
  const colorMap: Record<string, string> = {
    violet: '#7c3aed', blue: '#2563eb', emerald: '#059669',
    amber: '#d97706', rose: '#e11d48', cyan: '#0891b2',
  };
  const primaryColor = colorMap[agentColor] || '#7c3aed';

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)',
      borderRadius: '16px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: 18,
          background: `linear-gradient(135deg, ${primaryColor}40, ${primaryColor}20)`,
          border: `2px solid ${primaryColor}60`,
        }}>
          {agent.avatar || '🤖'}
        </div>
        <div>
          <div style={{ fontWeight: 700, color: '#fff', fontSize: 15 }}>{agent.name}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>{agent.agent_type}</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {streaming && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: primaryColor }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%', background: primaryColor,
                animation: 'pulse 1s infinite',
              }} />
              {streamStatus || 'Streaming...'}
            </div>
          )}
        </div>
      </div>

      {/* Active tool calls during streaming */}
      {streaming && activeToolCalls.length > 0 && (
        <div style={{
          padding: '8px 20px', background: 'rgba(124,58,237,0.06)',
          borderBottom: '1px solid rgba(124,58,237,0.15)',
          display: 'flex', gap: 8, flexWrap: 'wrap',
        }}>
          {activeToolCalls.map((tc, i) => (
            <span key={i} style={{
              padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
              background: tc.success === false && tc.error
                ? 'rgba(239,68,68,0.15)' : tc.output !== null
                ? 'rgba(34,197,94,0.15)' : 'rgba(124,58,237,0.15)',
              color: tc.success === false && tc.error ? '#f87171' : tc.output !== null ? '#4ade80' : '#a78bfa',
              border: `1px solid ${tc.output !== null ? 'rgba(34,197,94,0.3)' : 'rgba(124,58,237,0.3)'}`,
            }}>
              🔧 {tc.tool_name} {tc.output !== null ? '✓' : '...'}
            </span>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.map(msg => (
          <MessageBubble
            key={msg.id}
            message={msg}
            primaryColor={primaryColor}
            onCopy={copyMessage}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <div style={{
          display: 'flex', gap: 12, alignItems: 'flex-end',
          background: 'rgba(255,255,255,0.05)', borderRadius: 12,
          border: '1px solid rgba(255,255,255,0.1)', padding: '12px 16px',
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Message ${agent.name}... (Enter to send, Shift+Enter for newline)`}
            disabled={streaming}
            rows={1}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: '#fff', fontSize: 14, resize: 'none', lineHeight: 1.5,
              fontFamily: 'inherit', maxHeight: 120, overflowY: 'auto',
              opacity: streaming ? 0.5 : 1,
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || streaming}
            style={{
              width: 36, height: 36, borderRadius: 8, border: 'none', cursor: 'pointer',
              background: input.trim() && !streaming ? primaryColor : 'rgba(255,255,255,0.1)',
              color: '#fff', fontSize: 16, display: 'flex', alignItems: 'center',
              justifyContent: 'center', transition: 'all 0.2s', flexShrink: 0,
              opacity: !input.trim() || streaming ? 0.5 : 1,
            }}
          >
            {streaming ? '⏳' : '↑'}
          </button>
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', marginTop: 6, textAlign: 'center' }}>
          {agent.memory_enabled ? '🧠 Memory enabled' : '🔇 No memory'} · Model: {agent.preferred_model || 'Auto'}
        </div>
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .streaming-cursor::after { content: '▋'; animation: pulse 0.7s infinite; }
      `}</style>
    </div>
  );
};

const MessageBubble: React.FC<{
  message: Message;
  primaryColor: string;
  onCopy: (c: string) => void;
}> = ({ message, primaryColor, onCopy }) => {
  const isUser = message.role === 'user';
  const isAgent = message.role === 'agent';

  return (
    <div style={{
      display: 'flex', flexDirection: isUser ? 'row-reverse' : 'row',
      gap: 10, alignItems: 'flex-start', animation: 'fadeIn 0.2s ease',
    }}>
      {isAgent && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%', flexShrink: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center', fontSize: 14,
          background: `${primaryColor}20`, border: `1px solid ${primaryColor}40`,
        }}>🤖</div>
      )}
      <div style={{ maxWidth: '75%', display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{
          padding: '12px 16px', borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          background: isUser
            ? `linear-gradient(135deg, ${primaryColor}, ${primaryColor}cc)`
            : 'rgba(255,255,255,0.06)',
          color: '#fff', fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          border: isAgent ? '1px solid rgba(255,255,255,0.06)' : 'none',
          position: 'relative',
        }}>
          {message.content || (message.streaming ? '' : '...')}
          {message.streaming && <span className="streaming-cursor" />}
          {message.error && (
            <div style={{ marginTop: 8, color: '#f87171', fontSize: 12 }}>⚠️ {message.error}</div>
          )}
        </div>

        {/* Plan summary */}
        {isAgent && message.plan && message.plan.step_count > 0 && (
          <div style={{
            padding: '6px 12px', borderRadius: 8, fontSize: 11,
            background: 'rgba(124,58,237,0.1)', color: '#a78bfa',
            border: '1px solid rgba(124,58,237,0.2)',
          }}>
            🧩 Plan: {message.plan.step_count} step(s) · {message.plan.thought?.slice(0, 60)}...
          </div>
        )}

        {/* Tool calls summary */}
        {isAgent && message.toolCalls && message.toolCalls.length > 0 && (
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {message.toolCalls.map((tc, i) => (
              <span key={i} style={{
                padding: '2px 8px', borderRadius: 20, fontSize: 10, fontWeight: 600,
                background: tc.success ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                color: tc.success ? '#4ade80' : '#f87171',
                border: `1px solid ${tc.success ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}>
                🔧 {tc.tool_name} {tc.success ? '✓' : '✗'}
              </span>
            ))}
          </div>
        )}

        {/* Metadata row */}
        {isAgent && !message.streaming && (message.latencyMs || message.tokens || message.evaluation) && (
          <div style={{ display: 'flex', gap: 8, fontSize: 10, color: 'rgba(255,255,255,0.3)', flexWrap: 'wrap' }}>
            {message.latencyMs && <span>⚡ {message.latencyMs}ms</span>}
            {message.tokens && <span>🔤 {message.tokens} tokens</span>}
            {message.evaluation?.overall_score !== undefined && (
              <span style={{ color: message.evaluation.overall_score >= 0.7 ? '#4ade80' : '#f59e0b' }}>
                📊 Score: {(message.evaluation.overall_score * 100).toFixed(0)}%
              </span>
            )}
            {message.reflection?.is_satisfactory === false && (
              <span style={{ color: '#f59e0b' }}>⚠️ Review recommended</span>
            )}
            <button
              onClick={() => onCopy(message.content)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'rgba(255,255,255,0.3)', fontSize: 10, padding: 0,
              }}
            >📋 Copy</button>
          </div>
        )}
      </div>
      {isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
          background: 'rgba(255,255,255,0.1)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', fontSize: 14,
        }}>👤</div>
      )}
    </div>
  );
};

export default StreamingChat;
