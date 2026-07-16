'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Play, Bot, Code, FolderSearch, Users, Megaphone, 
  BarChart2, Split, Clock, Activity, Mail, Trash2, 
  Plus, Settings, ZoomIn, ZoomOut, Maximize, Undo2, 
  Redo2, Eye, HelpCircle, Save, Calendar, CheckSquare, 
  MessageSquare, Compass, ShieldAlert, CheckCircle2 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
export interface NodeData {
  id: string;
  type: string;
  name: string;
  x: number;
  y: number;
  config: Record<string, any>;
  status?: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
}

export interface Connection {
  fromId: string;
  toId: string;
}

// Node types visual config
export const NODE_TYPES: Record<string, { label: string; icon: any; color: string; desc: string }> = {
  trigger: { label: 'Workflow Trigger', icon: Play, color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400', desc: 'Schedules, webhooks or CRM event hooks.' },
  agent: { label: 'AI Agent Call', icon: Bot, color: 'bg-violet-500/10 border-violet-500/30 text-violet-400', desc: 'Dispatch query to custom agents.' },
  prompt: { label: 'Prompt Template', icon: Code, color: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400', desc: 'Bind workspace prompt string.' },
  rag: { label: 'Knowledge Sync', icon: FolderSearch, color: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400', desc: 'Semantic retrieval across databases.' },
  crm: { label: 'CRM Enrichment', icon: Users, color: 'bg-blue-500/10 border-blue-500/30 text-blue-400', desc: 'Lookup or update pipeline contact leads.' },
  campaign: { label: 'Campaign Ads', icon: Megaphone, color: 'bg-amber-500/10 border-amber-500/30 text-amber-400', desc: 'Publish creative variations to Google.' },
  condition: { label: 'Branch Logic', icon: Split, color: 'bg-rose-500/10 border-rose-500/30 text-rose-400', desc: 'Branch steps depending on properties.' },
  delay: { label: 'Time Delay', icon: Clock, color: 'bg-neutral-800 border-white/10 text-neutral-400', desc: 'Pause pipeline execution for set time.' },
  slack: { label: 'Slack Alert', icon: MessageSquare, color: 'bg-violet-600/20 border-violet-500/30 text-violet-300', desc: 'Dispatch chat notifications to teams.' },
  email: { label: 'Email Outreach', icon: Mail, color: 'bg-teal-500/10 border-teal-500/30 text-teal-400', desc: 'Deliver custom cohort sequences.' },
};

// ─────────────────────────────────────────────────────────────────────────────
// Component: WorkflowCanvas
// ─────────────────────────────────────────────────────────────────────────────
interface WorkflowCanvasProps {
  nodes: NodeData[];
  connections: Connection[];
  onNodesChange: (nodes: NodeData[]) => void;
  onConnectionsChange: (conns: Connection[]) => void;
  selectedNodeId: string | null;
  onSelectNode: (id: string | null) => void;
  className?: string;
}

export function WorkflowCanvas({
  nodes,
  connections,
  onNodesChange,
  onConnectionsChange,
  selectedNodeId,
  onSelectNode,
  className,
}: WorkflowCanvasProps) {
  // Zoom & Pan states
  const [scale, setScale] = React.useState(1);
  const [pan, setPan] = React.useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = React.useState(false);
  const [panStart, setPanStart] = React.useState({ x: 0, y: 0 });

  // Node connection wire in progress
  const [wireStartNodeId, setWireStartNodeId] = React.useState<string | null>(null);

  // Undo/Redo stacks
  const [history, setHistory] = React.useState<{ nodes: NodeData[]; connections: Connection[] }[]>([]);
  const [historyIndex, setHistoryIndex] = React.useState(-1);

  const pushState = (newNodes: NodeData[], newConns: Connection[]) => {
    const nextHist = history.slice(0, historyIndex + 1);
    nextHist.push({ nodes: JSON.parse(JSON.stringify(newNodes)), connections: [...newConns] });
    setHistory(nextHist);
    setHistoryIndex(nextHist.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const state = history[historyIndex - 1];
      onNodesChange(state.nodes);
      onConnectionsChange(state.connections);
      setHistoryIndex(historyIndex - 1);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const state = history[historyIndex + 1];
      onNodesChange(state.nodes);
      onConnectionsChange(state.connections);
      setHistoryIndex(historyIndex + 1);
    }
  };

  // Drag node offset helpers
  const handleDragNode = (id: string, deltaX: number, deltaY: number) => {
    const updated = nodes.map((n) => {
      if (n.id === id) {
        return { ...n, x: Math.round(n.x + deltaX), y: Math.round(n.y + deltaY) };
      }
      return n;
    });
    onNodesChange(updated);
  };

  const handleDragNodeEnd = () => {
    pushState(nodes, connections);
  };

  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    // Only pan if clicking on empty canvas target
    if ((e.target as HTMLElement).id === 'grid-canvas-bg' || (e.target as HTMLElement).id === 'canvas-wrapper') {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      onSelectNode(null);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      });
    }
  };

  const handleCanvasMouseUp = () => {
    setIsPanning(false);
  };

  // Wire Connection management
  const handleNodeConnectorClick = (id: string) => {
    if (!wireStartNodeId) {
      setWireStartNodeId(id);
    } else {
      if (wireStartNodeId !== id) {
        // Create new wire connection
        const exists = connections.some((c) => c.fromId === wireStartNodeId && c.toId === id);
        if (!exists) {
          const updated = [...connections, { fromId: wireStartNodeId, toId: id }];
          onConnectionsChange(updated);
          pushState(nodes, updated);
        }
      }
      setWireStartNodeId(null);
    }
  };

  // Add node helper
  const handleAddNode = (type: string) => {
    const id = `${type}-${Date.now()}`;
    const x = Math.round(-pan.x + 200 + Math.random() * 50);
    const y = Math.round(-pan.y + 150 + Math.random() * 50);
    const newNode: NodeData = {
      id,
      type,
      name: `New ${NODE_TYPES[type]?.label || 'Node'}`,
      x,
      y,
      config: {},
    };
    const updatedNodes = [...nodes, newNode];
    onNodesChange(updatedNodes);
    pushState(updatedNodes, connections);
    onSelectNode(id);
  };

  // Delete node helper
  const handleDeleteNode = (id: string) => {
    const updatedNodes = nodes.filter((n) => n.id !== id);
    const updatedConns = connections.filter((c) => c.fromId !== id && c.toId !== id);
    onNodesChange(updatedNodes);
    onConnectionsChange(updatedConns);
    pushState(updatedNodes, updatedConns);
    if (selectedNodeId === id) onSelectNode(null);
  };

  const handleAutoLayout = () => {
    const sorted = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
    const arranged = sorted.map((n, idx) => ({
      ...n,
      x: 100 + idx * 250,
      y: 200,
    }));
    onNodesChange(arranged);
    pushState(arranged, connections);
  };

  return (
    <div className={cn('relative w-full h-[550px] bg-neutral-950 border border-white/5 rounded-2xl overflow-hidden cursor-grab active:cursor-grabbing text-left select-none', className)}>
      
      {/* 1. Canvas Toolbar Controls */}
      <div className="absolute top-4 left-4 z-10 flex bg-neutral-900 border border-white/8 rounded-lg p-1 gap-1.5 shadow-xl">
        <button onClick={() => setScale(Math.min(scale + 0.1, 1.5))} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white" title="Zoom In"><ZoomIn className="w-4 h-4" /></button>
        <button onClick={() => setScale(Math.max(scale - 0.1, 0.5))} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white" title="Zoom Out"><ZoomOut className="w-4 h-4" /></button>
        <button onClick={() => { setScale(1); setPan({ x: 0, y: 0 }); }} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white" title="Reset view"><Maximize className="w-4 h-4" /></button>
        <div className="w-px bg-white/5 self-stretch my-1" />
        <button onClick={handleUndo} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white" title="Undo"><Undo2 className="w-4 h-4" /></button>
        <button onClick={handleRedo} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white" title="Redo"><Redo2 className="w-4 h-4" /></button>
        <div className="w-px bg-white/5 self-stretch my-1" />
        <button onClick={handleAutoLayout} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white text-xs font-semibold px-2" title="Auto Layout">Auto Layout</button>
      </div>

      {/* Add nodes bar */}
      <div className="absolute top-4 right-4 z-10 flex bg-neutral-900 border border-white/8 rounded-lg p-1 gap-1 shadow-xl max-w-[400px] overflow-x-auto">
        {Object.entries(NODE_TYPES).map(([type, meta]) => {
          const Icon = meta.icon;
          return (
            <button
              key={type}
              onClick={() => handleAddNode(type)}
              className="p-2 rounded hover:bg-white/5 text-neutral-400 hover:text-white flex items-center gap-1.5 shrink-0 text-xs font-semibold cursor-pointer"
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{meta.label.split(' ')[0]}</span>
            </button>
          );
        })}
      </div>

      {/* 2. Main Drag Canvas Desk */}
      <div
        id="canvas-wrapper"
        onMouseDown={handleCanvasMouseDown}
        onMouseMove={handleCanvasMouseMove}
        onMouseUp={handleCanvasMouseUp}
        className="w-full h-full relative"
      >
        <div
          id="grid-canvas-bg"
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(#262626 1px, transparent 0)',
            backgroundSize: '24px 24px',
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
            transformOrigin: '0 0',
          }}
        />

        {/* Nodes Desk */}
        <div
          className="absolute"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
            transformOrigin: '0 0',
          }}
        >
          {/* SVG Connection wire lines */}
          <svg className="absolute overflow-visible pointer-events-none z-0">
            {connections.map((c, idx) => {
              const fromNode = nodes.find((n) => n.id === c.fromId);
              const toNode = nodes.find((n) => n.id === c.toId);
              if (!fromNode || !toNode) return null;

              // Compute wiring curves
              const x1 = fromNode.x + 200;
              const y1 = fromNode.y + 40;
              const x2 = toNode.x;
              const y2 = toNode.y + 40;
              const dx = Math.abs(x2 - x1) * 0.5;

              return (
                <g key={`${c.fromId}-${c.toId}-${idx}`}>
                  <path
                    d={`M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    className="opacity-70"
                  />
                  <circle cx={x2} cy={y2} r={3} fill="#8b5cf6" />
                </g>
              );
            })}
          </svg>

          {/* Individual draggable node boxes */}
          {nodes.map((node) => {
            const isSelected = selectedNodeId === node.id;
            return (
              <WorkflowNode
                key={node.id}
                node={node}
                isSelected={isSelected}
                onSelect={() => onSelectNode(node.id)}
                onDelete={() => handleDeleteNode(node.id)}
                onConnectorClick={() => handleNodeConnectorClick(node.id)}
                isWiringSource={wireStartNodeId === node.id}
                onDrag={(dx, dy) => handleDragNode(node.id, dx, dy)}
                onDragEnd={handleDragNodeEnd}
              />
            );
          })}
        </div>
      </div>
      
      {/* 3. Mini-Map Drawer */}
      <div className="absolute bottom-4 right-4 bg-neutral-900 border border-white/8 rounded-lg p-2.5 w-24 h-16 shadow-2xl overflow-hidden pointer-events-none opacity-40 select-none">
        <div className="w-full h-full relative border border-white/5 rounded">
          {nodes.map((n) => (
            <div
              key={n.id + '-map'}
              className="absolute w-1 h-1 rounded-full bg-violet-500"
              style={{
                left: `${(n.x / 1000) * 100}%`,
                top: `${(n.y / 1000) * 100}%`,
              }}
            />
          ))}
        </div>
      </div>

    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Component: WorkflowNode
// ─────────────────────────────────────────────────────────────────────────────
interface WorkflowNodeProps {
  node: NodeData;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onConnectorClick: () => void;
  isWiringSource: boolean;
  onDrag: (dx: number, dy: number) => void;
  onDragEnd: () => void;
}

export function WorkflowNode({
  node,
  isSelected,
  onSelect,
  onDelete,
  onConnectorClick,
  isWiringSource,
  onDrag,
  onDragEnd,
}: WorkflowNodeProps) {
  const meta = NODE_TYPES[node.type] || { label: 'Action Node', icon: Code, color: 'bg-neutral-800' };
  const Icon = meta.icon;

  // Custom mouse drag tracking
  const handleMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect();

    const startX = e.clientX;
    const startY = e.clientY;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      onDrag(dx, dy);
    };

    const handleMouseUp = () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      onDragEnd();
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div
      onMouseDown={handleMouseDown}
      className={cn(
        'absolute w-[200px] h-20 rounded-xl border p-3 flex flex-col justify-between bg-neutral-950/80 cursor-grab hover:border-violet-500/30 transition-all select-none shadow-md z-10',
        isSelected ? 'border-violet-500 ring-2 ring-violet-500/25 bg-neutral-900' : 'border-white/5',
        node.status === 'RUNNING' && 'border-violet-400 animate-pulse',
        node.status === 'COMPLETED' && 'border-emerald-500/40 bg-emerald-950/10',
        node.status === 'FAILED' && 'border-rose-500/40 bg-rose-950/10'
      )}
      style={{
        left: node.x,
        top: node.y,
      }}
    >
      {/* Node Connector handles */}
      {/* Input connector on the left */}
      <button
        onMouseDown={(e) => { e.stopPropagation(); onConnectorClick(); }}
        className={cn(
          'absolute left-[-5px] top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border border-violet-500/50 bg-neutral-950 hover:bg-violet-400 transition-colors z-20 cursor-pointer',
          isWiringSource && 'bg-violet-500 scale-125'
        )}
        title="Input Handle"
      />

      <div className="flex items-center gap-2.5">
        <div className={cn('w-7 h-7 rounded border flex items-center justify-center shrink-0', meta.color)}>
          <Icon className="w-3.5 h-3.5" />
        </div>
        <div className="truncate">
          <span className="text-[10px] font-bold text-white block truncate leading-tight">{node.name}</span>
          <span className="text-[8px] font-mono text-neutral-500 uppercase tracking-wide block mt-1">{node.type}</span>
        </div>
      </div>

      <div className="flex justify-between items-center text-[9px] border-t border-white/5 pt-1.5 mt-1 font-mono">
        <span className="text-neutral-500">
          {node.status || 'READY'}
        </span>
        <button
          onMouseDown={(e) => { e.stopPropagation(); onDelete(); }}
          className="text-neutral-600 hover:text-rose-400 transition-colors cursor-pointer"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Output connector on the right */}
      <button
        onMouseDown={(e) => { e.stopPropagation(); onConnectorClick(); }}
        className={cn(
          'absolute right-[-5px] top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border border-violet-500/50 bg-neutral-950 hover:bg-violet-400 transition-colors z-20 cursor-pointer',
          isWiringSource && 'bg-violet-500 scale-125'
        )}
        title="Output Handle"
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Component: NodeInspector (Sidebar properties configure)
// ─────────────────────────────────────────────────────────────────────────────
interface NodeInspectorProps {
  node: NodeData | null;
  onUpdateConfig: (id: string, config: Record<string, any>, updatedName?: string) => void;
  className?: string;
}

export function NodeInspector({ node, onUpdateConfig, className }: NodeInspectorProps) {
  if (!node) {
    return (
      <div className={cn('p-6 text-center text-xs text-neutral-500 border border-white/5 bg-neutral-950/20 rounded-2xl flex flex-col items-center justify-center p-4 gap-2 h-full', className)}>
        <HelpCircle className="w-8 h-8 opacity-20" />
        <span>Select flowchart node to configure properties.</span>
      </div>
    );
  }

  const [localName, setLocalName] = React.useState(node.name);
  const [localConfig, setLocalConfig] = React.useState<Record<string, any>>(node.config);

  React.useEffect(() => {
    setLocalName(node.name);
    setLocalConfig(node.config);
  }, [node]);

  const handleUpdateField = (key: string, value: any) => {
    const updated = { ...localConfig, [key]: value };
    setLocalConfig(updated);
    onUpdateConfig(node.id, updated, localName);
  };

  const handleNameChange = (val: string) => {
    setLocalName(val);
    onUpdateConfig(node.id, localConfig, val);
  };

  return (
    <div className={cn('p-5 rounded-2xl border border-white/8 bg-neutral-950/40 space-y-6 text-left h-full overflow-y-auto', className)}>
      <div className="border-b border-white/5 pb-4">
        <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Node Settings</span>
        <span className="text-xs text-white font-bold block mt-1 leading-snug">{node.name}</span>
      </div>

      <div className="space-y-4">
        {/* Node custom name field */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Custom Label</label>
          <input
            type="text"
            value={localName}
            onChange={(e) => handleNameChange(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500"
          />
        </div>

        {/* Custom fields dependent on type */}
        {node.type === 'trigger' && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Trigger Mechanism</label>
              <select
                value={localConfig.triggerType || 'manual'}
                onChange={(e) => handleUpdateField('triggerType', e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none"
              >
                <option value="manual">Manual trigger</option>
                <option value="scheduled">Scheduled cron job</option>
                <option value="webhook">Inbound webhook callback</option>
                <option value="crm">CRM Event (New Contact)</option>
              </select>
            </div>

            {localConfig.triggerType === 'scheduled' && (
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Cron Expression</label>
                <input
                  type="text"
                  value={localConfig.cronExpression || '0 * * * *'}
                  onChange={(e) => handleUpdateField('cronExpression', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none font-mono"
                />
              </div>
            )}
          </div>
        )}

        {node.type === 'agent' && (
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Bind Agent AI</label>
            <input
              type="text"
              value={localConfig.agentName || ''}
              onChange={(e) => handleUpdateField('agentName', e.target.value)}
              placeholder="UUID or Name..."
              className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none"
            />
          </div>
        )}

        {node.type === 'prompt' && (
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">System Instructions Context</label>
            <textarea
              value={localConfig.promptTemplate || ''}
              onChange={(e) => handleUpdateField('promptTemplate', e.target.value)}
              rows={4}
              placeholder="e.g. Scrape and analyze lead targets..."
              className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none leading-relaxed font-mono"
            />
          </div>
        )}

        {node.type === 'slack' && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Webhook URL</label>
              <input
                type="text"
                value={localConfig.slackWebhook || ''}
                onChange={(e) => handleUpdateField('slackWebhook', e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Slack Message payload</label>
              <textarea
                value={localConfig.slackMessage || ''}
                onChange={(e) => handleUpdateField('slackMessage', e.target.value)}
                rows={3}
                placeholder="Audit trace alert..."
                className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none leading-relaxed"
              />
            </div>
          </div>
        )}

        {node.type === 'delay' && (
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Duration Seconds</label>
            <input
              type="number"
              value={localConfig.delaySeconds || 60}
              onChange={(e) => handleUpdateField('delaySeconds', parseInt(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none"
            />
          </div>
        )}
      </div>

    </div>
  );
}
