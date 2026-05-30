'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'bg-white rounded-xl border border-gray-200 shadow-sm',
          hover && 'hover:shadow-md hover:border-gray-300 transition-all cursor-pointer',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('px-6 py-4 border-b border-gray-100', className)} {...props} />
  )
);

CardHeader.displayName = 'CardHeader';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('px-6 py-4', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-xl', className)} {...props} />
  )
);

CardFooter.displayName = 'CardFooter';
