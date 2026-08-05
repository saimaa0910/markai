/**
 * Cost Dashboard — Sprint 7.1
 * ============================
 * Per-agent cost summary: tokens consumed, USD cost, latency trends, provider breakdown.
 */
import React, { useState, useEffect } from 'react';
import { fetchAgentAnalytics } from '../services';

interface CostDashboardProps {
  agentId: string;
  primaryColor?: string;
}

export const CostDashboard: React.FC<CostDashboardProps> = ({ agentId, primaryColor = '#7c3aed' }) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgentAnalytics(agentId)
      .then(setAnalytics)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [agentId]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 60, fontSize: 13 }}>
        Loading analytics...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 60, fontSize: 13 }}>
        No analytics data available.
      </div>
    );
  }

  const metrics = [
    { label: 'Total Runs', value: analytics.total_executions, icon: '🔄', color: primaryColor },
    { label: 'Success Rate', value: `${analytics.success_rate}%`, icon: '✅', color: '#4ade80' },
    { label: 'Failed', value: analytics.failed_executions, icon: '❌', color: '#f87171' },
    { label: 'Tokens', value: (analytics.total_tokens_consumed || 0).toLocaleString(), icon: '🔤', color: '#60a5fa' },
    { label: 'Avg Latency', value: `${analytics.average_latency_ms}ms`, icon: '⚡', color: '#f59e0b' },
    { label: 'Total Cost', value: `$${analytics.total_cost_usd?.toFixed(4) || '0.0000'}`, icon: '💰', color: '#34d399' },
  ];

  const toolUsage = analytics.tool_usage || {};

  return (
    <div style={{
      color: '#e2e8f0', fontFamily: "'Inter', -apple-system, sans-serif",
      display: 'flex', flexDirection: 'column', gap: 16,
    }}>
      <div style={{ fontSize: 16, fontWeight: 800, color: '#fff' }}>💰 Cost & Performance</div>

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {metrics.map(m => (
          <div key={m.label} style={{
            padding: '14px 14px', borderRadius: 12,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
          }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>{m.icon}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: m.color }}>{m.value}</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{m.label}</div>
          </div>
        ))}
      </div>

      {/* Tool Usage */}
      {Object.keys(toolUsage).length > 0 && (
        <div style={{
          padding: '14px', borderRadius: 12,
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.5)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            🔧 Tool Usage
          </div>
          {Object.entries(toolUsage).map(([tool, count]: any) => {
            const maxCount = Math.max(...Object.values(toolUsage) as number[]);
            const pct = Math.round((count / maxCount) * 100);
            return (
              <div key={tool} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', width: 140, flexShrink: 0 }}>
                  {tool.replace(/_tool$/, '')}
                </span>
                <div style={{ flex: 1, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
                  <div style={{
                    width: `${pct}%`, height: '100%', borderRadius: 3,
                    background: `linear-gradient(90deg, ${primaryColor}, ${primaryColor}80)`,
                  }} />
                </div>
                <span style={{ fontSize: 12, color: primaryColor, fontWeight: 700, width: 24, textAlign: 'right' }}>{count}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Model info */}
      <div style={{
        padding: '12px 14px', borderRadius: 12, display: 'flex', gap: 20,
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Model</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{analytics.preferred_model}</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Provider</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{analytics.preferred_provider}</div>
        </div>
      </div>
    </div>
  );
};

export default CostDashboard;
