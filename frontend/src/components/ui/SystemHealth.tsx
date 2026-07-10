'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Sparkline } from '@/components/ui/Sparkline';
import { healthApi, connectorsApi } from '@/lib/api';
import { useToast } from '@/components/ui/toast';
import type { OverallHealth, HealthResult } from '@/lib/types';
import { useLatencyTrend } from '@/hooks/use-latency-trend';
import {
  Database,
  HardDrive,
  Cpu,
  PlugZap,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Server,
  ChevronDown,
  ChevronRight,
  Clock,
  TrendingUp,
  Unplug,
  Activity,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ── Helpers ─────────────────────────────────────────────────────────────

function statusToVariant(status: string): 'success' | 'warning' | 'danger' | 'default' | 'info' {
  switch (status) {
    case 'healthy': return 'success';
    case 'degraded': return 'warning';
    case 'unhealthy': return 'danger';
    case 'not_configured':
    case 'not_available': return 'default';
    default: return 'info';
  }
}

function statusToIcon(status: string) {
  switch (status) {
    case 'healthy': return <CheckCircle2 size={16} className="text-success" />;
    case 'degraded': return <AlertTriangle size={16} className="text-warning" />;
    case 'unhealthy': return <XCircle size={16} className="text-error" />;
    case 'not_configured':
    case 'not_available': return <HelpCircle size={16} className="text-muted-foreground/40" />;
    default: return <HelpCircle size={16} />;
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'healthy': return 'Operational';
    case 'degraded': return 'Degraded';
    case 'unhealthy': return 'Down';
    case 'not_configured': return 'Not Configured';
    case 'not_available': return 'Unavailable';
    default: return status.replace('_', ' ');
  }
}

const SERVICE_META: Record<string, { label: string; icon: typeof Database; desc: string }> = {
  database: { label: 'Database', icon: Database, desc: 'PostgreSQL connection & query execution' },
  redis: { label: 'Redis', icon: HardDrive, desc: 'Cache, Pub/Sub & session store' },
  llm: { label: 'LLM Providers', icon: Cpu, desc: 'OpenAI, Anthropic, OpenRouter, Local, llamacpp' },
  connectors: { label: 'Connectors', icon: PlugZap, desc: 'Academic search APIs (OpenAlex, Semantic Scholar, etc.)' },
};

// ── Props ───────────────────────────────────────────────────────────────

interface SystemHealthProps {
  /** Auto-polling interval in ms. Set to 0 to disable. */
  pollInterval?: number;
  /** Optional class name override. */
  className?: string;
}

// ── Component ───────────────────────────────────────────────────────────

export function SystemHealth({ pollInterval = 30000, className }: SystemHealthProps) {
  const [health, setHealth] = useState<OverallHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedConnectors, setExpandedConnectors] = useState(false);
  const [expandedTrend, setExpandedTrend] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { recordLatency, getTrend } = useLatencyTrend();
  const { addToast } = useToast();
  const prevCbStates = useRef<Record<string, string>>({});

  const fetchHealth = useCallback(async () => {
    try {
      const data = await healthApi.check();
      setHealth(data);
      setLastUpdated(new Date());
      setError(null);

      // Detect circuit-breaker transitions and fire toasts
      const connectorsResult = data.checks?.connectors;
      if (connectorsResult?.details?.per_connector) {
        const perConnector = connectorsResult.details.per_connector as Record<string, any>;
        const latencyMap: Record<string, number> = {};
        const newCbStates: Record<string, string> = {};

        for (const [name, val] of Object.entries(perConnector)) {
          // Record latency
          if (typeof val === 'object' && val !== null && typeof val.latency_ms === 'number') {
            latencyMap[name] = val.latency_ms;
          }

          // Track circuit-breaker state
          const cbState = typeof val === 'boolean' ? 'closed' : (val?.circuit_breaker ?? 'closed');
          newCbStates[name] = cbState;

          // Detect closed → open transition
          const prev = prevCbStates.current[name];
          if (prev === 'closed' && cbState === 'open') {
            addToast({
              type: 'error',
              title: `${name.replace(/_/g, ' ')} circuit opened`,
              message: `Circuit-breaker tripped after ${val?.failure_count ?? '?'} consecutive failures. Requests to this connector are suspended for ${val?.cooldown_remaining ?? '?'}s.`,
              duration: 8000,
            });
          }
        }

        // Update stored state for next poll
        prevCbStates.current = newCbStates;

        if (Object.keys(latencyMap).length > 0) {
          recordLatency(latencyMap);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch health';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [recordLatency, addToast]);

  useEffect(() => {
    fetchHealth();
    if (pollInterval > 0) {
      intervalRef.current = setInterval(fetchHealth, pollInterval);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchHealth, pollInterval]);

  if (loading) {
    return (
      <div className={cn('space-y-4', className)}>
        <div className="flex items-center gap-3 mb-6">
          <Skeleton className="h-8 w-48 rounded-lg" />
          <Skeleton className="h-6 w-24 rounded-full" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <Card className={cn('p-10 text-center border-error/20 bg-error/5', className)}>
        <XCircle size={40} className="mx-auto mb-4 text-error" />
        <h3 className="text-lg font-bold text-foreground mb-2">Health Check Failed</h3>
        <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">{error}</p>
        <Button variant="secondary" size="sm" onClick={fetchHealth}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Retry
        </Button>
      </Card>
    );
  }

  if (!health) return null;

  const services = Object.entries(health.checks) as [string, HealthResult][];
  const trendData = getTrend();

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall status bar */}
      <div
        className={cn(
          'flex items-center justify-between p-5 rounded-2xl border backdrop-blur-sm transition-all duration-500',
          health.status === 'healthy'
            ? 'bg-success/5 border-success/20'
            : health.status === 'unhealthy'
              ? 'bg-error/5 border-error/20'
              : 'bg-warning/5 border-warning/20',
        )}
      >
        <div className="flex items-center gap-4">
          <div
            className={cn(
              'p-2.5 rounded-xl',
              health.status === 'healthy'
                ? 'bg-success/10'
                : health.status === 'unhealthy'
                  ? 'bg-error/10'
                  : 'bg-warning/10',
            )}
          >
            {health.status === 'healthy' ? (
              <CheckCircle2 size={22} className="text-success" />
            ) : health.status === 'unhealthy' ? (
              <XCircle size={22} className="text-error" />
            ) : (
              <AlertTriangle size={22} className="text-warning" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-base font-black text-foreground tracking-tight">
                System Status
              </h3>
              <Badge variant={statusToVariant(health.status)} size="md">
                {statusLabel(health.status)}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground font-medium mt-0.5">
              {health.status === 'healthy'
                ? 'All services are operational.'
                : health.status === 'unhealthy'
                  ? 'One or more services are down.'
                  : 'Some services are degraded or not configured.'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <div className="hidden sm:flex items-center gap-1.5 text-[9px] font-bold text-muted-foreground/50 uppercase tracking-wider">
              <Clock size={12} />
              <span>{lastUpdated.toLocaleTimeString()}</span>
            </div>
          )}
          <Button variant="ghost" size="sm" onClick={fetchHealth} className="shrink-0">
            <RefreshCw className="h-3.5 w-3.5 mr-1" /> Refresh
          </Button>
        </div>
      </div>

      {/* Service cards grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {services.map(([key, result]) => {
          const meta = SERVICE_META[key] ?? {
            label: key,
            icon: Server,
            desc: '',
          };
          const Icon = meta.icon;
          const isConnectors = key === 'connectors';
          const perConnector = result.details?.per_connector as Record<string, any> | undefined;
          const providerDetails = result.details?.providers as Record<string, { configured: boolean; default_model?: string }> | undefined;

          return (
            <Card
              key={key}
              className={cn(
                'p-5 border-border/5 transition-all duration-300 hover:shadow-lg',
                result.status === 'unhealthy' && 'border-error/20 bg-error/[0.02]',
                result.status === 'degraded' && 'border-warning/20 bg-warning/[0.02]',
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'p-2.5 rounded-xl',
                      result.status === 'healthy'
                        ? 'bg-success/10'
                        : result.status === 'unhealthy'
                          ? 'bg-error/10'
                          : result.status === 'degraded'
                            ? 'bg-warning/10'
                            : 'bg-muted',
                    )}
                  >
                    <Icon
                      size={18}
                      className={
                        result.status === 'healthy'
                          ? 'text-success'
                          : result.status === 'unhealthy'
                            ? 'text-error'
                            : result.status === 'degraded'
                              ? 'text-warning'
                              : 'text-muted-foreground/40'
                      }
                    />
                  </div>
                  <div>
                    <h4 className="text-sm font-black text-foreground">{meta.label}</h4>
                    <p className="text-[9px] text-muted-foreground/60 font-medium mt-0.5">{meta.desc}</p>
                  </div>
                </div>
                <Badge variant={statusToVariant(result.status)} size="sm">
                  {statusLabel(result.status)}
                </Badge>
              </div>

              {/* Connector-specific per-service breakdown */}
              {isConnectors && perConnector && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => setExpandedConnectors(!expandedConnectors)}
                    className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-muted-foreground/60 hover:text-foreground transition-colors mb-2"
                  >
                    {expandedConnectors ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Per-Connector Status ({Object.keys(perConnector).length})
                  </button>

                  {/* Average latency badge */}
                  {(result.details?.avg_latency_ms as number | undefined) && (
                    <div className="flex items-center gap-2 mb-2.5 px-1">
                      <div
                        className={cn(
                          'flex items-center gap-1.5 px-2 py-1 rounded-lg text-[9px] font-bold uppercase tracking-widest',
                          (result.details?.avg_latency_ms as number) < 300
                            ? 'bg-success/10 text-success'
                            : (result.details?.avg_latency_ms as number) < 1000
                              ? 'bg-warning/10 text-warning'
                              : 'bg-error/10 text-error',
                        )}
                      >
                        <Clock size={10} />
                        Avg {(result.details?.avg_latency_ms as number).toFixed(0)}ms
                      </div>

                      {/* Overall trend sparkline (all connectors aggregated) */}
                      <TrendingUp size={10} className="text-muted-foreground/40" />
                    </div>
                  )}

                  {expandedConnectors && (
                    <div className="space-y-1.5 animate-in slide-in-from-top-2 duration-200">
                      {Object.entries(perConnector).map(([name, val]) => {
                        // Support both dict format (online + latency_ms + circuit_breaker) and legacy boolean
                        const isOnline = typeof val === 'boolean' ? val : val?.online === true;
                        const latencyMs = typeof val === 'boolean' ? null : (val?.latency_ms as number | null);
                        const cbState: string | undefined = typeof val === 'boolean' ? undefined : val?.circuit_breaker;
                        const cbFailures: number = typeof val === 'boolean' ? 0 : (val?.failure_count as number) ?? 0;
                        const cbCooldown: number = typeof val === 'boolean' ? 0 : (val?.cooldown_remaining as number) ?? 0;
                        const connectorTrend = trendData[name] ?? [];

                        return (
                          <div
                            key={name}
                            className="flex items-center justify-between px-3 py-2.5 rounded-xl bg-stone-50 dark:bg-stone-900/50 border border-border/5"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="text-xs font-bold text-foreground capitalize truncate">
                                {name.replace(/_/g, ' ')}
                              </span>
                              {/* Circuit-breaker indicator */}
                              {cbState && cbState !== 'closed' && (
                                <div
                                  className={cn(
                                    'flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[7px] font-black uppercase tracking-wider shrink-0',
                                    cbState === 'open'
                                      ? 'bg-error/10 text-error'
                                      : 'bg-warning/10 text-warning',
                                  )}
                                  title={
                                    cbState === 'open'
                                      ? `Circuit OPEN — ${cbFailures} failures, ${cbCooldown.toFixed(0)}s cooldown remaining`
                                      : `Circuit HALF-OPEN — ${cbFailures} failures, recovering`
                                  }
                                >
                                  {cbState === 'open' ? (
                                    <Unplug size={8} />
                                  ) : (
                                    <Activity size={8} />
                                  )}
                                  {cbState === 'open' ? 'Open' : 'Half-Open'}
                                </div>
                              )}
                              {/* Closed circuit — subtle badge */}
                              {cbState === 'closed' && cbFailures > 0 && (
                                <div
                                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[7px] font-black uppercase tracking-wider text-success/60 bg-success/5 shrink-0"
                                  title={`Closed — ${cbFailures} recent failure(s), circuit normal`}
                                >
                                  <Zap size={8} />
                                  {cbFailures}f
                                </div>
                              )}
                              {/* Circuit reset button — only shown for open/half-open */}
                              {cbState && cbState !== 'closed' && (
                                <button
                                  type="button"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    try {
                                      await connectorsApi.resetCircuit(name);
                                      fetchHealth();
                                    } catch {
                                      // Error already emitted by request()
                                    }
                                  }}
                                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[7px] font-black uppercase tracking-wider shrink-0 bg-stone-200/50 dark:bg-stone-700/50 text-muted-foreground/70 hover:text-foreground hover:bg-stone-200 dark:hover:bg-stone-700 transition-colors"
                                  title="Clear circuit-breaker state and allow requests"
                                >
                                  <RefreshCw size={8} />
                                  Clear
                                </button>
                              )}
                              {/* Latency sparkline */}
                              {connectorTrend.length > 0 && (
                                <Sparkline
                                  data={connectorTrend}
                                  width={52}
                                  height={18}
                                  showValue={false}
                                />
                              )}
                              {/* Latency indicator bar */}
                              {latencyMs !== null && (
                                <div className="flex items-center gap-1.5">
                                  <div className="w-12 h-1.5 rounded-full bg-stone-200 dark:bg-stone-700 overflow-hidden">
                                    <div
                                      className={cn(
                                        'h-full rounded-full transition-all duration-500',
                                        latencyMs < 300
                                          ? 'bg-success'
                                          : latencyMs < 1000
                                            ? 'bg-warning'
                                            : 'bg-error',
                                      )}
                                      style={{
                                        width: `${Math.min(100, (latencyMs / 2000) * 100)}%`,
                                      }}
                                    />
                                  </div>
                                  <span className={cn(
                                    'text-[8px] font-bold tabular-nums',
                                    latencyMs < 300
                                      ? 'text-success/70'
                                      : latencyMs < 1000
                                        ? 'text-warning/70'
                                        : 'text-error/70',
                                  )}>
                                    {latencyMs.toFixed(0)}ms
                                  </span>
                                </div>
                              )}
                            </div>
                            {isOnline ? (
                              <span className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-success shrink-0">
                                <CheckCircle2 size={10} />
                                Online
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-error shrink-0">
                                <XCircle size={10} />
                                Offline
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* LLM provider breakdown */}
              {key === 'llm' && providerDetails && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {Object.entries(providerDetails).map(([name, config]) => (
                    <Badge
                      key={name}
                      variant={config.configured ? 'success' : 'default'}
                      size="sm"
                      className="text-[8px]"
                    >
                      {name}
                      {config.configured && config.default_model
                        ? ` (${config.default_model})`
                        : ''}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Redis version */}
              {key === 'redis' && result.details?.redis_version && (
                <div className="flex items-center gap-2 mt-3 text-[10px] font-bold text-muted-foreground/60">
                  <Server size={12} />
                  v{result.details.redis_version}
                </div>
              )}

              {/* Error */}
              {result.error && (
                <p className="mt-3 text-[10px] font-medium text-error/80 bg-error/5 rounded-xl px-3 py-2 border border-error/10">
                  {result.error.slice(0, 200)}
                </p>
              )}
            </Card>
          );
        })}
      </div>

      {/* Latency trend section */}
      {Object.keys(trendData).length > 0 && (
        <Card className="p-5 border-border/5">
          <button
            type="button"
            onClick={() => setExpandedTrend(!expandedTrend)}
            className="flex items-center justify-between w-full text-left"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-indigo-500/10">
                <TrendingUp size={16} className="text-indigo-500" />
              </div>
              <div>
                <h4 className="text-sm font-black text-foreground">Latency Trends</h4>
                <p className="text-[9px] text-muted-foreground/60 font-medium mt-0.5">
                  Last {Math.max(...Object.values(trendData).map((p) => p.length), 0)} polls
                  &middot; Persisted in browser
                </p>
              </div>
            </div>
            {expandedTrend ? <ChevronDown size={16} className="text-muted-foreground/40" /> : <ChevronRight size={16} className="text-muted-foreground/40" />}
          </button>

          {expandedTrend && (
            <div className="mt-4 space-y-2 animate-in slide-in-from-top-2 duration-200">
              {Object.entries(trendData).map(([name, points]) => {
                if (points.length < 2) return null;
                const avg = points.reduce((s, p) => s + p.v, 0) / points.length;
                return (
                  <div
                    key={name}
                    className="flex items-center justify-between px-3 py-2.5 rounded-xl bg-stone-50 dark:bg-stone-900/50 border border-border/5"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-xs font-bold text-foreground capitalize truncate shrink-0">
                        {name.replace(/_/g, ' ')}
                      </span>
                      <Sparkline
                        data={points}
                        width={100}
                        height={22}
                        showValue={false}
                      />
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[8px] font-bold tabular-nums text-muted-foreground/50">
                        {points.length} pts
                      </span>
                      <span
                        className={cn(
                          'text-[9px] font-bold tabular-nums',
                          avg < 300
                            ? 'text-success'
                            : avg < 1000
                              ? 'text-warning'
                              : 'text-error',
                        )}
                      >
                        avg {avg.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
