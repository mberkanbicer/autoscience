'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4" role="alert">
      <AlertCircle className="w-12 h-12 text-red-400 mb-4" aria-hidden="true" />
      <p className="text-gray-600 text-center mb-4 max-w-md">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} aria-label="Retry loading data">
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      )}
    </div>
  );
}

interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4" role="status">
      <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4" aria-hidden="true" />
      <p className="text-gray-500 text-sm">{message}</p>
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
