'use client';

import Link from 'next/link';
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
  className?: string;
}

export function Header({ title, subtitle, actions, breadcrumbs, className }: HeaderProps) {
  return (
    <div className={cn('sticky top-0 glass z-30 shadow-2xl transition-all duration-500 border-b border-stone-200 dark:border-stone-100/10', className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div className="px-4 lg:px-10 py-3 border-b border-stone-200/50 dark:border-stone-100/5 bg-background/20">
          <nav className="flex items-center gap-3 text-[10px] font-black tracking-[0.3em] uppercase">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-3">
                {i > 0 && <span className="text-muted-foreground/10 font-thin">|</span>}
                {crumb.href ? (
                  <Link href={crumb.href} className="text-primary hover:text-primary/70 transition-all duration-300 hover:translate-x-0.5">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-muted-foreground/60">{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        </div>
      )}

      {/* Main Header */}
      <div className="px-4 lg:px-10 py-5 lg:py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-2xl lg:text-3xl font-black text-foreground tracking-tighter leading-none truncate">{title}</h1>
            {subtitle && (
              <p className="mt-3 text-xs text-muted-foreground font-black uppercase tracking-[0.2em] opacity-60">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="flex items-center gap-4 animate-in fade-in slide-in-from-right-12 duration-1000 ease-out">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
