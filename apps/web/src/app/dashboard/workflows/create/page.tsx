'use client';

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useWorkflows } from '@/features/workflows/hooks';
import dynamic from 'next/dynamic';
import { RefreshCw } from 'lucide-react';

const WorkflowFlowchart = dynamic(
  () => import('@/features/workflows/components/WorkflowFlowchart').then((mod) => mod.WorkflowFlowchart),
  {
    ssr: false,
    loading: () => (
      <div className="h-[500px] bg-neutral-900/50 rounded-xl border border-white/5 flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-violet-400" />
        <span className="text-xs text-neutral-500 font-mono">Loading dynamic workflow canvas editor...</span>
      </div>
    ),
  }
);
import { NodeInspector } from '@/features/workflows/components/canvas';
import { useNodesState, useEdgesState, addEdge, MarkerType } from '@xyflow/react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Save, Sparkles } from 'lucide-react';
import { cn } from '@eaimos/shared';

export default function CreateWorkflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const templateName = searchParams.get('name') || '';
  const templateDesc = searchParams.get('desc') || '';
  const templateTrigger = searchParams.get('trigger') || 'MANUAL';

  const { createWorkflow } = useWorkflows();

  // Workflow Form attributes
  const [name, setName] = React.useState(templateName || 'My Automation Workflow');
  const [description, setDescription] = React.useState(templateDesc || '');
  const [triggerType, setTriggerType] = React.useState<any>(templateTrigger);
  const [cronExpression] = React.useState('*/10 * * * *');

  // Lifted React Flow canvas state
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([
    { 
      id: 'trigger-1', 
      type: 'trigger', 
      position: { x: 100, y: 200 }, 
      data: { label: 'Trigger Input', status: 'READY', config: { triggerType: 'manual' } } 
    },
  ]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);

  // Sync template trigger config if provided
  React.useEffect(() => {
    if (templateTrigger) {
      setTriggerType(templateTrigger);
    }
  }, [templateTrigger]);

  // Connect edge wire trigger handler
  const onConnect = React.useCallback(
    (params: any) => {
      const newEdge = {
        ...params,
        animated: true,
        style: { stroke: '#8b5cf6', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#8b5cf6' },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const handleUpdateNodeConfig = (id: string, config: Record<string, any>, updatedName?: string) => {
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === id) {
          return {
            ...n,
            data: {
              ...n.data,
              config,
              label: updatedName !== undefined ? updatedName : n.data.label,
            },
          };
        }
        return n;
      })
    );
  };

  const selectedNode = React.useMemo(() => {
    const fn = nodes.find((n) => n.id === selectedNodeId);
    if (!fn) return null;
    return {
      id: fn.id,
      type: fn.type,
      name: fn.data.label,
      x: fn.position?.x || 0,
      y: fn.position?.y || 0,
      config: fn.data.config || {},
    };
  }, [nodes, selectedNodeId]);

  const handleSave = () => {
    if (!name.trim()) {
      alert('Please enter a workflow name.');
      return;
    }

    createWorkflow.mutate(
      {
        name,
        description: description || null,
        status: 'DRAFT',
        trigger: triggerType,
        steps_definition: nodes.map((n) => ({
          id: n.id,
          type: n.type || 'agent',
          name: n.data.label,
          x: n.position.x,
          y: n.position.y,
          config: n.data.config || {},
          next: edges.filter((e) => e.source === n.id).map((e) => e.target),
        })),
        cron_expression: triggerType === 'SCHEDULED' ? cronExpression : null,
        webhook_config: null,
        max_retries: 3,
        timeout_seconds: 3600,
      },
      {
        onSuccess: () => {
          router.push('/dashboard/workflows');
        },
      }
    );
  };

  const handleDeleteNode = (id: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
    if (selectedNodeId === id) setSelectedNodeId(null);
  };

  const handleAddNode = (type: string) => {
    const id = `${type}-${Date.now()}`;
    const newNode = {
      id,
      type,
      position: { x: 250 + Math.random() * 50, y: 150 + Math.random() * 50 },
      data: {
        label: `New ${type.toUpperCase()}`,
        status: 'READY',
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeId(id);
  };

  const handleAutoLayout = () => {
    setNodes((nds) =>
      nds.map((n, idx) => ({
        ...n,
        position: { x: 100 + idx * 240, y: 200 },
      }))
    );
  };

  return (
    <div className="space-y-6 text-left">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/dashboard/workflows')}
            className="p-2 rounded-lg border border-white/5 bg-neutral-900 text-neutral-400 hover:text-white transition-all cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-violet-400" /> Visual Workflow Builder
            </h2>
            <p className="text-xs text-neutral-400 mt-1">Design triggers, AI agent execution logic, and data sync flows.</p>
          </div>
        </div>

        <Button
          variant="violet"
          onClick={handleSave}
          className="h-10 text-xs font-semibold gap-1.5"
          isLoading={createWorkflow.isPending}
        >
          <Save className="w-4 h-4" /> Save Workflow
        </Button>
      </div>

      {/* Meta data inputs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-neutral-950/40 p-4.5 rounded-xl border border-white/5">
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Workflow Name *</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the target automation task..."
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Trigger Hook *</label>
          <select
            value={triggerType}
            onChange={(e) => setTriggerType(e.target.value as any)}
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none"
          >
            <option value="MANUAL">Manual Trigger</option>
            <option value="SCHEDULED">Scheduled Cron</option>
            <option value="WEBHOOK">Inbound Webhook</option>
            <option value="CRM_EVENT">CRM Event Hook</option>
            <option value="CAMPAIGN_EVENT">Campaign Trigger</option>
          </select>
        </div>
      </div>

      {/* Canvas workspace split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        
        {/* Visual editor flowchart canvas (col-span-9) */}
        <div className="lg:col-span-9">
          <WorkflowFlowchart
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onSelectNode={setSelectedNodeId}
            onDeleteNode={handleDeleteNode}
            onAddNode={handleAddNode}
            onAutoLayout={handleAutoLayout}
          />
        </div>

        {/* Selected Node Properties drawer (col-span-3) */}
        <div className="lg:col-span-3">
          <NodeInspector
            node={selectedNode}
            onUpdateConfig={handleUpdateNodeConfig}
          />
        </div>
      </div>

    </div>
  );
}
