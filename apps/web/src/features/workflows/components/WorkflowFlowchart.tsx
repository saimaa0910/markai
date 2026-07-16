'use client';

import * as React from 'react';
import { 
  ReactFlow, MiniMap, Controls, Background, 
  MarkerType 
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CustomNode } from './CustomNode';
import { 
  ZoomIn, ZoomOut, Maximize, Undo2, Redo2, 
  Activity, Sparkles 
} from 'lucide-react';
import { cn } from '@eaimos/shared';

// Register custom node templates mapping
const NODE_TYPES = {
  trigger: CustomNode,
  agent: CustomNode,
  prompt: CustomNode,
  knowledge: CustomNode,
  crm: CustomNode,
  campaign: CustomNode,
  condition: CustomNode,
  delay: CustomNode,
  slack: CustomNode,
  email: CustomNode,
  end: CustomNode,
};

interface WorkflowFlowchartProps {
  nodes: any[];
  edges: any[];
  onNodesChange: any;
  onEdgesChange: any;
  onConnect: any;
  onSelectNode: (nodeId: string | null) => void;
  onDeleteNode: (nodeId: string) => void;
  onAddNode: (type: string) => void;
  onAutoLayout: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  className?: string;
}

export function WorkflowFlowchart({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onSelectNode,
  onDeleteNode,
  onAddNode,
  onAutoLayout,
  onUndo,
  onRedo,
  className,
}: WorkflowFlowchartProps) {
  const handleNodeClick = (_: any, node: any) => {
    onSelectNode(node.id);
  };

  // Inject onDelete trigger into node data properties
  const nodesWithCallbacks = React.useMemo(() => {
    return nodes.map((n) => ({
      ...n,
      data: {
        ...n.data,
        onDelete: onDeleteNode,
      },
    }));
  }, [nodes, onDeleteNode]);

  return (
    <div className={cn('relative w-full h-[550px] bg-neutral-950 border border-white/5 rounded-2xl overflow-hidden text-left', className)}>
      
      {/* Zoom / History controls toolbar */}
      <div className="absolute top-4 left-4 z-10 flex bg-neutral-900 border border-white/8 rounded-lg p-1 gap-1.5 shadow-xl select-none">
        {onUndo && (
          <button onClick={onUndo} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white cursor-pointer" title="Undo">
            <Undo2 className="w-4 h-4" />
          </button>
        )}
        {onRedo && (
          <button onClick={onRedo} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white cursor-pointer" title="Redo">
            <Redo2 className="w-4 h-4" />
          </button>
        )}
        <div className="w-px bg-white/5 self-stretch my-1" />
        <button onClick={onAutoLayout} className="p-1.5 rounded hover:bg-white/5 text-neutral-400 hover:text-white text-xs font-semibold px-2 cursor-pointer" title="Auto Layout">
          Auto Layout
        </button>
      </div>

      {/* Node Library drawer selector panel */}
      <div className="absolute top-4 right-4 z-10 flex bg-neutral-900 border border-white/8 rounded-lg p-1 gap-1 shadow-xl max-w-[450px] overflow-x-auto select-none scrollbar-none">
        {['trigger', 'agent', 'prompt', 'knowledge', 'crm', 'campaign', 'condition', 'delay', 'slack', 'email', 'end'].map((type) => (
          <button
            key={type}
            onClick={() => onAddNode(type)}
            className="p-2 rounded hover:bg-white/5 text-neutral-400 hover:text-white flex items-center gap-1.5 shrink-0 text-xs font-semibold cursor-pointer capitalize"
          >
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            <span>{type}</span>
          </button>
        ))}
      </div>

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodesWithCallbacks}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        nodeTypes={NODE_TYPES}
        fitView
      >
        <Background color="#333" gap={16} />
        <Controls showInteractive={false} className="!bg-neutral-900 !border-white/5 !text-white" />
        <MiniMap 
          nodeColor={() => '#8b5cf6'} 
          maskColor="rgba(0, 0, 0, 0.7)" 
          className="!bg-neutral-900 !border-white/5"
          style={{ width: 100, height: 70 }}
        />
      </ReactFlow>

    </div>
  );
}
