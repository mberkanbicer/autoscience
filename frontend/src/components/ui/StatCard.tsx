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
        'bg-white rounded-xl border border-gray-200 shadow-sm p-6',
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        {icon && (
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
            {icon}
          </div>
        )}
      </div>
      {change !== undefined && (
        <div className="mt-3 flex items-center text-sm">
          <span
            className={cn(
              'font-medium',
              change >= 0 ? 'text-green-600' : 'text-red-600'
            )}
          >
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
          </span>
          <span className="text-gray-500 ml-2">vs last period</span>
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
