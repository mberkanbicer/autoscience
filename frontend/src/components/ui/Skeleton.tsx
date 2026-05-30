'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const Skeleton = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('animate-pulse bg-gray-200 rounded', className)}
      {...props}
    />
  )
);

Skeleton.displayName = 'Skeleton';

export const SkeletonCard = () => (
  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
    <Skeleton className="h-4 w-3/4 mb-4" />
    <Skeleton className="h-3 w-full mb-2" />
    <Skeleton className="h-3 w-5/6 mb-4" />
    <div className="flex gap-2">
      <Skeleton className="h-6 w-16 rounded-full" />
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  </div>
);

export const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
    <div className="p-4 border-b border-gray-100">
      <Skeleton className="h-6 w-48" />
    </div>
    <div className="divide-y divide-gray-100">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4 flex items-center gap-4">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonStats = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16 mb-2" />
        <Skeleton className="h-3 w-32" />
      </div>
    ))}
  </div>
);
