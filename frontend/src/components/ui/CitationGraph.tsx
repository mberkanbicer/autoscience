'use client';

import { useEffect } from 'react';
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
import type { CitationGraph as CitationGraphData } from '@/lib/types';

interface CitationGraphProps {
  data: CitationGraphData;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function CitationGraph({ data, onNodeClick, className }: CitationGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!data?.nodes?.length) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    const center = { x: 500, y: 400 };
    const radius = Math.max(250, data.nodes.length * 30);

    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      const x = center.x + radius * Math.cos(angle);
      const y = center.y + radius * Math.sin(angle);
      const label = node.label.length > 36 ? `${node.label.slice(0, 36)}…` : node.label;

      newNodes.push({
        id: node.id,
        data: {
          label: (
            <div className="text-center">
              <div className="font-bold leading-tight">{label}</div>
              {node.year && (
                <div className="text-[8px] opacity-60 mt-1">{node.year}</div>
              )}
            </div>
          ),
        },
        position: { x, y },
        style: {
          background: 'hsla(var(--primary), 0.08)',
          border: '2px solid hsl(var(--primary))',
          borderRadius: '14px',
          fontSize: '9px',
          fontWeight: 800,
          color: 'hsl(var(--primary))',
          width: 150,
          padding: '10px',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)',
        },
      });
    });

    data.edges.forEach((edge, i) => {
      newEdges.push({
        id: `cite-${i}`,
        source: edge.source,
        target: edge.target,
        label: edge.label || 'cites',
        type: ConnectionLineType.SmoothStep,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: 'hsl(var(--primary))' },
        style: { stroke: 'hsl(var(--primary))', strokeWidth: 1.5 },
        labelStyle: { fontSize: 8, fontWeight: 700 },
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data, setNodes, setEdges]);

  return (
    <div className={className ?? 'h-[600px] glass rounded-[2.5rem] border border-stone-200/10'}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} color="hsl(var(--border))" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}