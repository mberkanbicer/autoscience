'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from '@/components/ui/toast';
import { ThemeToggle } from '@/components/theme-toggle';
import { ErrorBoundaryWrapper } from '@/components/ErrorBoundaryWrapper';
import { ArtifactProvider } from '@/lib/ArtifactContext';
import { ActivityTracker } from '@/components/ActivityTracker';
import { GlobalErrorToast } from '@/components/GlobalErrorToast';
import { refreshApiSettings } from '@/lib/apiSettings';
import { useEffect } from 'react';

const queryClient = new QueryClient();

function SettingsBootstrap() {
  useEffect(() => {
    refreshApiSettings().catch(() => {});
  }, []);
  return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ArtifactProvider>
        <SettingsBootstrap />
        <ActivityTracker />
        <ErrorBoundaryWrapper>{children}</ErrorBoundaryWrapper>
      </ArtifactProvider>
      <ToastProvider>
        <GlobalErrorToast />
      </ToastProvider>
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>
    </QueryClientProvider>
  );
}