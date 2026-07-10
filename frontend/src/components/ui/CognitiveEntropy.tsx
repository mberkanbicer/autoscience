'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from './Badge';

interface CognitiveEntropyProps {
  entropy: number;
  mode?: 'exploration' | 'exploitation' | 'balanced';
  size?: 'sm' | 'md';
  className?: string;
}

export function CognitiveEntropy({ entropy, mode, size = 'md', className }: CognitiveEntropyProps) {
  const entropyPercent = Math.round(entropy * 100);
  
  const modeConfig = {
    exploration: {
      label: 'Frontier Scan',
      description: 'Broad search mode: scanning unknown frontiers.',
      color: 'warning',
    },
    exploitation: {
      label: 'Deep Exploit',
      description: 'Focused mode: deep exploitation of specific findings.',
      color: 'primary',
    },
    balanced: {
      label: 'Balanced Focus',
      description: 'Maintaining research equilibrium.',
      color: 'success',
    },
  };
  
  const config = mode ? modeConfig[mode] : {
    label: entropy < 0.3 ? 'Deep Exploit' : entropy > 0.7 ? 'Frontier Scan' : 'Balanced Focus',
    description: entropy < 0.3 
      ? 'Focused mode: deep exploitation of specific findings.'
      : entropy > 0.7
      ? 'Broad search mode: scanning unknown frontiers.'
      : 'Maintaining research equilibrium.',
    color: entropy < 0.3 ? 'primary' : entropy > 0.7 ? 'warning' : 'success',
  };

  return (
    <div className={cn('flex items-center gap-4', className)}>
      <div className="flex items-center gap-2">
        <div className="relative">
          <div className={cn(
            'w-3 h-3 rounded-full',
            `bg-${config.color}`
          )} />
          <div className={cn(
            'absolute inset-0 w-3 h-3 rounded-full animate-ping opacity-20',
            `bg-${config.color}`
          )} />
        </div>
        <span className="text-[9px] font-black text-muted-foreground uppercase tracking-widest">
          Cognitive Entropy
        </span>
      </div>
      <div className="flex-1 h-2 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden p-1 shadow-inner">
        <div 
          className={cn(
            'h-full rounded-full shadow-[0_0_20px_rgba(217,119,6,0.4)] transition-all duration-1000 ease-out',
            `bg-${config.color}`
          )}
          style={{ width: `${entropyPercent}%` }}
        />
      </div>
      <Badge 
        variant={config.color as any} 
        className="text-[10px] font-black uppercase tracking-widest px-3 py-1"
      >
        {config.label}
      </Badge>
    </div>
  );
}
