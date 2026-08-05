/**
 * Run Console — Execution Trace Viewer
 * ======================================
 * Sprint 7.1: Shows step-by-step agent execution timeline.
 * Displays: thought → tool calls → tool results → final answer.
 */
import React, { useState } from 'react';
import type { AgentRun, AgentLog } from '../types';

interface RunConsoleProps {
  run: AgentRun;
  logs: AgentLog[];
  onClose?: () => void;
}

const STEP_ICONS: Record<string, string> = {
  thought: '💭',
  tool_call: '🔧',
  tool_result: '📦',
  final_answer: '✅',
};

const STEP_COLORS: Record<string, string> = {
  thought: 'rgba(139,92,246,0.15)',
  tool_call: 'rgba(59,130,246,0.15)',
  tool_result: 'rgba(16,185,129,0.15)',
  final_answer: 'rgba(245,158,11,0.15)',
};

const STEP_BORDER: Record<string, string> = {
  thought: 'rgba(139,92,246,0.4)',
  tool_call: 'rgba(59,130,246,0.4)',
  tool_result: 'rgba(16,185,129,0.4)',
  final_answer: 'rgba(245,158,11,0.4)',
};

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: '#4ade80',
  FAILED: '#f87171',
  RUNNING: '#60a5fa',
  PENDING: '#94a3b8',
  CANCELLED: '#f59e0b',
};

export const RunConsole: React.FC<RunConsoleProps> = ({ run, logs, onClose }) => {
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const statusColor = STATUS_COLORS[run.status] || '#94a3b8';

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0a0a0f 0%, #111827 100%)',
      borderRadius: 16, overflow: 'hidden',
      border: '1px solid rgba(255,255,255,0.08)',
      fontFamily: "'Inter', -apple-system, sans-serif",
      color: '#e2e8f0', height: '100%', display: 'flex', flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%', background: statusColor,
          boxShadow: `0 0 8px ${statusColor}`,
        }} />
        <span style={{ fontWeight: 700, fontSize: 15 }}>Execution Console</span>
        <span style={{
          padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
          background: `${statusColor}20`, color: statusColor, border: `1px solid ${statusColor}40`,
        }}>{run.status}</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button
            onClick={() => setShowRaw(!showRaw)}
            style={{
              padding: '4px 12px', borderRadius: 8, fontSize: 11,
              background: showRaw ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.05)',
              color: showRaw ? '#a78bfa' : '#94a3b8', border: '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
            }}
          >
            {showRaw ? '📋 Raw' : '🔍 Structured'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, background: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}
            >✕ Close</button>
          )}
        </div>
      </div>

      {/* Run Metadata */}
      <div style={{
        display: 'flex', gap: 16, padding: '10px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.04)', flexWrap: 'wrap',
      }}>
        {[
          { label: 'Iterations', value: run.iterations },
          { label: 'Tokens', value: run.total_tokens.toLocaleString() },
          { label: 'Latency', value: run.latency_ms ? `${run.latency_ms}ms` : '—' },
          { label: 'Tool Calls', value: run.tool_calls?.length ?? 0 },
        ].map(({ label, value }) => (
          <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
            <span style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>{value}</span>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {showRaw ? (
          <pre style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: 0 }}>
            {JSON.stringify({ run, logs }, null, 2)}
          </pre>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {logs.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>
                No execution logs recorded.
              </div>
            ) : (
              logs.map((log, i) => {
                const icon = STEP_ICONS[log.step_type] || '📄';
                const bg = STEP_COLORS[log.step_type] || 'rgba(255,255,255,0.05)';
                const border = STEP_BORDER[log.step_type] || 'rgba(255,255,255,0.1)';
                const isExpanded = expandedLog === log.id;
                const hasMetadata = log.meta_data && Object.keys(log.meta_data).length > 0;

                return (
                  <div key={log.id} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    {/* Timeline line */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '50%', display: 'flex',
                        alignItems: 'center', justifyContent: 'center', fontSize: 14,
                        background: bg, border: `1px solid ${border}`,
                      }}>{icon}</div>
                      {i < logs.length - 1 && (
                        <div style={{ width: 1, flex: 1, minHeight: 8, background: 'rgba(255,255,255,0.06)', marginTop: 4 }} />
                      )}
                    </div>

                    <div
                      style={{
                        flex: 1, padding: '10px 14px', borderRadius: 10,
                        background: bg, border: `1px solid ${border}`,
                        cursor: hasMetadata ? 'pointer' : 'default',
                        transition: 'all 0.15s',
                        marginBottom: 4,
                      }}
                      onClick={() => hasMetadata && setExpandedLog(isExpanded ? null : log.id)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {log.step_type.replace(/_/g, ' ')}
                        </span>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          {log.level === 'ERROR' && (
                            <span style={{ fontSize: 10, color: '#f87171', fontWeight: 600 }}>ERROR</span>
                          )}
                          {hasMetadata && (
                            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>{isExpanded ? '▲' : '▼'}</span>
                          )}
                        </div>
                      </div>
                      <div style={{ fontSize: 13, color: '#e2e8f0', marginTop: 4, lineHeight: 1.5 }}>
                        {log.content}
                      </div>
                      {isExpanded && hasMetadata && (
                        <pre style={{
                          marginTop: 8, padding: '8px 12px', borderRadius: 8,
                          background: 'rgba(0,0,0,0.3)', fontSize: 11, color: '#94a3b8',
                          overflow: 'auto', maxHeight: 200, lineHeight: 1.5, margin: '8px 0 0',
                        }}>
                          {JSON.stringify(log.meta_data, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Final Output */}
        {run.agent_output && (
          <div style={{
            marginTop: 16, padding: '14px 16px', borderRadius: 12,
            background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)',
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#f59e0b', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ✅ Final Answer
            </div>
            <div style={{ fontSize: 13, color: '#e2e8f0', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {run.agent_output}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RunConsole;
