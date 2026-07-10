'use client';

import { useMemo, useState } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { cn } from '@/lib/utils';
import { GitBranch, Info } from 'lucide-react';

export interface ConflictHeatmapEntry {
  cluster_name: string;
  cluster_id: string;
  conflict_type: string;
  count: number;
  max_severity: number;
  avg_severity: number;
}

interface ConflictHeatmapProps {
  data: ConflictHeatmapEntry[];
  className?: string;
}

const CONFLICT_TYPE_LABELS: Record<string, string> = {
  finding: 'Finding',
  method: 'Method',
  dataset: 'Dataset',
  assumption: 'Assumption',
  scope: 'Scope',
  recency: 'Recency',
  theory_practice: 'Theory-Practice',
};

function getHeatColor(severity: number, count: number): string {
  const intensity = Math.min(severity * count, 10) / 10;
  if (intensity <= 0.2) return 'bg-stone-100 dark:bg-stone-800/60 border-stone-200/20';
  if (intensity <= 0.4) return 'bg-yellow-100 dark:bg-yellow-900/40 border-yellow-200/30';
  if (intensity <= 0.6) return 'bg-orange-100 dark:bg-orange-900/40 border-orange-200/30';
  if (intensity <= 0.8) return 'bg-red-100 dark:bg-red-900/50 border-red-200/40';
  return 'bg-red-200 dark:bg-red-800/60 border-red-300/50';
}

export function ConflictHeatmap({ data, className }: ConflictHeatmapProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  const { clusters, types, grid } = useMemo(() => {
    const clusterSet = new Set<string>();
    const typeSet = new Set<string>();
    const gridMap = new Map<string, ConflictHeatmapEntry>();

    data.forEach((entry) => {
      clusterSet.add(entry.cluster_name);
      typeSet.add(entry.conflict_type);
      gridMap.set(`${entry.cluster_id}::${entry.conflict_type}`, entry);
    });

    const clusterList = Array.from(clusterSet);
    const typeList = Array.from(typeSet).sort();

    return {
      clusters: clusterList,
      types: typeList,
      grid: gridMap,
    };
  }, [data]);

  const getEntry = (clusterId: string, clusterName: string, type: string): ConflictHeatmapEntry => {
    const entry = grid.get(`${clusterId}::${type}`);
    if (entry) return entry;
    return {
      cluster_name: clusterName,
      cluster_id: clusterId,
      conflict_type: type,
      count: 0,
      max_severity: 0,
      avg_severity: 0,
    };
  };

  const filteredClusters = selectedType
    ? clusters.filter((c) => {
        const entry = grid.get(`${c}::${selectedType}`);
        return entry && entry.count > 0;
      })
    : clusters;

  const totalConflicts = data.reduce((sum, d) => sum + d.count, 0);
  const avgSeverity = data.length > 0
    ? data.reduce((sum, d) => sum + d.avg_severity * d.count, 0) / totalConflicts
    : 0;

  if (data.length === 0) {
    return (
      <Card className={cn('p-10 text-center', className)}>
        <GitBranch size={32} className="mx-auto mb-4 text-muted-foreground/20" />
        <h3 className="text-sm font-bold text-muted-foreground mb-2">No Conflict Data</h3>
        <p className="text-xs text-muted-foreground/50 max-w-md mx-auto">
          Conflicts will appear here once literature analysis detects scientific tensions across clusters.
        </p>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-error/10 rounded-xl">
            <GitBranch size={18} className="text-error" />
          </div>
          <div>
            <h3 className="font-bold text-sm">Conflict Heatmap</h3>
            <p className="text-[10px] text-muted-foreground/50 mt-0.5">
              {totalConflicts} conflicts across {clusters.length} clusters
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground/60">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-red-200 dark:bg-red-800/60 border border-red-300/50" />
            High
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-yellow-100 dark:bg-yellow-900/40 border border-yellow-200/30" />
            Med
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-stone-100 dark:bg-stone-800/60 border border-stone-200/20" />
            Low
          </span>
        </div>
      </div>

      {/* Summary stats */}
      <div className="flex items-center gap-6 mb-6 pb-6 border-b border-border/10">
        <div>
          <span className="text-2xl font-black tracking-tighter">{totalConflicts}</span>
          <span className="text-xs text-muted-foreground ml-2">total</span>
        </div>
        <div>
          <span className="text-lg font-bold">{avgSeverity.toFixed(1)}</span>
          <span className="text-xs text-muted-foreground ml-1">avg severity</span>
        </div>
        <div>
          <span className="text-lg font-bold">{types.length}</span>
          <span className="text-xs text-muted-foreground ml-1">conflict types</span>
        </div>
        <div>
          <span className="text-lg font-bold">{clusters.length}</span>
          <span className="text-xs text-muted-foreground ml-1">clusters</span>
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[600px]">
          {/* Column headers (cluster names) */}
          <div className="flex items-stretch mb-1">
            <div className="w-[120px] shrink-0 pr-3">
              <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/30">
                Type \ Cluster
              </span>
            </div>
            {filteredClusters.map((cluster) => (
              <button
                key={cluster}
                onClick={() => setSelectedCluster(selectedCluster === cluster ? null : cluster)}
                className={cn(
                  'flex-1 text-center px-2 py-2 text-[9px] font-bold uppercase tracking-wider rounded-t-lg transition-colors truncate',
                  selectedCluster === cluster
                    ? 'text-primary bg-primary/5'
                    : 'text-muted-foreground/40 hover:text-muted-foreground/60'
                )}
                title={cluster}
              >
                {cluster.length > 14 ? cluster.slice(0, 12) + '…' : cluster}
              </button>
            ))}
          </div>

          {/* Heatmap rows */}
          {types.map((type) => (
            <div key={type} className="flex items-stretch mb-0.5">
              {/* Row header (conflict type) */}
              <button
                onClick={() => setSelectedType(selectedType === type ? null : type)}
                className={cn(
                  'w-[120px] shrink-0 flex items-center pr-3 text-[10px] font-bold uppercase tracking-wider transition-colors',
                  selectedType === type ? 'text-primary' : 'text-muted-foreground/50 hover:text-muted-foreground/70'
                )}
              >
                <div className="flex items-center gap-1.5">
                  <span className={cn(
                    'w-1.5 h-1.5 rounded-full shrink-0',
                    type === 'finding' ? 'bg-error' :
                    type === 'method' ? 'bg-tertiary' :
                    type === 'dataset' ? 'bg-warning' :
                    type === 'assumption' ? 'bg-primary' :
                    type === 'scope' ? 'bg-info' :
                    'bg-muted'
                  )} />
                  {CONFLICT_TYPE_LABELS[type] || type.replace('_', ' ')}
                </div>
              </button>

              {/* Heatmap cells */}
              {filteredClusters.map((cluster) => {
                const entry = getEntry(
                  data.find((d) => d.cluster_name === cluster)?.cluster_id || cluster,
                  cluster,
                  type
                );
                const heatClass = getHeatColor(entry.max_severity, entry.count);

                return (
                  <div
                    key={`${cluster}::${type}`}
                    className={cn(
                      'flex-1 m-0.5 rounded-lg border transition-all duration-200 cursor-default relative group',
                      heatClass,
                      entry.count === 0 && 'opacity-30'
                    )}
                    title={`${type} in ${cluster}: ${entry.count} conflicts, severity ${entry.max_severity.toFixed(1)}`}
                  >
                    <div className="flex items-center justify-center h-10 text-[10px] font-mono font-bold">
                      {entry.count > 0 ? (
                        <span className={entry.max_severity >= 0.7 ? 'text-red-800 dark:text-red-200' :
                          entry.max_severity >= 0.4 ? 'text-orange-800 dark:text-orange-200' :
                          'text-stone-600 dark:text-stone-400'}>
                          {entry.count}
                        </span>
                      ) : (
                        <span className="text-muted-foreground/20">—</span>
                      )}
                    </div>

                    {/* Tooltip on hover */}
                    {entry.count > 0 && (
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-stone-900 dark:bg-stone-100 text-white dark:text-stone-900 text-[10px] rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 whitespace-nowrap min-w-[180px]">
                        <p className="font-bold mb-1 text-xs">{CONFLICT_TYPE_LABELS[type] || type}</p>
                        <p className="opacity-80">{entry.count} conflict{entry.count !== 1 ? 's' : ''}</p>
                        <p className="opacity-80">Max severity: {(entry.max_severity * 10).toFixed(0)}%</p>
                        <p className="opacity-80">Avg severity: {(entry.avg_severity * 10).toFixed(0)}%</p>
                        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-t-stone-900 dark:border-t-stone-100 border-l-transparent border-r-transparent" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Filter active indicator */}
      {(selectedType || selectedCluster) && (
        <div className="mt-4 flex items-center justify-between p-3 bg-primary/[0.03] border border-primary/10 rounded-xl">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Info size={14} className="text-primary" />
            Filtering by
            {selectedType && <Badge variant="info" className="text-[9px]">{selectedType}</Badge>}
            {selectedCluster && <Badge variant="default" className="text-[9px]">{selectedCluster}</Badge>}
          </div>
          <button
            onClick={() => { setSelectedType(null); setSelectedCluster(null); }}
            className="text-[10px] text-primary font-bold hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Per-cluster conflict breakdown */}
      <div className="mt-6 pt-6 border-t border-border/10">
        <h4 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 mb-4">
          Conflict Breakdown by Cluster
        </h4>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredClusters.slice(0, 9).map((cluster) => {
            const clusterEntries = data.filter((d) => d.cluster_name === cluster);
            const clusterTotal = clusterEntries.reduce((s, d) => s + d.count, 0);
            const clusterSeverity = clusterEntries.length > 0
              ? clusterEntries.reduce((s, d) => s + d.avg_severity * d.count, 0) / clusterTotal
              : 0;

            return (
              <div
                key={cluster}
                className="p-3 bg-stone-50 dark:bg-stone-900/50 rounded-xl border border-border/5"
              >
                <p className="text-xs font-bold truncate mb-2" title={cluster}>{cluster}</p>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground/60">
                  <span>{clusterTotal} conflict{clusterTotal !== 1 ? 's' : ''}</span>
                  <span>{(clusterSeverity * 10).toFixed(0)}% severity</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {clusterEntries.filter((e) => e.count > 0).map((entry) => (
                    <span
                      key={entry.conflict_type}
                      className="text-[8px] px-1.5 py-0.5 rounded font-mono bg-stone-200/50 dark:bg-stone-800/50 text-muted-foreground/60"
                    >
                      {entry.conflict_type.slice(0, 4)}:{entry.count}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
