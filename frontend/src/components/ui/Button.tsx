'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-primary text-white hover:bg-primary/90 shadow-2xl shadow-primary/40',
      secondary: 'bg-white/40 backdrop-blur-md text-foreground border border-border/20 hover:bg-white/60 shadow-lg shadow-black/5',
      ghost: 'text-muted-foreground hover:bg-primary/5 hover:text-primary',
      danger: 'bg-error text-white hover:bg-error/90 shadow-2xl shadow-error/40',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-xs font-bold uppercase tracking-widest',
      md: 'px-6 py-2.5 text-sm font-bold tracking-tight',
      lg: 'px-8 py-3.5 text-base font-black tracking-tight',
    };

    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-xl transition-all duration-300 active:scale-95 hover:scale-[1.03] focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-4 disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
