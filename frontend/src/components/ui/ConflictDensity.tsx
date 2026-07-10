'use client';

import { useMemo } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { GitBranch, AlertTriangle, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConflictData {
  total: number;
  by_type: Record<string, number>;
  severity_avg: number;
  trend?: 'increasing' | 'decreasing' | 'stable';
  type_distribution?: { type: string; count: number; percentage: number }[];
}

interface ConflictDensityProps {
  data: ConflictData;
  className?: string;
}

const CONFLICT_COLORS: Record<string, string> = {
  finding: 'bg-error/10 text-error border-error/20',
  method: 'bg-tertiary/10 text-tertiary border-tertiary/20',
  dataset: 'bg-warning/10 text-warning border-warning/20',
  assumption: 'bg-primary/10 text-primary border-primary/20',
  scope: 'bg-info/10 text-info border-info/20',
  recency: 'bg-success/10 text-success border-success/20',
  theory_practice: 'bg-stone-100 text-stone-700 border-stone-300',
};

const TREND_ICONS = {
  increasing: <ArrowUp size={14} className="text-error" />,
  decreasing: <ArrowDown size={14} className="text-success" />,
  stable: <Minus size={14} className="text-muted-foreground" />,
};

export function ConflictDensity({ data, className }: ConflictDensityProps) {
  const maxCount = useMemo(() => {
    const counts = Object.values(data.by_type);
    return counts.length > 0 ? Math.max(...counts) : 1;
  }, [data.by_type]);

  const entries = useMemo(() =>
    Object.entries(data.by_type)
      .sort(([, a], [, b]) => b - a),
    [data.by_type]
  );

  const densityLevel = data.total <= 2 ? 'low' : data.total <= 6 ? 'moderate' : 'high';

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <GitBranch size={18} className={cn(
            densityLevel === 'high' ? 'text-error' : densityLevel === 'moderate' ? 'text-warning' : 'text-success'
          )} />
          <h3 className="font-bold text-sm">Conflict Density</h3>
        </div>
        <div className="flex items-center gap-3">
          {data.trend && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              {TREND_ICONS[data.trend]}
              {data.trend}
            </span>
          )}
          <Badge variant={
            densityLevel === 'high' ? 'danger' :
            densityLevel === 'moderate' ? 'warning' : 'success'
          } className="text-[9px]">
            {densityLevel}
          </Badge>
        </div>
      </div>

      {/* Main metric */}
      <div className="flex items-end gap-4 mb-6">
        <div>
          <span className="text-4xl font-black tracking-tighter">{data.total}</span>
          <span className="text-sm text-muted-foreground ml-2 font-medium">total conflicts</span>
        </div>
        <div className="text-sm text-muted-foreground">
          Avg severity: {data.severity_avg.toFixed(1)}/10
        </div>
      </div>

      {/* Severity bar */}
      <div className="mb-6">
        <div className="flex justify-between text-[10px] text-muted-foreground/50 mb-1">
          <span>Conflict Severity Distribution</span>
          <span>{data.severity_avg.toFixed(1)} avg</span>
        </div>
        <div className="h-3 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden flex">
          <div className="h-full bg-success/50 rounded-l-full" style={{ width: `${Math.min(data.severity_avg * 10, 33)}%` }} />
          <div className="h-full bg-warning/50" style={{ width: `${Math.min(Math.max(data.severity_avg * 10 - 33, 0), 33)}%` }} />
          <div className="h-full bg-error/50 rounded-r-full" style={{ width: `${Math.min(Math.max(data.severity_avg * 10 - 66, 0), 34)}%` }} />
        </div>
        <div className="flex justify-between text-[9px] text-muted-foreground/30 mt-1">
          <span>Low</span>
          <span>Medium</span>
          <span>High</span>
        </div>
      </div>

      {/* Type breakdown */}
      <div className="space-y-2">
        {entries.map(([type, count]) => (
          <div key={type} className="flex items-center gap-3">
            <Badge variant="default" className={cn('text-[9px]', CONFLICT_COLORS[type] || 'bg-muted/30')}>
              {type.replace('_', ' ')}
            </Badge>
            <div className="flex-1 h-5 bg-stone-100 dark:bg-stone-800 rounded-lg overflow-hidden relative">
              <div
                className="h-full bg-primary/30 rounded-lg transition-all duration-500"
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
              <span className="absolute inset-0 flex items-center px-2 text-[10px] font-bold text-muted-foreground/50">
                {count}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Warning if high density */}
      {densityLevel === 'high' && (
        <div className="mt-4 p-3 bg-error/[0.05] border border-error/10 rounded-xl flex items-start gap-2">
          <AlertTriangle size={14} className="text-error mt-0.5 shrink-0" />
          <p className="text-xs text-error/80">
            High conflict density detected. Consider narrowing research scope or resolving key tensions before proceeding.
          </p>
        </div>
      )}
    </Card>
  );
}
