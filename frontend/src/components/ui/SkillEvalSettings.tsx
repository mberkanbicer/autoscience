'use client';

import { useCallback, useEffect, useState } from 'react';
import { skillsApi } from '@/lib/api';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { cn } from '@/lib/utils';
import { RefreshCw, Clock, Play, Square, AlertTriangle, CheckCircle, Loader2, Settings2 } from 'lucide-react';

interface SchedulerConfig {
  enabled: boolean;
  interval_hours: number;
  dry_run: boolean;
}

const HOUR_OPTIONS = [
  { value: 1, label: '1h' },
  { value: 2, label: '2h' },
  { value: 4, label: '4h' },
  { value: 6, label: '6h' },
  { value: 8, label: '8h' },
  { value: 12, label: '12h' },
  { value: 24, label: '24h' },
  { value: 48, label: '48h' },
  { value: 72, label: '72h' },
];

interface SkillEvalSettingsProps {
  className?: string;
}

export function SkillEvalSettings({ className }: SkillEvalSettingsProps) {
  const [config, setConfig] = useState<SchedulerConfig | null>(null);
  const [status, setStatus] = useState<{
    running: boolean;
    run_count: number;
    last_run_at: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [runningNow, setRunningNow] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configData, schedStatus] = await Promise.all([
        skillsApi.schedulerConfig(),
        skillsApi.schedulerStatus().catch(() => null),
      ]);
      setConfig(configData as unknown as SchedulerConfig);
      setStatus(schedStatus as unknown as typeof status);
    } catch (e) {
      setError('Failed to load scheduler configuration');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateConfig = async (updates: Partial<SchedulerConfig>) => {
    if (!config) return;
    setSaving(true);
    setError(null);
    try {
      const newConfig = await skillsApi.updateSchedulerConfig(updates);
      setConfig(newConfig as unknown as SchedulerConfig);
      setDirty(false);
      // Reload status after update
      try {
        const schedStatus = await skillsApi.schedulerStatus();
        setStatus(schedStatus as unknown as typeof status);
      } catch {}
    } catch (e) {
      setError('Failed to update scheduler configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = () => {
    if (!config) return;
    updateConfig({ enabled: !config.enabled });
  };

  const handleIntervalChange = (hours: number) => {
    if (!config || saving) return;
    setConfig({ ...config, interval_hours: hours });
    setDirty(true);
  };

  const handleDryRunToggle = () => {
    if (!config || saving) return;
    setConfig({ ...config, dry_run: !config.dry_run });
    setDirty(true);
  };

  const applyChanges = () => {
    if (!config) return;
    updateConfig({
      interval_hours: config.interval_hours,
      dry_run: config.dry_run,
    });
  };

  const handleRunNow = async () => {
    setRunningNow(true);
    setError(null);
    try {
      await skillsApi.evaluate({
        dry_run: config?.dry_run ?? false,
        project_id: undefined,
      });
      // Reload status after evaluation
      try {
        const schedStatus = await skillsApi.schedulerStatus();
        setStatus(schedStatus as unknown as typeof status);
      } catch {}
    } catch (e) {
      setError('Evaluation failed. Please try again.');
    } finally {
      setRunningNow(false);
    }
  };

  if (loading) {
    return (
      <Card className={cn('p-8', className)}>
        <div className="flex items-center gap-4 text-muted-foreground">
          <Loader2 size={18} className="animate-spin text-primary" />
          <span className="text-sm font-medium">Loading scheduler settings...</span>
        </div>
      </Card>
    );
  }

  const isRunning = status?.running ?? false;

  return (
    <Card className={cn('p-8', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-tertiary/10 rounded-xl">
            <Settings2 size={18} className="text-tertiary" />
          </div>
          <div>
            <h3 className="font-bold text-sm">Scheduled Evaluation</h3>
            <p className="text-[10px] text-muted-foreground/50 mt-0.5">
              Automatic skill performance evaluation on an interval
            </p>
          </div>
        </div>
        <Badge
          variant={isRunning ? 'success' : 'default'}
          className={cn(
            'text-[10px] font-black uppercase tracking-widest px-3 py-1',
            isRunning ? 'bg-success/10 text-success' : 'text-muted-foreground/40'
          )}
        >
          {isRunning ? (
            <><span className="w-1.5 h-1.5 bg-success rounded-full mr-2 animate-ping" /> Active</>
          ) : (
            <><span className="w-1.5 h-1.5 bg-muted-foreground/20 rounded-full mr-2" /> Disabled</>
          )}
        </Badge>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-error/5 border border-error/10 rounded-xl flex items-center gap-3">
          <AlertTriangle size={16} className="text-error shrink-0" />
          <p className="text-xs text-error/80 font-medium">{error}</p>
        </div>
      )}

      {/* Main toggle */}
      <div className="flex items-center justify-between p-4 bg-muted/20 rounded-xl border border-border/5 mb-6">
        <div className="flex items-center gap-3">
          {isRunning ? (
            <div className="p-2 bg-success/10 rounded-lg">
              <CheckCircle size={18} className="text-success" />
            </div>
          ) : (
            <div className="p-2 bg-muted rounded-lg">
              <Square size={18} className="text-muted-foreground/40" />
            </div>
          )}
          <div>
            <p className="text-sm font-bold">Scheduler</p>
            <p className="text-[10px] text-muted-foreground/50">
              {isRunning ? 'Running — evaluations will occur on schedule' : 'Paused — no automatic evaluations'}
            </p>
          </div>
        </div>
        <button
          onClick={handleToggle}
          disabled={saving}
          className={cn(
            'relative inline-flex h-7 w-12 shrink-0 rounded-full border-2 border-transparent transition-colors duration-300 focus-visible:outline-none disabled:opacity-50',
            config?.enabled ? 'bg-success' : 'bg-muted'
          )}
          role="switch"
          aria-checked={config?.enabled ?? false}
        >
          <span
            className={cn(
              'pointer-events-none inline-block h-6 w-6 rounded-full bg-white shadow-lg ring-0 transition-transform duration-300',
              config?.enabled ? 'translate-x-5' : 'translate-x-0'
            )}
          />
        </button>
      </div>

      {/* Interval selector */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Clock size={14} className="text-muted-foreground/40" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/40">
            Evaluation Interval
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {HOUR_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleIntervalChange(opt.value)}
              disabled={!config?.enabled || saving}
              className={cn(
                'px-4 py-2 rounded-xl text-[11px] font-bold transition-all duration-200 border',
                config?.interval_hours === opt.value
                  ? 'bg-primary/10 text-primary border-primary/20 shadow-sm'
                  : 'bg-muted/20 text-muted-foreground/60 border-border/5 hover:border-border/20 hover:text-foreground/80',
                (!config?.enabled || saving) && 'opacity-50 cursor-not-allowed'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Dry run toggle */}
      <div className="flex items-center justify-between p-4 bg-muted/20 rounded-xl border border-border/5 mb-6">
        <div className="flex items-center gap-3">
          <div className={cn(
            'p-2 rounded-lg',
            config?.dry_run ? 'bg-warning/10' : 'bg-muted'
          )}>
            <AlertTriangle size={18} className={config?.dry_run ? 'text-warning' : 'text-muted-foreground/40'} />
          </div>
          <div>
            <p className="text-sm font-bold">Dry Run Mode</p>
            <p className="text-[10px] text-muted-foreground/50">
              {config?.dry_run
                ? 'Evaluates but never mutates skill statuses — safe preview'
                : 'Skills will be deprecated/retired automatically when underperforming'}
            </p>
          </div>
        </div>
        <button
          onClick={handleDryRunToggle}
          disabled={saving}
          className={cn(
            'relative inline-flex h-7 w-12 shrink-0 rounded-full border-2 border-transparent transition-colors duration-300 focus-visible:outline-none disabled:opacity-50',
            config?.dry_run ? 'bg-warning' : 'bg-muted'
          )}
          role="switch"
          aria-checked={config?.dry_run ?? false}
        >
          <span
            className={cn(
              'pointer-events-none inline-block h-6 w-6 rounded-full bg-white shadow-lg ring-0 transition-transform duration-300',
              config?.dry_run ? 'translate-x-5' : 'translate-x-0'
            )}
          />
        </button>
      </div>

      {/* Apply button (only when dirty) */}
      {dirty && (
        <div className="mb-6 animate-in fade-in slide-in-from-top-2 duration-300">
          <Button
            variant="primary"
            size="sm"
            className="w-full rounded-xl py-5 text-[10px] font-black uppercase tracking-widest"
            onClick={applyChanges}
            disabled={saving}
          >
            {saving ? (
              <><Loader2 size={14} className="mr-2 animate-spin" /> Applying...</>
            ) : (
              <><RefreshCw size={14} className="mr-2" /> Apply Changes & Restart Scheduler</>
            )}
          </Button>
        </div>
      )}

      {/* Run now + status footer */}
      <div className="flex items-center justify-between pt-4 border-t border-border/5">
        <Button
          variant="secondary"
          size="sm"
          className={cn(
            'text-[9px] font-black uppercase tracking-widest rounded-xl px-4',
            runningNow && 'animate-pulse',
          )}
          onClick={handleRunNow}
          disabled={runningNow}
        >
          {runningNow ? (
            <><Loader2 size={12} className="mr-1.5 animate-spin" /> Running...</>
          ) : (
            <><Play size={12} className="mr-1.5" /> Run Now</>
          )}
        </Button>
        {status && (
          <div className="flex items-center gap-4 text-[10px] text-muted-foreground/40 font-mono">
            <span>Runs: {status.run_count}</span>
            <span>
              {status.last_run_at
                ? `Last: ${new Date(status.last_run_at).toLocaleString()}`
                : 'No runs yet'}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
