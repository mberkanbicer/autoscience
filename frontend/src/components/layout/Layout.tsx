'use client';

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
  projectId?: string;
}

export function Layout({ children, projectId }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar projectId={projectId} />
      <main className="ml-64">
        {children}
      </main>
    </div>
  );
}
