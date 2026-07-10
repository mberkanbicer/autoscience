'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from 'recharts';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { cn } from '@/lib/utils';
import { skillsApi } from '@/lib/api';
import type { PerformanceHistoryEntry } from '@/lib/types';
import {
  TrendingUp,
  Loader2,
  RefreshCw,
  BarChart3,
  AlertCircle,
} from 'lucide-react';

interface SkillPerformanceChartProps {
  projectId?: string;
  className?: string;
}

const CHART_COLORS = {
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  primary: '#0ea5e9',
  muted: '#94a3b8',
  grid: '#e2e8f0',
  text: '#64748b',
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-white dark:bg-stone-900 border border-border/20 rounded-xl shadow-2xl p-4 max-w-xs">
      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-3">
        {new Date(label).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        })}
      </p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-3 text-xs mb-1.5 last:mb-0">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="font-medium text-muted-foreground">{entry.name}:</span>
          <span className="font-bold text-foreground ml-auto">
            {entry.name === 'Success Rate'
              ? `${(entry.value * 100).toFixed(0)}%`
              : entry.value.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function SkillPerformanceChart({
  projectId,
  className,
}: SkillPerformanceChartProps) {
  const [history, setHistory] = useState<PerformanceHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showImprovement, setShowImprovement] = useState(false);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await skillsApi.performanceHistory(
        projectId ? { project_id: projectId, limit: 200 } : { limit: 200 },
      );
      setHistory(data);
    } catch (err) {
      console.error('Failed to load performance history:', err);
      setError('Could not load performance history');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Aggregate by timestamp: merge multiple evaluations at the same time
  const chartData = useMemo(() => {
    if (history.length === 0) return [];

    const SIX_HOURS = 6 * 60 * 60 * 1000;

    // Group evaluations within 6-hour windows into single data points
    const groups: { timestamp: number; rates: number[]; improvements: number[] }[] = [];

    for (const entry of history) {
      const ts = new Date(entry.timestamp).getTime();
      const existingGroup = groups.find(
        (g) => Math.abs(g.timestamp - ts) < SIX_HOURS,
      );

      if (existingGroup) {
        if (entry.success_rate !== null) existingGroup.rates.push(entry.success_rate);
        if (entry.avg_score_improvement !== null)
          existingGroup.improvements.push(entry.avg_score_improvement);
      } else {
        groups.push({
          timestamp: ts,
          rates: entry.success_rate !== null ? [entry.success_rate] : [],
          improvements: entry.avg_score_improvement !== null
            ? [entry.avg_score_improvement]
            : [],
        });
      }
    }

    return groups.map((g) => ({
      timestamp: g.timestamp,
      date: new Date(g.timestamp).toISOString(),
      avgSuccessRate:
        g.rates.length > 0
          ? g.rates.reduce((a, b) => a + b, 0) / g.rates.length
          : null,
      avgImprovement:
        g.improvements.length > 0
          ? g.improvements.reduce((a, b) => a + b, 0) / g.improvements.length
          : null,
      evaluationCount: g.rates.length,
    }));
  }, [history]);

  const avgRate = useMemo(() => {
    const valid = chartData.filter((d) => d.avgSuccessRate !== null);
    return valid.length > 0
      ? valid.reduce((s, d) => s + d.avgSuccessRate!, 0) / valid.length
      : 0;
  }, [chartData]);

  const trend = useMemo(() => {
    if (chartData.length < 2) return 'stable';
    const rates = chartData
      .filter((d) => d.avgSuccessRate !== null)
      .map((d) => d.avgSuccessRate!);
    if (rates.length < 2) return 'stable';
    const first = rates[0];
    const last = rates[rates.length - 1];
    const diff = last - first;
    if (diff > 0.05) return 'improving';
    if (diff < -0.05) return 'declining';
    return 'stable';
  }, [chartData]);

  if (loading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center justify-center h-48">
          <Loader2 size={20} className="animate-spin text-muted-foreground/50" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('p-6 text-center', className)}>
        <AlertCircle size={24} className="text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/50">{error}</p>
        <Button variant="ghost" size="sm" className="mt-3" onClick={loadHistory}>
          <RefreshCw size={12} className="mr-1.5" /> Retry
        </Button>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card className={cn('p-6 text-center', className)}>
        <BarChart3 size={24} className="text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/50">
          No evaluation history yet. Run an evaluation to see trends.
        </p>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp size={18} className="text-primary" />
          <h3 className="font-bold text-sm">Performance Trend</h3>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant={
              trend === 'improving'
                ? 'success'
                : trend === 'declining'
                  ? 'danger'
                  : 'default'
            }
            className="text-[8px]"
          >
            {trend === 'improving' ? '↑ Improving' : trend === 'declining' ? '↓ Declining' : '→ Stable'}
          </Badge>
          <Badge variant="info" className="text-[8px]">
            {history.length} evaluations
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowImprovement(!showImprovement)}
            className="text-[9px]"
          >
            {showImprovement ? 'Success Rate' : 'Score Impact'}
          </Button>
        </div>
      </div>

      {/* Summary stats row */}
      <div className="flex items-center gap-6 mb-6 text-xs">
        <div>
          <span className="text-muted-foreground/50 font-medium">Avg Rate</span>
          <span
            className={cn(
              'ml-2 font-black',
              avgRate >= 0.7
                ? 'text-success'
                : avgRate >= 0.5
                  ? 'text-warning'
                  : 'text-error',
            )}
          >
            {(avgRate * 100).toFixed(0)}%
          </span>
        </div>
        <div>
          <span className="text-muted-foreground/50 font-medium">Data Points</span>
          <span className="ml-2 font-black text-foreground">{chartData.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground/50 font-medium">Period</span>
          <span className="ml-2 font-black text-foreground">
            {chartData.length > 1
              ? `${new Date(chartData[0].timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${new Date(chartData[chartData.length - 1].timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
              : 'Single point'}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
          >
            <defs>
              <linearGradient id="srGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.success} stopOpacity={0.3} />
                <stop offset="95%" stopColor={CHART_COLORS.success} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="impGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={CHART_COLORS.grid}
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(ts) =>
                new Date(ts).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })
              }
              stroke={CHART_COLORS.text}
              tick={{ fontSize: 10 }}
              tickLine={false}
            />
            <YAxis
              yAxisId="sr"
              domain={[0, 1]}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              stroke={showImprovement ? CHART_COLORS.muted : CHART_COLORS.success}
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            {showImprovement && (
              <YAxis
                yAxisId="imp"
                orientation="right"
                domain={['auto', 'auto']}
                tickFormatter={(v) => v.toFixed(2)}
                stroke={CHART_COLORS.primary}
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={false}
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 10, fontWeight: 600 }}
              iconType="circle"
              iconSize={8}
            />
            <Area
              yAxisId="sr"
              type="monotone"
              dataKey="avgSuccessRate"
              name="Success Rate"
              stroke={CHART_COLORS.success}
              fill="url(#srGradient)"
              strokeWidth={2.5}
              dot={{ r: 3, fill: CHART_COLORS.success, strokeWidth: 0 }}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
            {showImprovement && (
              <Area
                yAxisId="imp"
                type="monotone"
                dataKey="avgImprovement"
                name="Avg Improvement"
                stroke={CHART_COLORS.primary}
                fill="url(#impGradient)"
                strokeWidth={2}
                strokeDasharray="4 3"
                dot={{ r: 2, fill: CHART_COLORS.primary, strokeWidth: 0 }}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Threshold lines legend */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border/10 text-[10px] text-muted-foreground/50">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 rounded bg-success" />
          Success rate
        </span>
        {showImprovement && (
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 rounded bg-primary border-0 border-dashed" style={{ borderTop: '2px dashed', height: 0 }} />
            Avg score improvement
          </span>
        )}
        <span className="flex items-center gap-1.5 ml-auto">
          <RefreshCw size={10} />
          <button onClick={loadHistory} className="hover:text-primary transition-colors">
            Refresh
          </button>
        </span>
      </div>
    </Card>
  );
}
