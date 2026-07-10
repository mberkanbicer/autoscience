'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 animate-in fade-in zoom-in-95 duration-700" role="alert">
      <div className="w-20 h-20 bg-error/10 backdrop-blur-sm border border-error/20 rounded-full flex items-center justify-center mb-6 shadow-inner animate-pulse">
        <AlertCircle className="w-10 h-10 text-error" aria-hidden="true" />
      </div>
      <p className="text-foreground/70 font-medium text-center mb-6 max-w-md leading-relaxed">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} className="px-6" aria-label="Retry loading data">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Operation
        </Button>
      )}
    </div>
  );
}

interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message = 'Synchronizing Lab State...' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 animate-in fade-in duration-700" role="status">
      <div className="relative mb-6">
        <div className="w-12 h-12 border-4 border-primary/10 border-t-primary rounded-full animate-spin shadow-lg" aria-hidden="true" />
        <div className="absolute inset-0 w-12 h-12 border-4 border-transparent border-b-tertiary/40 rounded-full animate-spin" style={{ animationDuration: '3s', animationDirection: 'reverse' }} />
      </div>
      <p className="text-muted-foreground text-sm font-bold uppercase tracking-[0.2em] animate-pulse">{message}</p>
    </div>
  );
}

interface LoadStateWrapperProps<T> {
  loading: boolean;
  error: string | null;
  data: T | null;
  onRetry?: () => void;
  loadingMessage?: string;
  children: (data: T) => React.ReactNode;
}

export function LoadStateWrapper<T>({
  loading,
  error,
  data,
  onRetry,
  loadingMessage,
  children,
}: LoadStateWrapperProps<T>) {
  if (loading) {
    return <LoadingSpinner message={loadingMessage} />;
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={onRetry} />;
  }

  if (data === null) {
    return <ErrorDisplay message="No data available" onRetry={onRetry} />;
  }

  return <>{children(data)}</>;
}
