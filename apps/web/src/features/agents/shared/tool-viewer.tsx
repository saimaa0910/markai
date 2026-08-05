/**
 * Tool Viewer — Sprint 7.1
 * =========================
 * Shows tool executions from a run with params, output, latency.
 * Includes full Tool Registry browser.
 */
import React, { useState, useEffect } from 'react';
import type { ToolExecution, AgentToolInfo } from '../types';
import { fetchTools } from '../services';

interface ToolViewerProps {
  toolCalls?: ToolExecution[];
  showRegistry?: boolean;
  primaryColor?: string;
}

const TOOL_CATEGORY_COLORS: Record<string, string> = {
  knowledge: '#60a5fa',
  crm: '#34d399',
  campaign: '#f59e0b',
  web: '#a78bfa',
  workflow: '#fb923c',
  calculator: '#4ade80',
  email: '#e879f9',
  rest_api: '#38bdf8',
  analytics: '#fbbf24',
};

const getToolColor = (name: string): string => {
  for (const [key, color] of Object.entries(TOOL_CATEGORY_COLORS)) {
    if (name.includes(key)) return color;
  }
  return '#94a3b8';
};

export const ToolViewer: React.FC<ToolViewerProps> = ({
  toolCalls = [],
  showRegistry = false,
  primaryColor = '#7c3aed',
}) => {
  const [registryTools, setRegistryTools] = useState<AgentToolInfo[]>([]);
  const [activeTab, setActiveTab] = useState<'executions' | 'registry'>(
    showRegistry || toolCalls.length === 0 ? 'registry' : 'executions'
  );
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loadingRegistry, setLoadingRegistry] = useState(false);

  useEffect(() => {
    if (activeTab === 'registry' && registryTools.length === 0) {
      setLoadingRegistry(true);
      fetchTools().then(setRegistryTools).catch(console.error).finally(() => setLoadingRegistry(false));
    }
  }, [activeTab]);

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column', gap: 12,
      color: '#e2e8f0', fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <div style={{ display: 'flex', gap: 4 }}>
        {[
          { id: 'executions', label: `🔧 Executions (${toolCalls.length})` },
          { id: 'registry', label: `📋 Registry (${registryTools.length || '...'})` },
        ].map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            style={{
              padding: '6px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600,
              cursor: 'pointer', border: 'none',
              background: activeTab === id ? `${primaryColor}25` : 'rgba(255,255,255,0.05)',
              color: activeTab === id ? primaryColor : 'rgba(255,255,255,0.4)',
              borderBottom: `2px solid ${activeTab === id ? primaryColor : 'transparent'}`,
              transition: 'all 0.15s',
            }}
          >{label}</button>
        ))}
      </div>

      {/* Tool Executions Tab */}
      {activeTab === 'executions' && (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {toolCalls.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 60, fontSize: 13 }}>
              No tool calls in this run.
            </div>
          ) : (
            toolCalls.map((tc, i) => {
              const color = getToolColor(tc.tool_name);
              const isExpanded = expanded === i;
              return (
                <div
                  key={i}
                  onClick={() => setExpanded(isExpanded ? null : i)}
                  style={{
                    padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                    background: 'rgba(255,255,255,0.04)',
                    border: `1px solid ${isExpanded ? color + '40' : 'rgba(255,255,255,0.06)'}`,
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center',
                        justifyContent: 'center', background: `${color}20`, border: `1px solid ${color}40`, fontSize: 14,
                      }}>🔧</div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{tc.tool_name}</div>
                        {tc.step_id && (
                          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>Step: {tc.step_id}</div>
                        )}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {tc.latency_ms && (
                        <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>⚡ {tc.latency_ms}ms</span>
                      )}
                      <span style={{
                        padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                        background: tc.success ? 'rgba(74,222,128,0.15)' : 'rgba(248,113,113,0.15)',
                        color: tc.success ? '#4ade80' : '#f87171',
                        border: `1px solid ${tc.success ? 'rgba(74,222,128,0.3)' : 'rgba(248,113,113,0.3)'}`,
                      }}>{tc.success ? '✓ OK' : '✗ FAIL'}</span>
                      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>{isExpanded ? '▲' : '▼'}</span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {tc.tool_params && Object.keys(tc.tool_params).length > 0 && (
                        <div>
                          <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>Input Params</div>
                          <pre style={{
                            padding: '8px 12px', borderRadius: 8, background: 'rgba(0,0,0,0.3)',
                            fontSize: 11, color: '#94a3b8', overflow: 'auto', maxHeight: 120, margin: 0, lineHeight: 1.5,
                          }}>{JSON.stringify(tc.tool_params, null, 2)}</pre>
                        </div>
                      )}
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                          {tc.success ? 'Output' : 'Error'}
                        </div>
                        <pre style={{
                          padding: '8px 12px', borderRadius: 8,
                          background: tc.success ? 'rgba(74,222,128,0.05)' : 'rgba(248,113,113,0.05)',
                          fontSize: 11, color: tc.success ? '#86efac' : '#fca5a5',
                          overflow: 'auto', maxHeight: 150, margin: 0, lineHeight: 1.5,
                          border: `1px solid ${tc.success ? 'rgba(74,222,128,0.15)' : 'rgba(248,113,113,0.15)'}`,
                        }}>
                          {tc.success
                            ? JSON.stringify(tc.output, null, 2)
                            : tc.error || 'Unknown error'}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Registry Tab */}
      {activeTab === 'registry' && (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {loadingRegistry ? (
            <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>Loading registry...</div>
          ) : registryTools.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>No tools registered.</div>
          ) : (
            registryTools.map(tool => {
              const color = getToolColor(tool.name);
              return (
                <div key={tool.name} style={{
                  padding: '12px 14px', borderRadius: 10,
                  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 6 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center',
                      justifyContent: 'center', background: `${color}20`, border: `1px solid ${color}40`, fontSize: 14,
                    }}>🔧</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>{tool.name}</div>
                      {tool.category && (
                        <span style={{ fontSize: 10, color, fontWeight: 600 }}>{tool.category}</span>
                      )}
                    </div>
                  </div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 1.5 }}>
                    {tool.description}
                  </div>
                  {tool.parameters_schema?.properties && (
                    <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {Object.keys(tool.parameters_schema.properties).map(param => (
                        <span key={param} style={{
                          padding: '1px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                          background: `${color}10`, color: color, border: `1px solid ${color}25`,
                        }}>
                          {tool.parameters_schema?.required?.includes(param) ? '*' : ''}{param}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default ToolViewer;
