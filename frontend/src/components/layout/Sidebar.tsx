'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FolderKanban,
  Lightbulb,
  FileSearch,
  FlaskConical,
  MessageSquare,
  GraduationCap,
  FileText,
  BookOpen,
  Settings,
  Activity,
  HelpCircle,
} from 'lucide-react';

const mainNavItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderKanban },
];

interface SidebarProps {
  projectId?: string;
}

export function Sidebar({ projectId }: SidebarProps) {
  const pathname = usePathname();

  const projectNavItems = projectId
    ? [
        { href: `/projects/${projectId}`, label: 'Overview', icon: LayoutDashboard },
        { href: `/projects/${projectId}/ideas`, label: 'Ideas', icon: Lightbulb },
        { href: `/projects/${projectId}/runs`, label: 'Research Runs', icon: Activity },
        { href: `/projects/${projectId}/papers`, label: 'Papers', icon: FileSearch },
        { href: `/projects/${projectId}/questions`, label: 'Questions', icon: MessageSquare },
        { href: `/projects/${projectId}/hypotheses`, label: 'Hypotheses', icon: FlaskConical },
        { href: `/projects/${projectId}/skills`, label: 'Skills', icon: GraduationCap },
        { href: `/projects/${projectId}/reports`, label: 'Reports', icon: FileText },
        { href: `/projects/${projectId}/wiki`, label: 'Wiki', icon: BookOpen },
        { href: `/projects/${projectId}/settings`, label: 'Settings', icon: Settings },
      ]
    : [];

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

        {/* Project Navigation */}
        {projectNavItems.length > 0 && (
          <>
            <div className="pt-6 pb-2">
              <span className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Project
              </span>
            </div>
            {projectNavItems.map((item) => {
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
