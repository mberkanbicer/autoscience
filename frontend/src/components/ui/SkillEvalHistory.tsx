'use client';

import { useCallback, useEffect, useState } from 'react';
import { skillsApi } from '@/lib/api';
import type { SkillEvalHistoryEntry } from '@/lib/types';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { cn } from '@/lib/utils';
import {
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Loader2,
  History,
  Calendar,
  BarChart3,
} from 'lucide-react';

interface SkillEvalHistoryProps {
  className?: string;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function SkillEvalHistory({ className }: SkillEvalHistoryProps) {
  const [entries, setEntries] = useState<SkillEvalHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await skillsApi.evalHistory({ limit: 50 });
      setEntries(data);
    } catch (e) {
      setError('Failed to load evaluation history');
      console.error('Failed to load evaluation history:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <Card className={cn('p-8', className)}>
        <div className="flex items-center gap-4 text-muted-foreground">
          <Loader2 size={18} className="animate-spin text-primary" />
          <span className="text-sm font-medium">Loading evaluation history...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('p-8', className)}>
        <div className="flex flex-col items-center gap-3 text-center">
          <ShieldAlert size={24} className="text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground/60">{error}</p>
          <Button variant="ghost" size="sm" onClick={load}>
            <RefreshCw size={12} className="mr-2" /> Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-info/10 rounded-xl">
            <History size={18} className="text-info" />
          </div>
          <div>
            <h3 className="font-bold text-sm">Evaluation History</h3>
            <p className="text-[10px] text-muted-foreground/50 mt-0.5">
              Past scheduled evaluation events
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {entries.length > 0 && (
            <Badge variant="info" className="text-[8px] bg-info/5">
              {entries.length} events
            </Badge>
          )}
          <Button variant="ghost" size="sm" onClick={load} className="text-[10px]">
            <RefreshCw size={12} className="mr-1.5" /> Refresh
          </Button>
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="p-4 rounded-full bg-muted/20 mb-4">
            <Calendar size={28} className="text-muted-foreground/20" />
          </div>
          <p className="text-sm font-bold text-muted-foreground/60 mb-1">No evaluations yet</p>
          <p className="text-[10px] text-muted-foreground/40 max-w-xs">
            Scheduled evaluation events will appear here after the first run. Use the scheduler
            settings above to start automatic evaluations.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => {
            const details = entry.details || {};
            const evaluated = details.evaluated_count ?? 0;
            const deprecated = details.deprecated_count ?? 0;
            const retired = details.retired_count ?? 0;
            const errors = details.error_count ?? 0;
            const dryRun = details.dry_run ?? false;
            const isExpanded = expandedId === entry.id;
            const hasChanges = deprecated > 0 || retired > 0;
            const hasErrors = errors > 0;

            return (
              <button
                key={entry.id}
                onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                className={cn(
                  'w-full text-left p-4 rounded-xl border transition-all duration-200',
                  hasErrors
                    ? 'bg-error/[0.03] border-error/10 hover:border-error/20'
                    : hasChanges
                      ? 'bg-warning/[0.03] border-warning/10 hover:border-warning/20'
                      : 'bg-muted/10 border-border/5 hover:border-border/15',
                )}
              >
                {/* Summary row */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2.5 text-xs font-medium text-muted-foreground/70">
                    <Clock size={12} className="shrink-0" />
                    <span>{formatTimestamp(entry.timestamp)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {dryRun && (
                      <Badge variant="warning" className="text-[7px] font-black uppercase tracking-widest px-1.5 py-0">
                        DRY RUN
                      </Badge>
                    )}
                    {hasErrors && (
                      <Badge variant="danger" className="text-[7px] font-black uppercase tracking-widest px-1.5 py-0">
                        ERRORS
                      </Badge>
                    )}
                    <Badge
                      variant={hasChanges ? 'warning' : 'success'}
                      size="sm"
                      className="text-[7px] font-black uppercase tracking-widest px-1.5 py-0"
                    >
                      {evaluated} evaluated
                    </Badge>
                  </div>
                </div>

                {/* Main stats row */}
                <div className="grid grid-cols-4 gap-3 mb-2">
                  <div className="flex items-center gap-1.5">
                    <BarChart3 size={12} className="text-muted-foreground/30 shrink-0" />
                    <span className="text-[11px] font-bold">{evaluated}</span>
                    <span className="text-[8px] text-muted-foreground/40 uppercase tracking-widest font-bold">eval</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle size={12} className={deprecated > 0 ? 'text-warning' : 'text-muted-foreground/20'} />
                    <span className={cn('text-[11px] font-bold', deprecated > 0 && 'text-warning')}>
                      {deprecated}
                    </span>
                    <span className="text-[8px] text-muted-foreground/40 uppercase tracking-widest font-bold">depr</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert size={12} className={retired > 0 ? 'text-danger' : 'text-muted-foreground/20'} />
                    <span className={cn('text-[11px] font-bold', retired > 0 && 'text-danger')}>
                      {retired}
                    </span>
                    <span className="text-[8px] text-muted-foreground/40 uppercase tracking-widest font-bold">retir</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 size={12} className={hasChanges ? 'text-muted-foreground/20' : 'text-success'} />
                    {hasErrors ? (
                      <span className={cn('text-[11px] font-bold', 'text-danger')}>{errors}</span>
                    ) : hasChanges ? (
                      <span className="text-[11px] font-bold text-warning/50">⨯</span>
                    ) : (
                      <span className="text-[11px] font-bold text-success">✓</span>
                    )}
                    <span className="text-[8px] text-muted-foreground/40 uppercase tracking-widest font-bold">
                      {hasErrors ? 'err' : 'ok'}
                    </span>
                  </div>
                </div>

                {/* Summary text */}
                {details.summary && (
                  <p className={cn(
                    'text-[10px] leading-relaxed',
                    isExpanded ? '' : 'line-clamp-1',
                    hasErrors ? 'text-error/70' : 'text-muted-foreground/60',
                  )}>
                    {details.summary}
                  </p>
                )}

                {/* Expanded details */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-border/5 animate-in fade-in slide-in-from-top-1 duration-200">
                    <div className="grid grid-cols-2 gap-2 text-[9px] font-mono text-muted-foreground/50">
                      <div>evaluated_count: <span className="text-foreground/70 font-bold">{evaluated}</span></div>
                      <div>deprecated_count: <span className={deprecated > 0 ? 'text-warning font-bold' : 'text-foreground/70 font-bold'}>{deprecated}</span></div>
                      <div>retired_count: <span className={retired > 0 ? 'text-danger font-bold' : 'text-foreground/70 font-bold'}>{retired}</span></div>
                      <div>error_count: <span className={hasErrors ? 'text-danger font-bold' : 'text-foreground/70 font-bold'}>{errors}</span></div>
                      <div>dry_run: <span className={dryRun ? 'text-warning font-bold' : 'text-foreground/70 font-bold'}>{String(dryRun)}</span></div>
                      <div>id: <span className="text-foreground/40">{entry.id.slice(0, 8)}...</span></div>
                    </div>
                    {entry.action && (
                      <p className="mt-2 text-[9px] text-muted-foreground/40 italic leading-relaxed">
                        {entry.action}
                      </p>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </Card>
  );
}
