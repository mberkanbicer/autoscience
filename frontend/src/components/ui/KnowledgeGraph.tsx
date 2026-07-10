'use client';

import React, { useMemo, useEffect, useState } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Background, 
  Controls, 
  ConnectionLineType,
  MarkerType,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { cn } from '@/lib/utils';

interface KnowledgeGraphProps {
  data: {
    nodes: Array<{
      id: string;
      title: string;
      year?: number;
      cluster_id?: string;
      paper_type?: string;
      citation_count: number;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      type: string;
      label?: string;
      severity?: number;
    }>;
  };
  onNodeClick: (nodeId: string) => void;
}

export function KnowledgeGraph({ data, onNodeClick }: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!data) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Simple Circular/Force-ish Layout
    const center = { x: 500, y: 400 };
    const radius = 400;

    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      
      // Jitter slightly to avoid perfect circles
      const x = center.x + radius * Math.cos(angle) + (Math.random() * 50);
      const y = center.y + radius * Math.sin(angle) + (Math.random() * 50);
      
      // Paper types use tertiary (Terracotta) for review, primary (Amber) for research
      const isReview = node.paper_type === 'review';
      const nodeColor = isReview ? 'tertiary' : 'primary';

      newNodes.push({
        id: node.id,
        data: { label: node.title.slice(0, 30) + '...' },
        position: { x, y },
        style: {
          background: `hsla(var(--${nodeColor}), 0.1)`,
          border: `2px solid hsl(var(--${nodeColor}))`,
          borderRadius: '16px',
          fontSize: '9px',
          fontWeight: '800',
          color: `hsl(var(--${nodeColor}))`,
          width: 140,
          padding: '10px',
          backdropFilter: 'blur(10px)',
          textAlign: 'center' as const,
          boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)',
        },
      });
    });

    data.edges.forEach((edge) => {
      const isConflict = edge.type === 'conflict';
      const isCitation = edge.type === 'citation';
      
      const edgeColor = isConflict ? 'error' : (isCitation ? 'primary' : 'secondary');

      newEdges.push({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: isCitation,
        type: ConnectionLineType.SmoothStep,
        style: { 
          stroke: `hsl(var(--${edgeColor}))`, 
          strokeWidth: isConflict ? 3 : 1.5,
          opacity: isConflict ? 0.8 : 0.4
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: `hsl(var(--${edgeColor}))`,
        },
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data]);

  return (
    <div className="w-full h-[700px] glass rounded-[2.5rem] overflow-hidden shadow-2xl relative border border-stone-200/10">
      <div className="absolute top-8 left-8 z-10 space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-primary" />
          <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">Research Paper</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-error" />
          <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">Scientific Conflict</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-px bg-primary opacity-40" />
          <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">Citation Vector</span>
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeClick(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="hsla(var(--primary), 0.03)" gap={30} size={1} />
        <Controls className="glass-dark border-none shadow-2xl rounded-xl overflow-hidden mb-6 mr-6" />
      </ReactFlow>
    </div>
  );
}
