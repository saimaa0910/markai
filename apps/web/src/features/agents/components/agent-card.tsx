'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { AgentDefinition } from '../types';
import { AgentAvatar, AgentStatusBadge } from './badges';
import { Button } from '@/components/ui/button';
import { 
  Settings, Play, Copy, Archive, Trash2, 
  ArrowRight, Sparkles, Cpu, CpuIcon 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

interface AgentCardProps {
  agent: AgentDefinition;
  onDuplicate?: (agent: AgentDefinition) => void;
  onArchive?: (agent: AgentDefinition) => void;
  onDelete?: (agent: AgentDefinition) => void;
  viewMode?: 'grid' | 'list';
}

export function AgentCard({
  agent,
  onDuplicate,
  onArchive,
  onDelete,
  viewMode = 'grid',
}: AgentCardProps) {
  const router = useRouter();

  if (viewMode === 'list') {
    return (
      <div className="flex items-center justify-between p-4 rounded-xl border border-white/5 bg-neutral-950/40 hover:border-violet-500/20 hover:bg-neutral-900/10 transition-all duration-300 group">
        <div className="flex items-center gap-4">
          <AgentAvatar name={agent.name} avatarColor={agent.avatar_color} />
          <div>
            <h4 className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
              {agent.name}
            </h4>
            <p className="text-xs text-neutral-400 truncate max-w-md mt-0.5">
              {agent.description || 'No description provided.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-neutral-500 px-2 py-0.5 rounded bg-neutral-900 border border-white/5 uppercase">
            {agent.agent_type}
          </span>
          <span className="text-[10px] font-mono text-neutral-500 px-2 py-0.5 rounded bg-neutral-900 border border-white/5">
            {agent.preferred_model || 'Gateway default'}
          </span>
          <AgentStatusBadge status={agent.status} />

          <div className="flex items-center gap-1.5 border-l border-white/5 pl-3 ml-1">
            <Button
              variant="ghost"
              size="icon"
              className="w-8 h-8 text-neutral-500 hover:text-white"
              onClick={() => router.push(`/dashboard/agents/${agent.id}`)}
              title="Configure Agent"
            >
              <Settings className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="w-8 h-8 text-neutral-500 hover:text-white"
              onClick={() => router.push(`/dashboard/agents/playground?agentId=${agent.id}`)}
              title="Chat in Playground"
            >
              <Play className="w-4 h-4 text-violet-400" />
            </Button>
            {onDuplicate && (
              <Button
                variant="ghost"
                size="icon"
                className="w-8 h-8 text-neutral-500 hover:text-white"
                onClick={() => onDuplicate(agent)}
                title="Duplicate Definition"
              >
                <Copy className="w-3.5 h-3.5" />
              </Button>
            )}
            {onArchive && agent.status !== 'ARCHIVED' && (
              <Button
                variant="ghost"
                size="icon"
                className="w-8 h-8 text-neutral-500 hover:text-white"
                onClick={() => onArchive(agent)}
                title="Archive Agent"
              >
                <Archive className="w-3.5 h-3.5" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="w-8 h-8 text-neutral-500 hover:text-rose-400"
                onClick={() => onDelete(agent)}
                title="Delete Agent"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Grid view mode
  return (
    <div className="group rounded-2xl border border-white/8 bg-neutral-950/40 hover:border-violet-500/30 hover:bg-neutral-900/10 transition-all duration-300 flex flex-col justify-between overflow-hidden p-6 relative">
      <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px] pointer-events-none" />

      {/* Header card details */}
      <div className="flex items-start justify-between border-b border-white/5 pb-4 mb-4 text-left">
        <div className="flex items-center gap-3">
          <AgentAvatar name={agent.name} avatarColor={agent.avatar_color} />
          <div>
            <h4 className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors leading-tight">
              {agent.name}
            </h4>
            <span className="text-[9px] font-bold text-violet-400 font-mono uppercase tracking-wider block mt-1">
              {agent.agent_type}
            </span>
          </div>
        </div>
        <AgentStatusBadge status={agent.status} />
      </div>

      {/* Body desc details */}
      <div className="text-left mb-6">
        <p className="text-neutral-400 text-xs leading-relaxed min-h-[40px] line-clamp-3">
          {agent.description || 'No description provided.'}
        </p>

        <div className="flex items-center gap-2 mt-4 text-[10px] font-mono text-neutral-500">
          <Cpu className="w-3.5 h-3.5 text-neutral-600" />
          <span>Model: {agent.preferred_model || 'Gateway default'}</span>
        </div>
      </div>

      {/* Footer controls actions */}
      <div className="flex items-center justify-between border-t border-white/5 pt-4">
        <div className="flex items-center gap-1">
          {onDuplicate && (
            <Button
              variant="ghost"
              size="icon"
              className="w-7 h-7 text-neutral-500 hover:text-white"
              onClick={() => onDuplicate(agent)}
              title="Duplicate Definition"
            >
              <Copy className="w-3.5 h-3.5" />
            </Button>
          )}
          {onArchive && agent.status !== 'ARCHIVED' && (
            <Button
              variant="ghost"
              size="icon"
              className="w-7 h-7 text-neutral-500 hover:text-white"
              onClick={() => onArchive(agent)}
              title="Archive Agent"
            >
              <Archive className="w-3.5 h-3.5" />
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="w-7 h-7 text-neutral-500 hover:text-rose-400"
              onClick={() => onDelete(agent)}
              title="Delete Agent"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-[11px] text-neutral-300 hover:text-white px-2.5"
            onClick={() => router.push(`/dashboard/agents/${agent.id}`)}
          >
            Configure
          </Button>
          <Button
            variant="violet"
            size="sm"
            className="h-8 text-[11px] font-semibold gap-1 px-3"
            onClick={() => router.push(`/dashboard/agents/playground?agentId=${agent.id}`)}
          >
            Playground <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
