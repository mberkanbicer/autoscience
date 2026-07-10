'use client';

import React, { useMemo, useEffect } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Background, 
  Controls, 
  ConnectionLineType,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Paper, PaperCluster } from '@/lib/types';

interface SemanticMapProps {
  cluster: PaperCluster;
  papers: Paper[];
}

export function SemanticMap({ cluster, papers }: SemanticMapProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    // 1. Center Node: The Cluster
    newNodes.push({
      id: 'cluster-root',
      data: { label: cluster.name?.toUpperCase() || 'SYNTHETIC_NODE' },
      position: { x: 300, y: 150 },
      type: 'input',
      style: { 
        background: 'hsla(var(--primary), 0.2)', 
        border: '3px solid hsl(var(--primary))', 
        borderRadius: '24px', 
        fontSize: '10px', 
        fontWeight: '900', 
        color: 'hsl(var(--primary))', 
        width: 200, 
        padding: '20px',
        backdropFilter: 'blur(12px)', 
        letterSpacing: '0.2em', 
        boxShadow: '0 0 40px hsla(var(--primary), 0.3)' 
      },
    });

    // 2. Paper Nodes
    papers.forEach((paper, i) => {
      const angle = (i / papers.length) * 2 * Math.PI;
      const radius = 250;
      const x = 300 + radius * Math.cos(angle);
      const y = 150 + radius * Math.sin(angle);
      
      const id = `paper-${paper.id}`;
      newNodes.push({
        id,
        data: { label: paper.title.slice(0, 40) + (paper.title.length > 40 ? '...' : '') },
        position: { x, y },
        style: { 
          background: 'hsla(var(--secondary), 0.05)', 
          border: '1px solid hsla(var(--secondary), 0.2)', 
          borderRadius: '12px', 
          fontSize: '8px', 
          fontWeight: '700', 
          color: 'hsl(var(--secondary))', 
          width: 150, 
          padding: '10px',
          backdropFilter: 'blur(8px)', 
          letterSpacing: '0.05em' 
        },
      });

      newEdges.push({
        id: `e-root-${id}`,
        source: 'cluster-root',
        target: id,
        animated: true,
        style: { stroke: 'hsla(var(--primary), 0.3)', strokeWidth: 2 },
      });
    });

    // 3. Label Nodes (optional, showing them as satellites)
    cluster.labels.forEach((l, i) => {
        const x = 300 + (i % 2 === 0 ? -450 : 750);
        const y = i * 100;
        const id = `label-${i}`;
        newNodes.push({
            id,
            data: { label: `VECTOR: ${l.label}` },
            position: { x, y },
            style: { 
                background: 'hsla(var(--tertiary), 0.1)', 
                border: '1px solid hsla(var(--tertiary), 0.3)', 
                borderRadius: '8px', 
                fontSize: '8px', 
                fontWeight: '900', 
                color: 'hsl(var(--tertiary))', 
                width: 120, 
                padding: '8px',
                letterSpacing: '0.1em' 
            },
        });
        newEdges.push({
            id: `e-label-${id}`,
            source: 'cluster-root',
            target: id,
            style: { stroke: 'hsla(var(--tertiary), 0.2)', strokeWidth: 1, strokeDasharray: '5,5' },
        });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [cluster, papers, setNodes, setEdges]);

  return (
    <div className="w-full h-[500px] bg-stone-50 dark:bg-stone-950/20 rounded-2xl overflow-hidden border border-border/5">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="hsla(var(--primary), 0.05)" gap={20} size={1} />
        <Controls className="glass-dark border-none shadow-2xl rounded-xl overflow-hidden" />
      </ReactFlow>
    </div>
  );
}
