'use client';

import * as React from 'react';
import { Handle, Position } from '@xyflow/react';
import { 
  Play, Bot, Code, FolderSearch, Users, Megaphone, 
  BarChart2, Split, Clock, Activity, Mail, Trash2, 
  Plus, Settings, MessageSquare, Database, CheckCircle2, 
  AlertCircle, HelpCircle 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

const NODE_ICONS: Record<string, any> = {
  trigger: Play,
  agent: Bot,
  prompt: Code,
  knowledge: FolderSearch,
  crm: Users,
  campaign: Megaphone,
  condition: Split,
  delay: Clock,
  slack: MessageSquare,
  email: Mail,
  webhook: Activity,
  http: Activity,
  storage: Database,
  end: CheckCircle2,
};

const NODE_COLORS: Record<string, string> = {
  trigger: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  agent: 'bg-violet-500/10 border-violet-500/30 text-violet-400',
  prompt: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400',
  knowledge: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
  crm: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
  campaign: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  condition: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
  delay: 'bg-neutral-800 border-white/10 text-neutral-400',
  slack: 'bg-violet-600/20 border-violet-500/30 text-violet-300',
  email: 'bg-teal-500/10 border-teal-500/30 text-teal-400',
  end: 'bg-neutral-900 border-white/5 text-neutral-500',
};

export function CustomNode({ data, id, type }: any) {
  const nodeType = type || 'agent';
  const Icon = NODE_ICONS[nodeType] || HelpCircle;
  const colorClass = NODE_COLORS[nodeType] || 'bg-neutral-800 text-neutral-400';

  const isTrigger = nodeType === 'trigger';
  const isEnd = nodeType === 'end';
  const isCondition = nodeType === 'condition';

  return (
    <div
      className={cn(
        'w-[200px] h-20 rounded-xl border p-3 flex flex-col justify-between bg-neutral-950/80 cursor-grab hover:border-violet-500/30 transition-all select-none shadow-md',
        data.isSelected ? 'border-violet-500 ring-2 ring-violet-500/25 bg-neutral-900' : 'border-white/5',
        data.status === 'RUNNING' && 'border-violet-400 animate-pulse',
        data.status === 'COMPLETED' && 'border-emerald-500/40 bg-emerald-950/10',
        data.status === 'FAILED' && 'border-rose-500/40 bg-rose-950/10'
      )}
    >
      {/* Target input handle (on the left) */}
      {!isTrigger && (
        <Handle
          type="target"
          position={Position.Left}
          style={{ background: '#8b5cf6', width: 8, height: 8 }}
          id="input-handle"
        />
      )}

      <div className="flex items-center gap-2.5">
        <div className={cn('w-7 h-7 rounded border flex items-center justify-center shrink-0', colorClass)}>
          <Icon className="w-3.5 h-3.5" />
        </div>
        <div className="truncate text-left">
          <span className="text-[10px] font-bold text-white block truncate leading-tight">{data.label || 'Action Node'}</span>
          <span className="text-[8px] font-mono text-neutral-500 uppercase tracking-wide block mt-1">{nodeType}</span>
        </div>
      </div>

      <div className="flex justify-between items-center text-[9px] border-t border-white/5 pt-1.5 mt-1 font-mono text-left">
        <span className="text-neutral-500">
          {data.status || 'READY'}
        </span>
        {data.onDelete && (
          <button
            onClick={(e) => { e.stopPropagation(); data.onDelete(id); }}
            className="text-neutral-600 hover:text-rose-400 transition-colors cursor-pointer"
          >
            Delete
          </button>
        )}
      </div>

      {/* Source output handles (on the right) */}
      {!isEnd && (
        <>
          {isCondition ? (
            <>
              {/* True handle */}
              <Handle
                type="source"
                position={Position.Right}
                id="true"
                style={{ top: '30%', background: '#10b981', width: 8, height: 8 }}
                title="True Branch"
              />
              {/* False handle */}
              <Handle
                type="source"
                position={Position.Right}
                id="false"
                style={{ top: '70%', background: '#ef4444', width: 8, height: 8 }}
                title="False Branch"
              />
            </>
          ) : (
            <Handle
              type="source"
              position={Position.Right}
              style={{ background: '#8b5cf6', width: 8, height: 8 }}
              id="output-handle"
            />
          )}
        </>
      )}
    </div>
  );
}
