'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { projectsApi } from '@/lib/api';
import type { ProjectStats } from '@/lib/types';
import {
  LayoutDashboard,
  FolderKanban,
  Lightbulb,
  FlaskConical,
  BookOpen,
  Settings,
  Activity,
  Layers,
  CheckCircle,
  FileText,
  Database,
  Users,
  X,
} from 'lucide-react';

const PIPELINE_STAGES = [
  { key: 'ideas', label: 'Ideas' },
  { key: 'total_papers', label: 'Literature' },
  { key: 'total_clusters', label: 'Analysis' },
  { key: 'total_conflicts', label: 'Conflicts' },
  { key: 'total_questions', label: 'Questions' },
  { key: 'total_hypotheses', label: 'Hypotheses' },
  { key: 'total_reports', label: 'Reports' },
];

const mainNavItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderKanban },
  { href: '/settings', label: 'API Settings', icon: Settings },
];

const projectNavItems = (projectId: string) => [
  { href: `/projects/${projectId}`, label: 'Overview', icon: LayoutDashboard },
  { href: `/projects/${projectId}/health`, label: 'Cognitive Health', icon: LayoutDashboard },
  { href: `/projects/${projectId}/ideas`, label: 'Ideas', icon: Lightbulb },
  { href: `/projects/${projectId}/runs`, label: 'Research Runs', icon: Activity },
  { href: `/projects/${projectId}/papers`, label: 'Papers', icon: FileText },
  { href: `/projects/${projectId}/clusters`, label: 'Clusters', icon: Layers },
  { href: `/projects/${projectId}/datasets`, label: 'Datasets', icon: Database },
  { href: `/projects/${projectId}/approval`, label: 'Approvals', icon: CheckCircle },
  { href: `/projects/${projectId}/wiki`, label: 'Wiki', icon: BookOpen },
  { href: `/projects/${projectId}/team`, label: 'Team', icon: Users },
  { href: `/projects/${projectId}/manuscripts`, label: 'Manuscripts', icon: FileText },
  { href: `/projects/${projectId}/article-studio`, label: 'Article Studio', icon: FileText },
  { href: `/projects/${projectId}/settings`, label: 'Settings', icon: Settings },
];

interface SidebarContentProps {
  projectId?: string;
  onNavigate?: () => void;
  showClose?: boolean;
  onClose?: () => void;
}

export function SidebarContent({
  projectId,
  onNavigate,
  showClose,
  onClose,
}: SidebarContentProps) {
  const pathname = usePathname();
  const [stats, setStats] = useState<ProjectStats | null>(null);

  useEffect(() => {
    if (!projectId) return;
    const fetchStats = () => {
      projectsApi.stats(projectId).then(setStats).catch(() => {});
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [projectId]);

  const navLink = (item: { href: string; label: string; icon: typeof LayoutDashboard }) => {
    const Icon = item.icon;
    const isActive =
      pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onNavigate}
        className={cn(
          'flex items-center gap-4 px-5 py-3.5 rounded-[1.2rem] text-sm font-bold transition-all duration-300',
          isActive
            ? 'bg-primary text-stone-900 shadow-xl shadow-primary/20'
            : 'text-muted-foreground hover:bg-primary/5 hover:text-primary',
        )}
      >
        <Icon size={18} />
        <span>{item.label}</span>
      </Link>
    );
  };

  return (
    <>
      <div className="px-5 py-6 border-b border-stone-200 dark:border-stone-100/5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group" onClick={onNavigate}>
          <div className="w-10 h-10 bg-primary rounded-2xl flex items-center justify-center shadow-lg">
            <FlaskConical size={20} className="text-stone-900" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight">Autoscience</span>
            <span className="block text-[8px] font-black uppercase tracking-[0.3em] text-primary/80">
              Scientific Hearth
            </span>
          </div>
        </Link>
        {showClose && onClose && (
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full hover:bg-muted lg:hidden"
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        )}
      </div>

      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        <p className="px-4 mb-3 text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">
          Navigation
        </p>
        {mainNavItems.map(navLink)}

        {projectId && (
          <>
            <p className="px-4 pt-6 pb-2 text-[10px] font-black text-muted-foreground/50 uppercase tracking-[0.2em]">
              Active Project
            </p>
            {projectNavItems(projectId).map(navLink)}
          </>
        )}
      </nav>

      {stats && (
        <div className="p-4 border-t border-stone-200 dark:border-stone-100/5">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={14} className="text-primary" />
            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
              Pipeline
            </span>
          </div>
          <div className="space-y-1.5">
            {PIPELINE_STAGES.map((stage) => (
              <div key={stage.key} className="flex justify-between text-[10px]">
                <span className="text-muted-foreground">{stage.label}</span>
                <span className="text-primary font-bold">
                  {(stats[stage.key as keyof ProjectStats] as number | undefined) ?? 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

interface SidebarProps {
  projectId?: string;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ projectId, mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  useEffect(() => {
    onMobileClose?.();
  }, [pathname, onMobileClose]);

  return (
    <>
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-64 bg-stone-50 dark:bg-stone-950 border-r border-stone-200 dark:border-stone-100/5 z-40 flex-col shadow-2xl">
        <SidebarContent projectId={projectId} />
      </aside>

      {mobileOpen && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
            aria-label="Close navigation"
            onClick={onMobileClose}
          />
          <aside className="fixed left-0 top-0 h-full w-[min(18rem,85vw)] z-50 bg-stone-50 dark:bg-stone-950 border-r border-stone-200 dark:border-stone-100/5 flex flex-col shadow-2xl lg:hidden animate-in slide-in-from-left duration-300">
            <SidebarContent
              projectId={projectId}
              onNavigate={onMobileClose}
              showClose
              onClose={onMobileClose}
            />
          </aside>
        </>
      )}
    </>
  );
}