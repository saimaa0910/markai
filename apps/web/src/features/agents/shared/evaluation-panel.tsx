/**
 * Evaluation Panel — Sprint 7.1
 * ==============================
 * Visual dashboard for agent run evaluation scores.
 * Shows radar chart (SVG), score cards, and critique text.
 */
import React, { useState, useEffect } from 'react';
import type { AgentEvaluation } from '../types';
import { fetchEvaluations } from '../services';

interface EvaluationPanelProps {
  agentId: string;
  primaryColor?: string;
}

const SCORE_DIMS = [
  { key: 'accuracy_score', label: 'Accuracy', icon: '🎯' },
  { key: 'brand_alignment_score', label: 'Brand', icon: '🏷️' },
  { key: 'safety_score', label: 'Safety', icon: '🛡️' },
  { key: 'completeness_score', label: 'Complete', icon: '✅' },
  { key: 'reasoning_score', label: 'Reasoning', icon: '🧩' },
  { key: 'tool_usage_score', label: 'Tools', icon: '🔧' },
  { key: 'knowledge_usage_score', label: 'Knowledge', icon: '📚' },
  { key: 'latency_score', label: 'Speed', icon: '⚡' },
];

function RadarChart({ scores, primaryColor }: { scores: Record<string, number>; primaryColor: string }) {
  const size = 200;
  const center = size / 2;
  const radius = 80;
  const dims = SCORE_DIMS;
  const n = dims.length;

  const points = dims.map((dim, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const val = scores[dim.key] ?? 0;
    const r = val * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      lx: center + (radius + 18) * Math.cos(angle),
      ly: center + (radius + 18) * Math.sin(angle),
      label: dim.label,
      icon: dim.icon,
    };
  });

  const polyPoints = points.map(p => `${p.x},${p.y}`).join(' ');

  // Grid lines at 25%, 50%, 75%, 100%
  const gridLevels = [0.25, 0.5, 0.75, 1.0];
  const gridPolygons = gridLevels.map(level => {
    const pts = dims.map((_, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2;
      const r = level * radius;
      return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
    });
    return pts.join(' ');
  });

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ overflow: 'visible' }}>
      {/* Grid */}
      {gridPolygons.map((pts, i) => (
        <polygon key={i} points={pts} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={1} />
      ))}
      {/* Axes */}
      {dims.map((_, i) => {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2;
        return (
          <line
            key={i}
            x1={center} y1={center}
            x2={center + radius * Math.cos(angle)}
            y2={center + radius * Math.sin(angle)}
            stroke="rgba(255,255,255,0.08)" strokeWidth={1}
          />
        );
      })}
      {/* Score polygon */}
      <polygon
        points={polyPoints}
        fill={`${primaryColor}20`}
        stroke={primaryColor}
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {/* Dots */}
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill={primaryColor} />
      ))}
      {/* Labels */}
      {points.map((p, i) => (
        <text
          key={i}
          x={p.lx} y={p.ly}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
        >
          {p.icon}
        </text>
      ))}
    </svg>
  );
}

function ScoreBar({ label, score, icon, color }: { label: string; score: number | null; icon: string; color: string }) {
  const pct = score !== null ? Math.round(score * 100) : null;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 20, textAlign: 'center', fontSize: 13 }}>{icon}</span>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', width: 72, flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 2, transition: 'width 0.6s ease',
          width: pct !== null ? `${pct}%` : '0%',
          background: pct !== null && pct >= 70 ? '#4ade80' : pct !== null && pct >= 50 ? '#f59e0b' : '#f87171',
        }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 700, color: '#e2e8f0', width: 32, textAlign: 'right' }}>
        {pct !== null ? `${pct}%` : '—'}
      </span>
    </div>
  );
}

export const EvaluationPanel: React.FC<EvaluationPanelProps> = ({ agentId, primaryColor = '#7c3aed' }) => {
  const [evaluations, setEvaluations] = useState<AgentEvaluation[]>([]);
  const [selected, setSelected] = useState<AgentEvaluation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvaluations(agentId, 20)
      .then(data => {
        setEvaluations(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [agentId]);

  const avgScore = evaluations.length > 0
    ? evaluations.reduce((s, e) => s + (e.overall_score ?? 0), 0) / evaluations.length
    : null;

  const radarScores = selected
    ? Object.fromEntries(SCORE_DIMS.map(d => [d.key, (selected as any)[d.key] ?? 0]))
    : {};

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column', gap: 16,
      color: '#e2e8f0', fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Summary row */}
      <div style={{ display: 'flex', gap: 12 }}>
        {[
          { label: 'Total Evals', value: evaluations.length },
          {
            label: 'Avg Score',
            value: avgScore !== null ? `${(avgScore * 100).toFixed(0)}%` : '—',
            color: avgScore !== null && avgScore >= 0.7 ? '#4ade80' : '#f59e0b',
          },
          {
            label: 'Pass Rate',
            value: evaluations.length
              ? `${Math.round(evaluations.filter(e => e.is_satisfactory).length / evaluations.length * 100)}%`
              : '—',
            color: '#34d399',
          },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            flex: 1, padding: '12px 14px', borderRadius: 12,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: color || '#e2e8f0' }}>{value}</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>Loading evaluations...</div>
      ) : evaluations.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 60, fontSize: 13 }}>
          No evaluations yet.<br />Run the agent with reflection + evaluation enabled to see quality scores here.
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', gap: 16, overflow: 'hidden' }}>
          {/* Left: list */}
          <div style={{ width: 200, flexShrink: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
            {evaluations.map((ev, i) => (
              <div
                key={ev.id}
                onClick={() => setSelected(ev)}
                style={{
                  padding: '8px 10px', borderRadius: 8, cursor: 'pointer',
                  background: selected?.id === ev.id ? `${primaryColor}20` : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${selected?.id === ev.id ? `${primaryColor}40` : 'rgba(255,255,255,0.06)'}`,
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, color: '#e2e8f0' }}>Run {i + 1}</span>
                  <span style={{
                    fontSize: 12, fontWeight: 800,
                    color: (ev.overall_score ?? 0) >= 0.7 ? '#4ade80' : (ev.overall_score ?? 0) >= 0.5 ? '#f59e0b' : '#f87171',
                  }}>{ev.overall_score !== null ? `${((ev.overall_score ?? 0) * 100).toFixed(0)}%` : '—'}</span>
                </div>
                <div style={{ fontSize: 10, color: ev.is_satisfactory ? '#4ade80' : '#f87171', marginTop: 2, fontWeight: 600 }}>
                  {ev.is_satisfactory ? '✓ Pass' : '✗ Review'}
                </div>
              </div>
            ))}
          </div>

          {/* Right: detail */}
          {selected && (
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Radar + Score bars */}
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <RadarChart scores={radarScores} primaryColor={primaryColor} />
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {SCORE_DIMS.map(dim => (
                    <ScoreBar
                      key={dim.key}
                      label={dim.label}
                      score={(selected as any)[dim.key]}
                      icon={dim.icon}
                      color={primaryColor}
                    />
                  ))}
                </div>
              </div>

              {/* Overall score badge */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 14px', borderRadius: 12,
                background: selected.is_satisfactory ? 'rgba(74,222,128,0.08)' : 'rgba(248,113,113,0.08)',
                border: `1px solid ${selected.is_satisfactory ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
              }}>
                <span style={{
                  fontSize: 32, fontWeight: 900,
                  color: (selected.overall_score ?? 0) >= 0.7 ? '#4ade80' : (selected.overall_score ?? 0) >= 0.5 ? '#f59e0b' : '#f87171',
                }}>
                  {selected.overall_score !== null ? `${((selected.overall_score ?? 0) * 100).toFixed(0)}%` : '—'}
                </span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>
                    {selected.is_satisfactory ? '✓ Output Satisfactory' : '⚠️ Review Recommended'}
                  </div>
                  {selected.confidence !== null && (
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>
                      Confidence: {((selected.confidence ?? 0) * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              </div>

              {/* Critique */}
              {selected.critique && (
                <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                    Critique
                  </div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, fontStyle: 'italic' }}>
                    "{selected.critique}"
                  </div>
                </div>
              )}

              {/* Suggested Edits */}
              {selected.suggested_edits && (
                <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.15)' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                    💡 Suggested Edits
                  </div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
                    {selected.suggested_edits}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvaluationPanel;
