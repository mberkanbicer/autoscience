'use client';
import { Button } from './Button';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className, icon, title, description, action, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col items-center justify-center py-16 px-4 animate-in fade-in zoom-in-95 duration-700', className)}
      {...props}
    >
      {icon && (
        <div className="w-20 h-20 bg-muted/50 backdrop-blur-sm border border-border/10 rounded-full flex items-center justify-center mb-6 shadow-inner animate-pulse">
          {icon}
        </div>
      )}
      <h3 className="text-xl font-bold text-foreground mb-2 tracking-tight">{title}</h3>
      {description && <p className="text-sm text-muted-foreground text-center max-w-sm mb-6 leading-relaxed">{description}</p>}
      {action && (
        <div className="animate-in slide-in-from-bottom-2 duration-500 delay-300">
          {action}
        </div>
      )}
    </div>
  )
);

EmptyState.displayName = 'EmptyState';

interface ErrorStateProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState = forwardRef<HTMLDivElement, ErrorStateProps>(
  ({ className, title = 'System Conflict Detected', message, onRetry, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col items-center justify-center py-16 px-4 animate-in fade-in zoom-in-95 duration-700', className)}
      {...props}
    >
      <div className="w-20 h-20 bg-error/10 backdrop-blur-sm border border-error/20 rounded-full flex items-center justify-center mb-6 shadow-inner group">
        <svg className="w-10 h-10 text-error transition-transform duration-500 group-hover:rotate-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="text-xl font-bold text-foreground mb-2 tracking-tight">{title}</h3>
      <p className="text-sm text-muted-foreground text-center max-w-sm mb-6 leading-relaxed">{message}</p>
      {onRetry && (
        <Button
          variant="danger"
          onClick={onRetry}
          className="px-6 py-2.5"
        >
          Resolve Conflict
        </Button>
      )}
    </div>
  )
);

ErrorState.displayName = 'ErrorState';
