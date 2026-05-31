'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StatsGrid } from '@/components/ui/StatCard';
import { SkeletonStats } from '@/components/ui/Skeleton';
import { projectsApi } from '@/lib/api';
import { Project, ProjectStats } from '@/lib/types';
import {
  Lightbulb,
  FileSearch,
  Activity,
  MessageSquare,
  FlaskConical,
  GraduationCap,
  Settings,
  ArrowRight,
  GitBranch,
  MessageSquareText,
  BookOpen,
  Network,
} from 'lucide-react';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const [projectData, statsData] = await Promise.all([
        projectsApi.get(projectId),
        projectsApi.stats(projectId),
      ]);
      setProject(projectData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Loading..." />
        <div className="p-6">
          <SkeletonStats />
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout projectId={projectId}>
        <Header title="Project Not Found" />
      </Layout>
    );
  }

  const navItems = [
    { href: `/projects/${projectId}/ideas`, label: 'Ideas', icon: Lightbulb, color: 'bg-yellow-100 text-yellow-600' },
    { href: `/projects/${projectId}/runs`, label: 'Research Runs', icon: Activity, color: 'bg-green-100 text-green-600' },
    { href: `/projects/${projectId}/papers`, label: 'Papers', icon: FileSearch, color: 'bg-blue-100 text-blue-600' },
    { href: `/projects/${projectId}/questions`, label: 'Questions', icon: MessageSquare, color: 'bg-purple-100 text-purple-600' },
    { href: `/projects/${projectId}/hypotheses`, label: 'Hypotheses', icon: FlaskConical, color: 'bg-indigo-100 text-indigo-600' },
    { href: `/projects/${projectId}/skills`, label: 'Skills', icon: GraduationCap, color: 'bg-orange-100 text-orange-600' },
    { href: `/projects/${projectId}/reports`, label: 'Reports', icon: FileSearch, color: 'bg-red-100 text-red-600' },
    { href: `/projects/${projectId}/wiki`, label: 'Wiki', icon: FileSearch, color: 'bg-teal-100 text-teal-600' },
    { href: `/projects/${projectId}/pipeline`, label: 'Pipeline', icon: GitBranch, color: 'bg-cyan-100 text-cyan-600' },
    { href: `/projects/${projectId}/settings`, label: 'Settings', icon: Settings, color: 'bg-gray-100 text-gray-600' },
  ];

  return (
    <Layout projectId={projectId}>
      <Header
        title={project.name}
        subtitle={project.domain}
        actions={
          <div className="flex gap-3">
            <Badge variant={project.idle_research_enabled ? 'success' : 'default'}>
              {project.idle_research_enabled ? 'Idle Research Active' : 'Idle Research Off'}
            </Badge>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        {stats && (
          <StatsGrid
            className="lg:grid-cols-5"
            stats={[
              { label: 'Ideas', value: stats.total_ideas, icon: <Lightbulb size={24} /> },
              { label: 'Active Ideas', value: stats.active_ideas, icon: <Lightbulb size={24} /> },
              { label: 'Papers', value: stats.total_papers, icon: <FileSearch size={24} /> },
              { label: 'Runs', value: stats.total_runs, icon: <Activity size={24} /> },
              { label: 'Questions', value: stats.total_questions, icon: <MessageSquareText size={24} /> },
              { label: 'Hypotheses', value: stats.total_hypotheses, icon: <FlaskConical size={24} /> },
              { label: 'Conflicts', value: stats.total_conflicts, icon: <MessageSquare size={24} /> },
              { label: 'Skills', value: stats.total_skills, icon: <GraduationCap size={24} /> },
              { label: 'Reports', value: stats.total_reports || 0, icon: <BookOpen size={24} /> },
              { label: 'Wiki Notes', value: stats.total_wiki_notes || 0, icon: <BookOpen size={24} /> },
              { label: 'Clusters', value: stats.total_clusters || 0, icon: <Network size={24} /> },
            ]}
          />
        )}

        {/* Navigation Grid */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Navigate to</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href}>
                  <Card hover className="h-full">
                    <div className="p-4 flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.color}`}>
                        <Icon size={24} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{item.label}</h3>
                      </div>
                      <ArrowRight size={16} className="text-gray-400" />
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Project Info */}
        {project.description && (
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">About</h3>
              <p className="text-gray-600">{project.description}</p>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
}
