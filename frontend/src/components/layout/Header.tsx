'use client';

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
    <div className={cn('bg-white border-b border-gray-200', className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div className="px-6 py-2 border-b border-gray-100">
          <nav className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-2">
                {i > 0 && <span className="text-gray-300">/</span>}
                {crumb.href ? (
                  <a href={crumb.href} className="text-blue-600 hover:text-blue-700">
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-gray-600">{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        </div>
      )}

      {/* Main Header */}
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {subtitle && (
              <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </div>
      </div>
    </div>
  );
}
