'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { projectsApi } from '@/lib/api';
import {
  LayoutDashboard,
  FolderKanban,
  Lightbulb,
  FlaskConical,
  GraduationCap,
  BookOpen,
  Settings,
  Activity,
  HelpCircle,
  Layers,
  CheckCircle,
} from 'lucide-react';

const PIPELINE_STAGES = [
  { key: 'ideas', label: 'Ideas', href: 'ideas', color: '#EAB308' },
  { key: 'total_papers', label: 'Literature', href: 'papers', color: '#3B82F6' },
  { key: 'total_clusters', label: 'Analysis', href: 'pipeline', color: '#8B5CF6' },
  { key: 'total_conflicts', label: 'Conflicts', href: 'pipeline', color: '#EF4444' },
  { key: 'total_questions', label: 'Questions', href: 'questions', color: '#14B8A6' },
  { key: 'total_hypotheses', label: 'Hypotheses', href: 'hypotheses', color: '#7C3AED' },
  { key: 'total_reports', label: 'Reports', href: 'reports', color: '#F97316' },
];

const mainNavItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderKanban },
  { href: '/settings', label: 'API Settings', icon: Settings },
];

interface SidebarProps {
  projectId?: string;
}

export function Sidebar({ projectId }: SidebarProps) {
  const pathname = usePathname();
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    if (!projectId) return;
    projectsApi.stats(projectId).then(setStats).catch(() => {});
  }, [projectId]);

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white z-40 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-700">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center">
            <FlaskConical size={20} className="text-white" />
          </div>
          <div>
            <span className="font-bold text-lg">Autoscience</span>
            <span className="block text-xs text-gray-400">Research Platform</span>
          </div>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="mb-4">
          <span className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Main
          </span>
        </div>
        {mainNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}

        {/* Project Navigation - Top items */}
        {projectId && (
          <>
            <div className="pt-6 pb-2">
              <span className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Project
              </span>
            </div>
            {[
              { href: `/projects/${projectId}`, label: 'Overview', icon: LayoutDashboard },
              { href: `/projects/${projectId}/ideas`, label: 'Ideas', icon: Lightbulb },
              { href: `/projects/${projectId}/runs`, label: 'Research Runs', icon: Activity },
              { href: `/projects/${projectId}/skills`, label: 'Skills', icon: GraduationCap },
              { href: `/projects/${projectId}/clusters`, label: 'Clusters', icon: Layers },
              { href: `/projects/${projectId}/approval`, label: 'Approvals', icon: CheckCircle },
              { href: `/projects/${projectId}/wiki`, label: 'Wiki', icon: BookOpen },
              { href: `/projects/${projectId}/settings`, label: 'Settings', icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all',
                    isActive
                      ? 'bg-white/10 text-white'
                      : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
                  )}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </>
        )}

        {/* Pipeline Stages */}
        {projectId && (
          <>
            <div className="pt-4 pb-2">
              <span className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Pipeline
              </span>
            </div>
            <div className="relative ml-3">
              {/* Vertical connector line */}
              <div className="absolute left-[7px] top-3 bottom-3 w-px bg-gray-700" />
              {/* Animated flow line */}
              {stats && (
                <div className="absolute left-[7px] top-3 w-px h-3/4 animate-pipeline-flow" style={{ opacity: 0.3 }} />
              )}
              <div className="space-y-0.5">
                {PIPELINE_STAGES.map((stage) => {
                  const count = stats ? (stats[stage.key] ?? stats[`total_${stage.key}`] ?? 0) : 0;
                  const hasData = count > 0;
                  const isActive = pathname.includes(`/projects/${projectId}/${stage.href}`);
                  return (
                    <Link
                      key={stage.key}
                      href={`/projects/${projectId}/${stage.href}`}
                      className={cn(
                        'flex items-center gap-3 pl-0 pr-3 py-1.5 rounded-r-xl text-sm transition-all',
                        isActive
                          ? 'bg-white/10 text-white'
                          : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
                      )}
                    >
                      {/* Dot indicator */}
                      <div className="relative z-10 flex items-center justify-center">
                        <div
                          className={cn(
                            'w-[15px] h-[15px] rounded-full border-2',
                            isActive && 'animate-pulse-glow'
                          )}
                          style={{
                            borderColor: stage.color,
                            backgroundColor: hasData ? stage.color : 'transparent',
                            boxShadow: isActive ? `0 0 8px ${stage.color}` : 'none',
                          }}
                        />
                      </div>
                      <span className="flex-1">{stage.label}</span>
                      {stats && (
                        <span className="text-xs text-gray-500 font-mono">{count}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-gray-700">
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-gray-400 hover:bg-gray-700/50 hover:text-white transition-all"
        >
          <HelpCircle size={16} />
          Help & Support
        </a>
      </div>
    </div>
  );
}
