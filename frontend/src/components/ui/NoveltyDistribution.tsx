'use client';

import { useMemo } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { BarChart3, TrendingUp, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScoreEntry {
  dimension: string;
  score: number;
  weight: number;
  is_risk: boolean;
}

interface NoveltyDistributionProps {
  scores: ScoreEntry[];
  overallValue?: number;
  classification?: string;
  className?: string;
  compact?: boolean;
}

const DIMENSION_LABELS: Record<string, string> = {
  novelty: 'Novelty',
  feasibility: 'Feasibility',
  importance: 'Importance',
  evidence_support: 'Evidence',
  validation_clarity: 'Validation',
  differentiation: 'Differentiation',
  data_availability: 'Data',
  skill_leverage: 'Skills',
  user_alignment: 'Alignment',
  prior_art_risk: 'Prior Art Risk',
  safety_risk: 'Safety Risk',
  cost_risk: 'Cost Risk',
};

const DIMENSION_COLORS: Record<string, string> = {
  novelty: 'bg-primary',
  feasibility: 'bg-success',
  importance: 'bg-amber',
  evidence_support: 'bg-blue-400',
  validation_clarity: 'bg-tertiary',
  differentiation: 'bg-purple-400',
  data_availability: 'bg-cyan-400',
  skill_leverage: 'bg-pink-400',
  user_alignment: 'bg-emerald-400',
  prior_art_risk: 'bg-error',
  safety_risk: 'bg-warning',
  cost_risk: 'bg-orange-400',
};

export function NoveltyDistribution({ scores, overallValue, classification, className, compact = false }: NoveltyDistributionProps) {
  const sorted = useMemo(() =>
    [...scores].sort((a, b) => b.score - a.score),
    [scores]
  );

  const avgScore = useMemo(() =>
    scores.length > 0
      ? scores.reduce((sum, s) => sum + s.score, 0) / scores.length
      : 0,
    [scores]
  );

  if (scores.length === 0) {
    return (
      <Card className={cn('p-8 text-center', className)}>
        <BarChart3 size={24} className="text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/50">No scores available</p>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {!compact && (
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Lightbulb size={18} className="text-primary" />
            <h3 className="font-bold text-sm">Idea Scoring</h3>
          </div>
          {classification && (
            <Badge variant={
              classification === 'high_value' || classification === 'promising' ? 'success' :
              classification === 'incremental' ? 'warning' : 'danger'
            } className="text-[9px]">
              {classification.replace('_', ' ')}
            </Badge>
          )}
        </div>
      )}

      {/* Overall score */}
      {overallValue !== undefined && (
        <div className="flex items-end gap-4 mb-6 pb-6 border-b border-border/10">
          <div>
            <span className="text-5xl font-black tracking-tighter">{overallValue.toFixed(1)}</span>
            <span className="text-sm text-muted-foreground ml-2 font-medium">/ 10</span>
          </div>
          <div className="text-sm text-muted-foreground pb-1">
            Avg: {avgScore.toFixed(1)}
          </div>
          {!compact && (
            <div className="flex-1 h-2 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden self-center">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-1000',
                  overallValue >= 7 ? 'bg-success' : overallValue >= 5 ? 'bg-warning' : 'bg-error'
                )}
                style={{ width: `${overallValue * 10}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* Dimension bars */}
      <div className={cn('space-y-2', compact && 'space-y-1')}>
        {sorted.map((entry) => (
          <div key={entry.dimension} className="flex items-center gap-3">
            <span className={cn(
              'font-bold text-muted-foreground shrink-0',
              compact ? 'text-[9px] w-16' : 'text-xs w-24'
            )}>
              {DIMENSION_LABELS[entry.dimension] || entry.dimension}
            </span>
            <div className="flex-1 h-5 bg-stone-100 dark:bg-stone-800 rounded-lg overflow-hidden relative">
              <div
                className={cn(
                  'h-full rounded-lg transition-all duration-700 ease-out',
                  entry.is_risk ? 'bg-error/40' : DIMENSION_COLORS[entry.dimension] || 'bg-primary/40'
                )}
                style={{ width: `${entry.score * 10}%` }}
              />
              <span className={cn(
                'absolute inset-0 flex items-center font-mono',
                compact ? 'px-1.5 text-[9px]' : 'px-2 text-[10px]'
              )}>
                {entry.score.toFixed(1)}
              </span>
            </div>
            {!compact && (
              <span className="text-[10px] text-muted-foreground/50 w-10 text-right font-mono">
                ×{entry.weight.toFixed(2)}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      {!compact && (
        <div className="mt-4 flex items-center gap-4 text-[10px] text-muted-foreground/50">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-primary/40" />
            Positive dimensions
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded bg-error/40" />
            Risk dimensions (negative weight)
          </span>
        </div>
      )}
    </Card>
  );
}
