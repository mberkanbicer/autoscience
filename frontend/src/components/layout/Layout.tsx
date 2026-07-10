'use client';

import { ReactNode, useState } from 'react';
import { Sidebar } from './Sidebar';
import { ArtifactPanel } from './ArtifactPanel';
import { ShortcutOverlay } from './ShortcutOverlay';
import { MobileTopBar } from './MobileTopBar';

interface LayoutProps {
  children: ReactNode;
  projectId?: string;
}

export function Layout({ children, projectId }: LayoutProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background flex flex-col lg:flex-row relative overflow-hidden transition-colors duration-1000">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-5%] left-[-5%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[140px] animate-pulse opacity-60" style={{ animationDuration: '7s' }} />
        <div className="absolute bottom-[-10%] right-[-5%] w-[50%] h-[50%] bg-tertiary/10 rounded-full blur-[140px] animate-pulse opacity-60" style={{ animationDuration: '11s' }} />
      </div>

      <MobileTopBar projectId={projectId} onMenuClick={() => setMobileNavOpen(true)} />
      <Sidebar
        projectId={projectId}
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />
      <main className="flex-1 lg:ml-64 min-w-0 relative z-10 animate-in fade-in duration-700">
        {children}
      </main>
      <ArtifactPanel />
      <ShortcutOverlay />
    </div>
  );
}