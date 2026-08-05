/**
 * Memory Viewer — Sprint 7.1
 * ============================
 * Browse all agent memory tiers for a session:
 * SHORT_TERM | LONG_TERM | EPISODIC | SEMANTIC
 */
import React, { useState, useEffect, useCallback } from 'react';
import type { AgentMemoryItem, MemoryType } from '../types';
import { fetchSessionMemory, writeSessionMemory } from '../services';

interface MemoryViewerProps {
  sessionId: string;
  agentId?: string;
  primaryColor?: string;
}

const MEMORY_COLORS: Record<MemoryType, string> = {
  SHORT_TERM: '#60a5fa',
  LONG_TERM: '#a78bfa',
  EPISODIC: '#f59e0b',
  SEMANTIC: '#34d399',
};

const MEMORY_ICONS: Record<MemoryType, string> = {
  SHORT_TERM: '⚡',
  LONG_TERM: '🧠',
  EPISODIC: '📖',
  SEMANTIC: '🌐',
};

export const MemoryViewer: React.FC<MemoryViewerProps> = ({
  sessionId,
  primaryColor = '#7c3aed',
}) => {
  const [items, setItems] = useState<AgentMemoryItem[]>([]);
  const [filter, setFilter] = useState<MemoryType | 'ALL'>('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [writing, setWriting] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchSessionMemory(sessionId, 50);
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load]);

  const handleWrite = async () => {
    if (!newKey.trim() || !newValue.trim()) return;
    setWriting(true);
    try {
      await writeSessionMemory(sessionId, newKey, newValue);
      setNewKey('');
      setNewValue('');
      await load();
    } catch (e) {
      console.error(e);
    } finally {
      setWriting(false);
    }
  };

  const filtered = items.filter(m => {
    const matchesType = filter === 'ALL' || m.memory_type === filter;
    const matchesSearch = !search || m.memory_key.includes(search) || m.memory_value.includes(search);
    return matchesType && matchesSearch;
  });

  const byType = items.reduce((acc, m) => {
    acc[m.memory_type] = (acc[m.memory_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column', gap: 12,
      color: '#e2e8f0', fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#fff' }}>🧠 Memory Store</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>{items.length} items stored</div>
        </div>
        <button
          onClick={load}
          style={{
            padding: '6px 14px', borderRadius: 8, fontSize: 12, background: 'rgba(255,255,255,0.05)',
            color: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer',
          }}
        >↻ Refresh</button>
      </div>

      {/* Type summary pills */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {(['ALL', 'SHORT_TERM', 'LONG_TERM', 'EPISODIC', 'SEMANTIC'] as const).map(type => {
          const count = type === 'ALL' ? items.length : byType[type] || 0;
          const color = type === 'ALL' ? primaryColor : MEMORY_COLORS[type];
          return (
            <button
              key={type}
              onClick={() => setFilter(type)}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                cursor: 'pointer', border: `1px solid ${filter === type ? color : 'rgba(255,255,255,0.1)'}`,
                background: filter === type ? `${color}20` : 'transparent',
                color: filter === type ? color : 'rgba(255,255,255,0.4)', transition: 'all 0.15s',
              }}
            >
              {type === 'ALL' ? '🌐' : MEMORY_ICONS[type as MemoryType]} {type.replace(/_/g, ' ')} ({count})
            </button>
          );
        })}
      </div>

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Search memory keys or values..."
        style={{
          padding: '8px 14px', borderRadius: 8, fontSize: 13, width: '100%', boxSizing: 'border-box',
          background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
          color: '#e2e8f0', outline: 'none',
        }}
      />

      {/* Memory List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>Loading memory...</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)', padding: 40, fontSize: 13 }}>
            {items.length === 0 ? 'No memory stored yet. Run the agent to build up memory.' : 'No items match your filter.'}
          </div>
        ) : (
          filtered.map(m => {
            const color = MEMORY_COLORS[m.memory_type];
            const icon = MEMORY_ICONS[m.memory_type];
            const importancePct = Math.round(m.importance * 100);
            return (
              <div key={m.id} style={{
                padding: '10px 14px', borderRadius: 10,
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                transition: 'border-color 0.15s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{
                      padding: '1px 8px', borderRadius: 20, fontSize: 10, fontWeight: 700,
                      background: `${color}15`, color, border: `1px solid ${color}30`,
                    }}>{icon} {m.memory_type.replace(/_/g, ' ')}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>{m.memory_key}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 8, fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>
                    <span title="Importance">⭐ {importancePct}%</span>
                    <span title="Access count">👁 {m.access_count}x</span>
                  </div>
                </div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', lineHeight: 1.6, marginTop: 2 }}>
                  {m.memory_value}
                </div>
                {/* Importance bar */}
                <div style={{ marginTop: 6, height: 2, background: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
                  <div style={{ width: `${importancePct}%`, height: '100%', background: color, borderRadius: 1 }} />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Write Memory */}
      <div style={{
        padding: 14, borderRadius: 12, background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Write Memory
        </div>
        <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
          <input
            type="text"
            value={newKey}
            onChange={e => setNewKey(e.target.value)}
            placeholder="Memory key"
            style={{
              padding: '6px 10px', borderRadius: 6, fontSize: 12, background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0', outline: 'none',
            }}
          />
          <textarea
            value={newValue}
            onChange={e => setNewValue(e.target.value)}
            placeholder="Memory value"
            rows={2}
            style={{
              padding: '6px 10px', borderRadius: 6, fontSize: 12, background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0', outline: 'none',
              fontFamily: 'inherit', resize: 'none',
            }}
          />
          <button
            onClick={handleWrite}
            disabled={writing || !newKey.trim() || !newValue.trim()}
            style={{
              padding: '7px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600,
              background: newKey && newValue ? `${primaryColor}` : 'rgba(255,255,255,0.05)',
              color: '#fff', border: 'none', cursor: 'pointer',
              opacity: !newKey || !newValue ? 0.5 : 1,
            }}
          >{writing ? 'Saving...' : '💾 Save to Memory'}</button>
        </div>
      </div>
    </div>
  );
};

export default MemoryViewer;
