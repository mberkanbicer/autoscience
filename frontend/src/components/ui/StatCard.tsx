'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
}

export const StatCard = forwardRef<HTMLDivElement, StatCardProps>(
  ({ className, label, value, change, icon, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'glass rounded-3xl p-10 transition-all duration-700 hover:shadow-[0_30px_70px_-15px_rgba(0,0,0,0.1)] hover:-translate-y-3 hover:scale-[1.03] group relative overflow-hidden',
        className
      )}
      {...props}
    >
      <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.07] transition-opacity duration-1000">
         {icon}
      </div>
      <div className="flex items-center justify-between relative z-10">
        <div>
          <p className="text-[10px] font-black text-muted-foreground/30 uppercase tracking-[0.4em] mb-3">{label}</p>
          <p className="text-4xl font-black text-foreground tracking-tighter group-hover:text-primary transition-colors duration-700">{value}</p>
        </div>
        {icon && (
          <div className="w-16 h-16 bg-stone-100/50 backdrop-blur-md rounded-2xl flex items-center justify-center text-primary shadow-inner group-hover:bg-primary group-hover:text-stone-900 group-hover:rotate-[15deg] transition-all duration-700 ease-out">
            {icon}
          </div>
        )}
      </div>
      {change !== undefined && (
        <div className="mt-8 flex items-center relative z-10">
          <span
            className={cn(
              'px-4 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border shadow-sm',
              change >= 0 
                ? 'bg-success/10 text-success border-success/20 animate-pulse' 
                : 'bg-error/10 text-error border-error/20'
            )}
          >
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)}% INTEL_VELOCITY
          </span>
        </div>
      )}
    </div>
  )
);

StatCard.displayName = 'StatCard';

interface StatsGridProps extends HTMLAttributes<HTMLDivElement> {
  stats: StatCardProps[];
}

export const StatsGrid = forwardRef<HTMLDivElement, StatsGridProps>(
  ({ className, stats, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4', className)}
      {...props}
    >
      {stats.map((stat, i) => (
        <StatCard key={i} {...stat} />
      ))}
    </div>
  )
);

StatsGrid.displayName = 'StatsGrid';
