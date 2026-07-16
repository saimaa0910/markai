'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useWorkflowDetails, useWorkflows, useWorkflowExecution, useExecutionSteps } from '@/features/workflows/hooks';
import { WorkflowFlowchart } from '@/features/workflows/components/WorkflowFlowchart';
import { NodeInspector } from '@/features/workflows/components/canvas';
import { useNodesState, useEdgesState, addEdge, MarkerType } from '@xyflow/react';
import { Button } from '@/components/ui/button';
import { ExecutionLog } from '@/features/agents/components/timeline';
import { ArrowLeft, Save, Play, RefreshCw, AlertCircle } from 'lucide-react';
import { cn } from '@eaimos/shared';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function WorkflowDetailsRoute({ params }: RouteProps) {
  const router = useRouter();
  const { id } = React.use(params);

  const { workflow, isLoading, isError } = useWorkflowDetails(id);
  const { updateWorkflow } = useWorkflows();
  const { executeWorkflow } = useWorkflowExecution(id);

  // Workflow meta data settings
  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [status, setStatus] = React.useState<any>('DRAFT');

  // Lifted React Flow canvas state
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);

  // Live execution variables
  const [runLogsId, setRunLogsId] = React.useState<string | undefined>(undefined);
  const { steps: executionSteps, isLoading: loadingSteps } = useExecutionSteps(runLogsId);

  const loadedWorkflowId = React.useRef<string | null>(null);

  // Sync loaded definition properties once on fetch
  React.useEffect(() => {
    if (workflow && loadedWorkflowId.current !== workflow.id) {
      loadedWorkflowId.current = workflow.id;
      setName(workflow.name);
      setDescription(workflow.description || '');
      setStatus(workflow.status);

      // Reconstruct nodes from steps_definition
      const visualNodes = (workflow.steps_definition || []).map((step, idx) => ({
        id: step.id,
        type: step.type || 'agent',
        position: { x: step.x !== undefined ? step.x : 100 + idx * 220, y: step.y !== undefined ? step.y : 200 },
        data: {
          label: step.name,
          status: step.status || 'READY',
          config: step.config || {},
        },
      }));

      // Reconstruct connection links
      const links: any[] = [];
      (workflow.steps_definition || []).forEach((step) => {
        if (step.next && Array.isArray(step.next)) {
          step.next.forEach((targetId: string, linkIdx: number) => {
            links.push({
              id: `e-${step.id}-${targetId}-${linkIdx}`,
              source: step.id,
              target: targetId,
              animated: true,
              style: { stroke: '#8b5cf6', strokeWidth: 2 },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#8b5cf6' },
            });
          });
        }
      });

      setNodes(visualNodes);
      setEdges(links);
    }
  }, [workflow, setNodes, setEdges]);

  // Sync node status glows during execution steps
  React.useEffect(() => {
    if (executionSteps && executionSteps.length > 0) {
      setNodes((prev) =>
        prev.map((n) => {
          const stepMatch = executionSteps.find((s) => s.step_id === n.id);
          if (stepMatch) {
            return {
              ...n,
              data: {
                ...n.data,
                status: stepMatch.status as any,
              },
            };
          }
          return n;
        })
      );
    }
  }, [executionSteps, setNodes]);

  const handleUpdateNodeConfig = (nodeId: string, config: Record<string, any>, updatedName?: string) => {
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === nodeId) {
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
    updateWorkflow.mutate(
      {
        id,
        data: {
          name,
          description: description || null,
          status,
          steps_definition: nodes.map((n) => ({
            id: n.id,
            type: n.type || 'agent',
            name: n.data.label,
            x: n.position.x,
            y: n.position.y,
            config: n.data.config || {},
            next: edges.filter((e) => e.source === n.id).map((e) => e.target),
          })),
        },
      },
      {
        onSuccess: () => {
          alert('Workflow saved successfully!');
        },
      }
    );
  };

  const handleExecute = () => {
    // Soft save layout first to catch connector adjustments
    handleSave();

    // Trigger run execution mutation
    executeWorkflow.mutate(
      {},
      {
        onSuccess: (data) => {
          setRunLogsId(data.id);
          alert(`Workflow triggered successfully. Execution status: ${data.status}`);
        },
      }
    );
  };

  const handleAddNode = (type: string) => {
    const nodeId = `${type}-${Date.now()}`;
    const newNode = {
      id: nodeId,
      type,
      position: { x: 250 + Math.random() * 50, y: 150 + Math.random() * 50 },
      data: {
        label: `New ${type.toUpperCase()}`,
        status: 'READY',
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeId(nodeId);
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    if (selectedNodeId === nodeId) setSelectedNodeId(null);
  };

  const handleAutoLayout = () => {
    setNodes((nds) =>
      nds.map((n, idx) => ({
        ...n,
        position: { x: 100 + idx * 240, y: 200 },
      }))
    );
  };

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

  if (isLoading) {
    return (
      <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-violet-400" />
        <span className="text-xs">Loading workflow canvas details...</span>
      </div>
    );
  }

  if (isError || !workflow) {
    return (
      <div className="py-20 text-center text-neutral-500 flex flex-col items-center gap-3">
        <AlertCircle className="w-8 h-8 opacity-25" />
        <span>Workflow blueprint details not found.</span>
        <Button variant="outline" onClick={() => router.push('/dashboard/workflows')} className="mt-4">
          Back to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard/workflows')}
            className="p-2 rounded-lg border border-white/5 bg-neutral-950 text-neutral-400 hover:text-white transition-all cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">{name}</h2>
            <p className="text-xs text-neutral-400 mt-1 uppercase font-mono tracking-wider">{workflow.trigger} · Blueprint ID: {workflow.id.slice(0, 8)}</p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleExecute}
            className="h-10 text-xs font-semibold gap-1.5 border-white/5 text-neutral-300 hover:text-white cursor-pointer"
            isLoading={executeWorkflow.isPending}
          >
            <Play className="w-4 h-4 text-violet-400" /> Run Workflow
          </Button>
          <Button
            variant="violet"
            onClick={handleSave}
            className="h-10 text-xs font-semibold gap-1.5"
            isLoading={updateWorkflow.isPending}
          >
            <Save className="w-4 h-4" /> Save changes
          </Button>
        </div>
      </div>

      {/* Meta configuration bar */}
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
            placeholder="Outline this automation..."
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Status Blueprint</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
            className="w-full px-3 py-2 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white focus:outline-none"
          >
            <option value="DRAFT">DRAFT</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="ARCHIVED">ARCHIVED</option>
          </select>
        </div>
      </div>

      {/* Editor desk & logs console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Canvas editor (col-span-9) */}
        <div className="lg:col-span-9 space-y-6">
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

          {/* Execution steps logs feed */}
          {runLogsId && (
            <div className="space-y-3.5 text-left border-t border-white/5 pt-6">
              <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest block">Live Run Diagnostics</span>
              <ExecutionLog 
                logs={executionSteps.map((step) => ({
                  id: step.id,
                  run_id: step.execution_id,
                  organization_id: step.organization_id,
                  level: step.status === 'FAILED' ? 'ERROR' : 'INFO',
                  step_type: step.step_type,
                  content: step.error_message 
                    ? `Node Execution failed: ${step.error_message}` 
                    : `Node successfully completed in ${step.latency_ms || 0}ms. Input: ${JSON.stringify(step.input_data || {})}, Output: ${JSON.stringify(step.output_data || {})}`,
                  meta_data: step.output_data,
                }))}
                isLoading={loadingSteps}
              />
            </div>
          )}
        </div>

        {/* Node inspector panel (col-span-3) */}
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
