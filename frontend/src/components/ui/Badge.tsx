'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'sm', children, ...props }, ref) => {
    const variants = {
      default: 'bg-gray-100 text-gray-700',
      success: 'bg-green-100 text-green-700',
      warning: 'bg-yellow-100 text-yellow-700',
      danger: 'bg-red-100 text-red-700',
      info: 'bg-blue-100 text-blue-700',
      purple: 'bg-purple-100 text-purple-700',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-medium rounded-full',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// Status-specific badges
export const StatusBadge = ({ status }: { status: string }) => {
  const getStatusVariant = (status: string): BadgeProps['variant'] => {
    const s = status.toLowerCase();
    if (['completed', 'done', 'active', 'approved', 'promoted', 'high_value'].includes(s)) return 'success';
    if (['running', 'pending', 'under_validation', 'promising'].includes(s)) return 'warning';
    if (['failed', 'rejected', 'error', 'weak', 'reject'].includes(s)) return 'danger';
    if (['paused', 'cancelled', 'archived', 'incremental'].includes(s)) return 'default';
    return 'info';
  };

  return (
    <Badge variant={getStatusVariant(status)}>
      {status.replace('_', ' ')}
    </Badge>
  );
};
