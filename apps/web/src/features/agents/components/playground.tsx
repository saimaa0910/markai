/**
 * Agent Playground — Sprint 7.1
 * ==============================
 * Full-screen split-pane UI:
 *   Left  = Agent Config panel + session list
 *   Right = Streaming Chat panel + Run Console (tabbed)
 */
import React, { useState, useEffect } from 'react';
import type { AgentDefinition, AgentSession, AgentRun, AgentLog } from '../types';
import { fetchAgent, fetchSessions, fetchRuns, fetchRunLogs, createSession } from '../services';
import { StreamingChat } from './streaming-chat';
import { RunConsole } from './run-console';

interface PlaygroundProps {
  agentId: string;
}

type RightTab = 'chat' | 'console' | 'memory' | 'evaluation';

export const AgentPlayground: React.FC<PlaygroundProps> = ({ agentId }) => {
  const [agent, setAgent] = useState<AgentDefinition | null>(null);
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [activeSession, setActiveSession] = useState<AgentSession | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [runLogs, setRunLogs] = useState<AgentLog[]>([]);
  const [rightTab, setRightTab] = useState<RightTab>('chat');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [agentData, sessionData] = await Promise.all([
          fetchAgent(agentId),
          fetchSessions(),
        ]);
        setAgent(agentData);
        const agentSessions = sessionData.filter(s => s.agent_id === agentId && s.is_active);
        setSessions(agentSessions);
        if (agentSessions.length > 0) {
          setActiveSession(agentSessions[0]);
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [agentId]);

  useEffect(() => {
    if (!activeSession) return;
    fetchRuns(activeSession.id).then(setRuns).catch(console.error);
  }, [activeSession]);

  useEffect(() => {
    if (!selectedRun) return;
    fetchRunLogs(selectedRun.id).then(setRunLogs).catch(console.error);
  }, [selectedRun]);

  const handleNewSession = async () => {
    if (!agent) return;
    try {
      const session = await createSession(agent.id, `Session ${Date.now()}`);
      setSessions(prev => [session, ...prev]);
      setActiveSession(session);
      setRuns([]);
    } catch (e: any) {
      console.error('Failed to create session:', e);
    }
  };

  const agentColor = agent?.avatar_color || 'violet';
  const colorMap: Record<string, string> = {
    violet: '#7c3aed', blue: '#2563eb', emerald: '#059669',
    amber: '#d97706', rose: '#e11d48', cyan: '#0891b2',
  };
  const primaryColor = colorMap[agentColor] || '#7c3aed';

  if (loading) {
    return (
      <div style={{
        height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f0f1a, #1a1a2e)',
        color: 'rgba(255,255,255,0.4)', fontSize: 14,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
          Loading Agent Playground...
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div style={{
        height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f0f1a, #1a1a2e)', color: '#f87171', fontSize: 14,
      }}>
        ⚠️ {error || 'Agent not found'}
      </div>
    );
  }

  const TABS: { id: RightTab; label: string; icon: string }[] = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'console', label: 'Console', icon: '🔍' },
    { id: 'memory', label: 'Memory', icon: '🧠' },
    { id: 'evaluation', label: 'Eval', icon: '📊' },
  ];

  return (
    <div style={{
      display: 'flex', height: '100%', width: '100%',
      background: 'linear-gradient(135deg, #0a0a0f 0%, #111827 100%)',
      fontFamily: "'Inter', -apple-system, sans-serif",
      overflow: 'hidden',
    }}>
      {/* LEFT PANEL — Config + Sessions */}
      <div style={{
        width: 280, flexShrink: 0,
        borderRight: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        background: 'rgba(255,255,255,0.01)',
      }}>
        {/* Agent Card */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 20,
              background: `linear-gradient(135deg, ${primaryColor}30, ${primaryColor}15)`,
              border: `2px solid ${primaryColor}50`,
            }}>
              {agent.avatar || '🤖'}
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: 14 }}>{agent.name}</div>
              <div style={{
                fontSize: 11, color: primaryColor, fontWeight: 600,
                background: `${primaryColor}15`, padding: '1px 8px',
                borderRadius: 20, marginTop: 2, display: 'inline-block',
              }}>{agent.agent_type}</div>
            </div>
          </div>
          {agent.description && (
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', lineHeight: 1.5 }}>
              {agent.description}
            </div>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
            {[
              { icon: '🌡️', label: `Temp: ${agent.temperature}` },
              { icon: '🔄', label: `Iter: ${agent.max_iterations}` },
              { icon: '🧠', label: agent.memory_enabled ? 'Memory ON' : 'Memory OFF' },
            ].map(({ icon, label }) => (
              <span key={label} style={{
                padding: '3px 8px', borderRadius: 8, fontSize: 10, fontWeight: 600,
                background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)',
                border: '1px solid rgba(255,255,255,0.08)',
              }}>{icon} {label}</span>
            ))}
          </div>

          {/* Allowed Tools */}
          {agent.allowed_tools?.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tools</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {agent.allowed_tools.map(t => (
                  <span key={t} style={{
                    padding: '2px 6px', borderRadius: 6, fontSize: 10,
                    background: `${primaryColor}15`, color: primaryColor,
                    border: `1px solid ${primaryColor}30`,
                  }}>🔧 {t.replace(/_tool$/, '')}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sessions */}
        <div style={{ flex: 1, overflow: 'auto', padding: '12px 8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 8px', marginBottom: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sessions
            </span>
            <button
              onClick={handleNewSession}
              style={{
                padding: '4px 10px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                background: `${primaryColor}20`, color: primaryColor,
                border: `1px solid ${primaryColor}40`, cursor: 'pointer',
              }}
            >+ New</button>
          </div>
          {sessions.length === 0 ? (
            <div style={{ padding: '12px 8px', fontSize: 12, color: 'rgba(255,255,255,0.25)', textAlign: 'center' }}>
              No sessions yet
            </div>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                onClick={() => setActiveSession(s)}
                style={{
                  padding: '8px 12px', borderRadius: 10, cursor: 'pointer', marginBottom: 4,
                  background: activeSession?.id === s.id ? `${primaryColor}20` : 'transparent',
                  border: `1px solid ${activeSession?.id === s.id ? `${primaryColor}40` : 'transparent'}`,
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 13, color: '#e2e8f0', fontWeight: activeSession?.id === s.id ? 600 : 400 }}>
                  {s.title}
                </div>
              </div>
            ))
          )}

          {/* Recent Runs */}
          {runs.length > 0 && (
            <div style={{ marginTop: 16, padding: '0 8px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Recent Runs
              </div>
              {runs.slice(0, 5).map(r => (
                <div
                  key={r.id}
                  onClick={() => { setSelectedRun(r); setRightTab('console'); }}
                  style={{
                    padding: '6px 8px', borderRadius: 8, cursor: 'pointer', marginBottom: 3,
                    background: selectedRun?.id === r.id ? 'rgba(255,255,255,0.06)' : 'transparent',
                    border: '1px solid transparent',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 140 }}>
                      {r.user_input}
                    </span>
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: '1px 6px', borderRadius: 6,
                      color: r.status === 'COMPLETED' ? '#4ade80' : r.status === 'FAILED' ? '#f87171' : '#94a3b8',
                      background: r.status === 'COMPLETED' ? 'rgba(74,222,128,0.1)' : r.status === 'FAILED' ? 'rgba(248,113,113,0.1)' : 'rgba(148,163,184,0.1)',
                    }}>{r.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT PANEL — Tabs */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Tab Bar */}
        <div style={{
          display: 'flex', gap: 4, padding: '12px 16px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          background: 'rgba(255,255,255,0.01)',
        }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setRightTab(tab.id)}
              style={{
                padding: '6px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                cursor: 'pointer', border: 'none', transition: 'all 0.15s',
                background: rightTab === tab.id ? `${primaryColor}25` : 'transparent',
                color: rightTab === tab.id ? primaryColor : 'rgba(255,255,255,0.4)',
                borderBottom: rightTab === tab.id ? `2px solid ${primaryColor}` : '2px solid transparent',
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
          {activeSession && (
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'rgba(255,255,255,0.3)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
              {activeSession.title}
            </div>
          )}
        </div>

        {/* Tab Content */}
        <div style={{ flex: 1, overflow: 'hidden', padding: rightTab === 'chat' ? 0 : 16 }}>
          {rightTab === 'chat' && activeSession && (
            <StreamingChat agent={agent} sessionId={activeSession.id} />
          )}
          {rightTab === 'chat' && !activeSession && (
            <div style={{
              height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', gap: 16, color: 'rgba(255,255,255,0.3)',
            }}>
              <div style={{ fontSize: 48 }}>💬</div>
              <div>Create a session to start chatting</div>
              <button
                onClick={handleNewSession}
                style={{
                  padding: '10px 24px', borderRadius: 10, fontSize: 14, fontWeight: 600,
                  background: `linear-gradient(135deg, ${primaryColor}, ${primaryColor}cc)`,
                  color: '#fff', border: 'none', cursor: 'pointer',
                }}
              >+ New Session</button>
            </div>
          )}
          {rightTab === 'console' && (
            selectedRun ? (
              <RunConsole run={selectedRun} logs={runLogs} />
            ) : (
              <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>
                Select a run from the sidebar to view the execution console.
              </div>
            )
          )}
          {rightTab === 'memory' && activeSession && (
            <MemoryPlaceholder sessionId={activeSession.id} primaryColor={primaryColor} />
          )}
          {rightTab === 'evaluation' && (
            <EvalPlaceholder agentId={agent.id} primaryColor={primaryColor} />
          )}
        </div>
      </div>
    </div>
  );
};

// Inline lightweight panels for memory / eval (full components available separately)
const MemoryPlaceholder: React.FC<{ sessionId: string; primaryColor: string }> = ({ sessionId, primaryColor }) => {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    import('../services').then(({ fetchSessionMemory }) => {
      fetchSessionMemory(sessionId).then(setItems).catch(console.error);
    });
  }, [sessionId]);
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>🧠 Session Memory ({items.length})</div>
      {items.length === 0 ? (
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13, textAlign: 'center', padding: 40 }}>No memory items stored yet.</div>
      ) : (
        items.map((m, i) => (
          <div key={i} style={{
            padding: '10px 14px', borderRadius: 10, marginBottom: 6,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: primaryColor }}>{m.memory_key}</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>{m.memory_type} · ⭐ {m.importance}</span>
            </div>
            <div style={{ fontSize: 12, color: '#e2e8f0', lineHeight: 1.5 }}>{m.memory_value}</div>
          </div>
        ))
      )}
    </div>
  );
};

const EvalPlaceholder: React.FC<{ agentId: string; primaryColor: string }> = ({ agentId, primaryColor }) => {
  const [evals, setEvals] = useState<any[]>([]);
  useEffect(() => {
    import('../services').then(({ fetchEvaluations }) => {
      fetchEvaluations(agentId).then(setEvals).catch(console.error);
    });
  }, [agentId]);
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>📊 Evaluations ({evals.length})</div>
      {evals.length === 0 ? (
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13, textAlign: 'center', padding: 40 }}>No evaluations yet. Run the agent to see quality scores.</div>
      ) : (
        evals.slice(0, 5).map((ev, i) => (
          <div key={i} style={{
            padding: '12px 14px', borderRadius: 12, marginBottom: 8,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{
                fontSize: 18, fontWeight: 800,
                color: (ev.overall_score ?? 0) >= 0.7 ? '#4ade80' : (ev.overall_score ?? 0) >= 0.5 ? '#f59e0b' : '#f87171',
              }}>
                {ev.overall_score !== null ? `${((ev.overall_score ?? 0) * 100).toFixed(0)}%` : '—'}
              </span>
              <span style={{ fontSize: 11, color: ev.is_satisfactory ? '#4ade80' : '#f87171', fontWeight: 600 }}>
                {ev.is_satisfactory ? '✓ Pass' : '✗ Review'}
              </span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {[
                ['Accuracy', ev.accuracy_score],
                ['Brand', ev.brand_alignment_score],
                ['Safety', ev.safety_score],
                ['Complete', ev.completeness_score],
              ].map(([label, score]: any) => score !== null && (
                <span key={label} style={{
                  padding: '2px 8px', borderRadius: 20, fontSize: 10, fontWeight: 600,
                  background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}>{label}: {((score ?? 0) * 100).toFixed(0)}%</span>
              ))}
            </div>
            {ev.critique && (
              <div style={{ marginTop: 8, fontSize: 11, color: 'rgba(255,255,255,0.4)', fontStyle: 'italic', lineHeight: 1.5 }}>
                "{ev.critique}"
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default AgentPlayground;
