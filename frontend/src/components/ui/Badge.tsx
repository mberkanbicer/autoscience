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
      default: 'bg-muted text-muted-foreground/60 border border-border/10',
      success: 'bg-success/20 text-success border border-success/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]',
      warning: 'bg-warning/20 text-warning border border-warning/30 shadow-[0_0_10px_rgba(245,158,11,0.1)]',
      danger: 'bg-error/20 text-error border border-error/30 shadow-[0_0_10px_rgba(244,63,94,0.1)]',
      info: 'bg-primary/20 text-primary border border-primary/30 shadow-[0_0_10px_rgba(14,165,233,0.1)]',
      purple: 'bg-tertiary/20 text-tertiary border border-tertiary/30 shadow-[0_0_10px_rgba(139,92,246,0.1)]',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.1em]',
      md: 'px-3 py-1 text-[10px] font-black uppercase tracking-[0.15em]',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-lg transition-all duration-300',
          (variant === 'success' || variant === 'warning') && 'animate-pulse',
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
