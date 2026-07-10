'use client';

import { cn } from '@/lib/utils';
import { Badge } from './Badge';

interface FocusMetricProps {
  /** Focus score from 0 (broad/exploration) to 1 (deep/focused) */
  focusScore: number;
  /** Optional label override (deep_dive | balanced | broad_scan) */
  focusLabel?: string;
  size?: 'sm' | 'md';
  className?: string;
}

const focusConfig = {
  deep_dive: {
    icon: '🎯',
    label: 'Deep Dive',
    description: 'Highly focused — research concentrated in specific clusters.',
    gradient: 'from-emerald-500 to-teal-400',
    badgeColor: 'success' as const,
  },
  balanced: {
    icon: '⚖️',
    label: 'Balanced',
    description: 'Even mix of depth and breadth across research areas.',
    gradient: 'from-amber-500 to-orange-400',
    badgeColor: 'warning' as const,
  },
  broad_scan: {
    icon: '🔭',
    label: 'Broad Scan',
    description: 'Wide exploration — papers spread across many clusters.',
    gradient: 'from-violet-500 to-purple-400',
    badgeColor: 'info' as const,
  },
};

export function FocusMetric({ focusScore, focusLabel, size = 'md', className }: FocusMetricProps) {
  const scorePercent = Math.round(focusScore * 100);

  const config =
    focusLabel && focusLabel in focusConfig
      ? focusConfig[focusLabel as keyof typeof focusConfig]
      : focusScore > 0.7
        ? focusConfig.deep_dive
        : focusScore < 0.3
          ? focusConfig.broad_scan
          : focusConfig.balanced;

  const isSm = size === 'sm';

  return (
    <div className={cn('flex items-center gap-4', className)}>
      {/* Label row */}
      <div className="flex items-center gap-2 min-w-fit">
        <div className="relative">
          <div className={cn(
            'rounded-full',
            isSm ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5',
            `bg-${config.badgeColor}`
          )} />
          <div className={cn(
            'absolute inset-0 rounded-full animate-ping opacity-20',
            `bg-${config.badgeColor}`
          )} />
        </div>
        <span className={cn(
          'font-black text-muted-foreground uppercase tracking-widest',
          isSm ? 'text-[8px]' : 'text-[9px]'
        )}>
          Research Focus
        </span>
      </div>

      {/* Gauge bar */}
      <div className="flex-1 relative">
        {/* Background track */}
        <div className={cn(
          'w-full bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden shadow-inner',
          isSm ? 'h-1.5' : 'h-2.5'
        )}>
          {/* Gradient fill */}
          <div
            className={cn(
              'h-full rounded-full transition-all duration-1000 ease-out',
              'bg-gradient-to-r', config.gradient
            )}
            style={{ width: `${scorePercent}%` }}
          />
        </div>

        {/* Depth/Breadth labels */}
        {!isSm && (
          <div className="flex justify-between mt-1 px-0.5">
            <span className="text-[7px] font-bold text-muted-foreground/30 uppercase tracking-wider">
              Breadth
            </span>
            <span className="text-[7px] font-bold text-muted-foreground/30 uppercase tracking-wider">
              Depth
            </span>
          </div>
        )}
      </div>

      {/* Score + badge */}
      <div className="flex items-center gap-2 min-w-fit">
        <span className={cn(
          'font-black tabular-nums',
          isSm ? 'text-sm' : 'text-lg',
          `text-${config.badgeColor}`
        )}>
          {scorePercent}%
        </span>
        <Badge
          variant={config.badgeColor}
          className={cn(
            'font-black uppercase tracking-widest',
            isSm ? 'text-[8px] px-2 py-0.5' : 'text-[10px] px-3 py-1'
          )}
        >
          {config.icon} {config.label}
        </Badge>
      </div>
    </div>
  );
}

/** Compact version — just the gauge and percentage */
export function FocusGauge({ focusScore, size = 'sm', className }: { focusScore: number; size?: 'sm' | 'md'; className?: string }) {
  const scorePercent = Math.round(focusScore * 100);
  const color = focusScore > 0.7 ? 'text-success' : focusScore < 0.3 ? 'text-primary' : 'text-warning';

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn(
        'flex-1 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden shadow-inner',
        size === 'sm' ? 'h-1.5' : 'h-2.5'
      )}>
        <div
          className={cn(
            'h-full rounded-full transition-all duration-1000 ease-out',
            'bg-gradient-to-r',
            focusScore > 0.7 ? 'from-emerald-500 to-teal-400' :
            focusScore < 0.3 ? 'from-violet-500 to-purple-400' :
            'from-amber-500 to-orange-400'
          )}
          style={{ width: `${scorePercent}%` }}
        />
      </div>
      <span className={cn('font-black tabular-nums text-xs', color)}>{scorePercent}%</span>
    </div>
  );
}
