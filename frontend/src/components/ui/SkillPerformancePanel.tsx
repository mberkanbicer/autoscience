'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card } from './Card';
import { Button } from './Button';
import { Badge } from './Badge';
import { cn } from '@/lib/utils';
import { skillsApi } from '@/lib/api';
import type { SkillPerformanceStats, SkillEvaluateResult } from '@/lib/types';
import {
  BarChart3,
  Activity,
  AlertTriangle,
  Brain,
  Zap,
  RefreshCw,
  ShieldAlert,
  Timer,
  CheckCircle2,
  Loader2,
  Play,
} from 'lucide-react';

interface SkillPerformancePanelProps {
  projectId?: string;
  className?: string;
  onEvaluationComplete?: () => void;
}

export function SkillPerformancePanel({
  projectId,
  className,
  onEvaluationComplete,
}: SkillPerformancePanelProps) {
  const [stats, setStats] = useState<SkillPerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<SkillEvaluateResult | null>(null);
  const [lastResult, setLastResult] = useState<SkillEvaluateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    try {
      const data = await skillsApi.performanceStats(projectId);
      setStats(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load skill performance stats:', err);
      setError('Could not load performance data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handlePreview = async () => {
    setEvaluating(true);
    setDryRunResult(null);
    setLastResult(null);
    setError(null);

    try {
      const result = await skillsApi.evaluate({
        dry_run: true,
        project_id: projectId,
      });
      setDryRunResult(result);
    } catch (err) {
      console.error('Skill evaluation preview failed:', err);
      setError('Preview failed. Please try again.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleExecute = async () => {
    setEvaluating(true);
    setError(null);

    try {
      const result = await skillsApi.evaluate({
        dry_run: false,
        project_id: projectId,
      });
      setLastResult(result);
      setDryRunResult(null);

      // Reload stats after evaluation
      await loadStats();
      onEvaluationComplete?.();
    } catch (err) {
      console.error('Skill evaluation execution failed:', err);
      setError('Execution failed. Please try again.');
    } finally {
      setEvaluating(false);
    }
  };

  const handleDismiss = () => {
    setDryRunResult(null);
    setLastResult(null);
  };

  const atRiskPercent = stats && stats.total_skills_evaluated > 0
    ? Math.round((stats.at_risk_count / stats.total_skills_evaluated) * 100)
    : 0;

  if (loading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center justify-center h-32">
          <Loader2 size={20} className="animate-spin text-muted-foreground/50" />
        </div>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card className={cn('p-6 text-center', className)}>
        <ShieldAlert size={24} className="text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/50">{error || 'No data available'}</p>
        <Button variant="ghost" size="sm" className="mt-4" onClick={loadStats}>
          <RefreshCw size={12} className="mr-2" /> Retry
        </Button>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-primary" />
          <h3 className="font-bold text-sm">Skill Performance Monitor</h3>
        </div>
        <div className="flex items-center gap-2">
          {atRiskPercent > 30 && (
            <Badge variant="warning" className="text-[8px]">
              {stats.at_risk_count} at risk
            </Badge>
          )}
          {!dryRunResult && !lastResult && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handlePreview}
              disabled={evaluating}
              className={cn(
                'text-[10px] font-black uppercase tracking-widest px-4',
                evaluating && 'animate-pulse',
              )}
            >
              {evaluating ? (
                <>
                  <Loader2 size={12} className="mr-1.5 animate-spin" />
                  Evaluating
                </>
              ) : (
                <>
                  <Activity size={12} className="mr-1.5" />
                  Evaluate All
                </>
              )}
            </Button>
          )}
          {(dryRunResult || lastResult) && (
            <Button variant="ghost" size="sm" onClick={handleDismiss} className="text-[10px]">
              Dismiss
            </Button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-stone-50 dark:bg-stone-900 rounded-xl">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-2">
            <Brain size={12} /> Evaluated
          </div>
          <div className="text-2xl font-black">{stats.total_skills_evaluated}</div>
        </div>
        <div className="p-3 bg-stone-50 dark:bg-stone-900 rounded-xl">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-2">
            <Zap size={12} /> Total Uses
          </div>
          <div className="text-2xl font-black">{stats.total_usage}</div>
        </div>
        <div className="p-3 bg-success/[0.05] rounded-xl">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-2">
            <CheckCircle2 size={12} /> Success Rate
          </div>
          <div className="text-2xl font-black text-success">
            {Math.round(stats.avg_success_rate * 100)}%
          </div>
        </div>
        <div className={cn(
          'p-3 rounded-xl',
          stats.at_risk_count > 0 ? 'bg-error/[0.05]' : 'bg-stone-50 dark:bg-stone-900',
        )}>
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-2">
            <AlertTriangle size={12} /> At Risk
          </div>
          <div className={cn(
            'text-2xl font-black',
            stats.at_risk_count > 0 ? 'text-error' : 'text-muted-foreground',
          )}>
            {stats.at_risk_count}
          </div>
        </div>
      </div>

      {/* Threshold info */}
      <div className="flex flex-wrap gap-2 mb-6">
        <Badge variant="default" className="bg-stone-100 dark:bg-stone-900 text-[8px] font-bold uppercase tracking-widest">
          <Timer size={10} className="mr-1" />
          Min uses: {stats.min_usage_for_evaluation}
        </Badge>
        <Badge variant="default" className="bg-stone-100 dark:bg-stone-900 text-[8px] font-bold uppercase tracking-widest">
          <CheckCircle2 size={10} className="mr-1" />
          Min SR: {Math.round(stats.min_success_rate_threshold * 100)}%
        </Badge>
        <Badge variant="default" className="bg-stone-100 dark:bg-stone-900 text-[8px] font-bold uppercase tracking-widest">
          <Timer size={10} className="mr-1" />
          Grace: {stats.deprecated_grace_days}d
        </Badge>
      </div>

      {/* Dry Run Result — requires user to confirm execution */}
      {dryRunResult && (
        <div className="p-4 rounded-xl border bg-warning/[0.05] border-warning/20">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-warning" />
              <span className="text-[10px] font-black uppercase tracking-widest">Preview</span>
            </div>
            <Badge variant="warning" className="text-[8px]">
              {dryRunResult.evaluated_count} evaluated
            </Badge>
          </div>

          <p className="text-xs text-muted-foreground mb-3">{dryRunResult.summary}</p>

          {dryRunResult.deprecated.length > 0 && (
            <div className="mb-2">
              <span className="text-[9px] font-black text-warning uppercase tracking-widest">
                Will deprecate ({dryRunResult.deprecated.length})
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {dryRunResult.deprecated.map((name, i) => (
                  <Badge key={i} variant="warning" size="sm" className="text-[9px]">
                    {name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {dryRunResult.retired.length > 0 && (
            <div className="mb-2">
              <span className="text-[9px] font-black text-danger uppercase tracking-widest">
                Will retire ({dryRunResult.retired.length})
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {dryRunResult.retired.map((name, i) => (
                  <Badge key={i} variant="danger" size="sm" className="text-[9px]">
                    {name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {dryRunResult.errors.length > 0 && (
            <div className="mt-2">
              <span className="text-[9px] font-black text-danger uppercase tracking-widest">
                Errors ({dryRunResult.errors.length})
              </span>
              <ul className="mt-1 space-y-0.5">
                {dryRunResult.errors.map((err, i) => (
                  <li key={i} className="text-[10px] text-muted-foreground/70 line-clamp-1">
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-warning/10 flex items-center gap-3">
            {dryRunResult.deprecated.length > 0 || dryRunResult.retired.length > 0 ? (
              <Button
                variant="danger"
                size="sm"
                onClick={handleExecute}
                disabled={evaluating}
                className="text-[10px] font-black uppercase tracking-widest"
              >
                {evaluating ? (
                  <>
                    <Loader2 size={12} className="mr-1.5 animate-spin" />
                    Applying
                  </>
                ) : (
                  <>
                    <Play size={12} className="mr-1.5" />
                    Execute Changes
                  </>
                )}
              </Button>
            ) : (
              <span className="text-xs text-muted-foreground/70 font-medium">
                No changes needed — all skills performing adequately
              </span>
            )}
            <span className="text-[9px] text-muted-foreground/50 font-medium">
              {dryRunResult.deprecated.length > 0 || dryRunResult.retired.length > 0
                ? 'Preview only — no changes made yet'
                : 'Dry run completed'}
            </span>
          </div>
        </div>
      )}

      {/* Final Result — after execution */}
      {lastResult && (
        <div className={cn(
          'p-4 rounded-xl border',
          lastResult.deprecated.length > 0 || lastResult.retired.length > 0
            ? 'bg-info/[0.05] border-info/20'
            : 'bg-success/[0.05] border-success/20',
        )}>
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={14} className="text-success" />
              <span className="text-[10px] font-black uppercase tracking-widest">Evaluation Complete</span>
            </div>
            <Badge variant="info" className="text-[8px]">
              {lastResult.evaluated_count} evaluated
            </Badge>
          </div>

          <p className="text-xs text-muted-foreground mb-3">{lastResult.summary}</p>

          {lastResult.deprecated.length > 0 && (
            <div className="mb-2">
              <span className="text-[9px] font-black text-warning uppercase tracking-widest">
                Deprecated ({lastResult.deprecated.length})
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {lastResult.deprecated.map((name, i) => (
                  <Badge key={i} variant="warning" size="sm" className="text-[9px]">
                    {name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {lastResult.retired.length > 0 && (
            <div className="mb-2">
              <span className="text-[9px] font-black text-danger uppercase tracking-widest">
                Retired ({lastResult.retired.length})
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {lastResult.retired.map((name, i) => (
                  <Badge key={i} variant="danger" size="sm" className="text-[9px]">
                    {name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {lastResult.errors.length > 0 && (
            <div className="mt-2">
              <span className="text-[9px] font-black text-danger uppercase tracking-widest">
                Errors ({lastResult.errors.length})
              </span>
              <ul className="mt-1 space-y-0.5">
                {lastResult.errors.map((err, i) => (
                  <li key={i} className="text-[10px] text-muted-foreground/70 line-clamp-1">
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border/5">
            <span className="text-[9px] text-muted-foreground/50 font-medium">
              Changes applied
            </span>
            {onEvaluationComplete && (
              <Button variant="ghost" size="sm" className="text-[9px]" onClick={onEvaluationComplete}>
                <RefreshCw size={10} className="mr-1" /> Reload skills
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-3 rounded-xl bg-error/[0.05] border border-error/20 text-center">
          <p className="text-xs text-error font-medium">{error}</p>
          <Button variant="ghost" size="sm" className="mt-2" onClick={handlePreview}>
            <RefreshCw size={10} className="mr-1" /> Try again
          </Button>
        </div>
      )}
    </Card>
  );
}
