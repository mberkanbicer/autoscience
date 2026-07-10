'use client';

import React, { useMemo, useEffect } from 'react';
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
import { Badge } from '@/components/ui/Badge';

interface ThinkingTreeProps {
  events: any[];
}

export function ThinkingTree({ events }: ThinkingTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    // 1. Root Node: Intent
    newNodes.push({
      id: 'root',
      data: { label: 'SYNTHESIS_HUB' },
      position: { x: 250, y: 0 },
      type: 'input',
      style: { background: 'hsla(var(--primary), 0.15)', border: '2px solid hsla(var(--primary), 0.5)', borderRadius: '24px', fontSize: '9px', fontWeight: '900', color: 'hsl(var(--primary))', width: 160, backdropFilter: 'blur(12px)', letterSpacing: '0.2em', boxShadow: '0 0 30px hsla(var(--primary), 0.2)' },
    });

    let currentY = 120;
    const keywordsSeen = new Set();
    const sourcesSeen = new Set();
    const clustersSeen = new Set();
    const stepsSeen = new Set<string>();
    const thoughtsSeen = new Set<string>();
    let lastStepId: string | null = null;

    events.forEach((event) => {
      const { type, data } = event;

      if (type === 'step_started') {
        const stepId = data.step;
        if (!stepsSeen.has(stepId)) {
          const id = `step-${stepId}`;
          newNodes.push({
            id,
            data: { label: (data.label || stepId).toUpperCase() },
            position: { x: 250, y: currentY },
            style: { 
                background: 'hsla(var(--primary), 0.1)', 
                border: '2px solid hsl(var(--primary))', 
                borderRadius: '20px', 
                fontSize: '8px', 
                fontWeight: '900', 
                color: 'hsl(var(--primary))', 
                width: 150, 
                backdropFilter: 'blur(10px)',
                boxShadow: '0 0 20px hsla(var(--primary), 0.2)'
            },
          });
          
          // Connect to root if it's the first step, else to the previous step node
          const prevStepId = Array.from(stepsSeen).pop();
          newEdges.push({
            id: `e-${prevStepId ? `step-${prevStepId}` : 'root'}-${id}`,
            source: prevStepId ? `step-${prevStepId}` : 'root',
            target: id,
            animated: true,
            style: { stroke: 'hsl(var(--primary))', strokeWidth: 2 },
          });
          
          stepsSeen.add(stepId);
          lastStepId = id;
          currentY += 120;
        }
      }

      if (type === 'thinking' && data.thought) {
        const thoughtKey = data.thought.slice(0, 80);
        if (!thoughtsSeen.has(thoughtKey)) {
          const id = `thought-${thoughtsSeen.size}`;
          const parentId = lastStepId || 'root';
          const parentX = parentId === 'root' ? 250 : 250;
          newNodes.push({
            id,
            data: { label: data.thought.slice(0, 48).toUpperCase() },
            position: { x: parentX + (thoughtsSeen.size % 2 === 0 ? -180 : 180), y: currentY },
            style: {
              background: 'hsla(var(--primary), 0.08)',
              border: '1px dashed hsla(var(--primary), 0.4)',
              borderRadius: '14px',
              fontSize: '7px',
              fontWeight: '700',
              color: 'hsl(var(--primary))',
              width: 160,
              backdropFilter: 'blur(8px)',
            },
          });
          newEdges.push({
            id: `e-${parentId}-${id}`,
            source: parentId,
            target: id,
            animated: true,
            style: { stroke: 'hsla(var(--primary), 0.3)', strokeWidth: 1.5, strokeDasharray: '4 4' },
          });
          thoughtsSeen.add(thoughtKey);
          currentY += 90;
        }
      }

      if (type === 'keywords') {
        const kws = data.keywords || [];
        kws.forEach((kw: string, i: number) => {
          if (!keywordsSeen.has(kw)) {
            const id = `kw-${kw}`;
            newNodes.push({
              id,
              data: { label: kw.toUpperCase() },
              position: { x: i * 160, y: currentY },
              style: { background: 'hsla(var(--secondary), 0.05)', border: '1px solid hsla(var(--secondary), 0.3)', borderRadius: '16px', fontSize: '8px', fontWeight: '800', color: 'hsl(var(--secondary))', width: 140, backdropFilter: 'blur(8px)', letterSpacing: '0.1em' },
            });
            newEdges.push({
              id: `e-root-${id}`,
              source: 'root',
              target: id,
              animated: true,
              style: { stroke: 'hsla(var(--primary), 0.4)', strokeWidth: 3 },
            });
            keywordsSeen.add(kw);
          }
        });
        currentY += 140;
      }

      if (type === 'search_started') {
        const sources = data.sources || [];
        sources.forEach((src: string, i: number) => {
          if (!sourcesSeen.has(src)) {
            const id = `src-${src}`;
            newNodes.push({
              id,
              data: { label: `VECTOR_${src.toUpperCase()}` },
              position: { x: i * 160, y: currentY },
              style: { background: 'hsla(var(--success), 0.1)', border: '1px solid hsla(var(--success), 0.4)', borderRadius: '16px', fontSize: '8px', fontWeight: '800', color: 'hsl(var(--success))', width: 140, backdropFilter: 'blur(8px)', letterSpacing: '0.1em' },
            });
            newEdges.push({
              id: `e-src-${id}`,
              source: 'root',
              target: id,
              animated: true,
              style: { stroke: 'hsla(var(--success), 0.4)', strokeWidth: 3 },
            });
            sourcesSeen.add(src);
          }
        });
        currentY += 140;
      }

      if (type === 'papers_clustered') {
        const count = data.clusters || 0;
        for (let i = 0; i < count; i++) {
           const id = `cluster-${i}`;
           if (!clustersSeen.has(id)) {
              newNodes.push({
                id,
                data: { label: `CORE_NODE_0${i+1}` },
                position: { x: i * 160, y: currentY },
                style: { background: 'hsla(var(--tertiary), 0.1)', border: '1px solid hsla(var(--tertiary), 0.4)', borderRadius: '16px', fontSize: '8px', fontWeight: '800', color: 'hsl(var(--tertiary))', width: 140, backdropFilter: 'blur(8px)', letterSpacing: '0.1em' },
              });
              newEdges.push({
                id: `e-clust-${id}`,
                source: 'root',
                target: id,
                animated: true,
                style: { stroke: 'hsla(var(--tertiary), 0.4)', strokeWidth: 3 },
              });
              clustersSeen.add(id);
           }
        }
      }
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [events, setNodes, setEdges]);

  return (
    <div className="w-full h-96 glass rounded-3xl overflow-hidden shadow-2xl relative">
      <div className="absolute top-6 right-6 z-10">
         <Badge variant="info" className="bg-stone-900/50 px-4 py-1">REALTIME_MAP</Badge>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="hsla(var(--primary), 0.05)" gap={28} size={1} />
        <Controls className="glass-dark border-none shadow-2xl rounded-2xl overflow-hidden" />
      </ReactFlow>
    </div>
  );
}
