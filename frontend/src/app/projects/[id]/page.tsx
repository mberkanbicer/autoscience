'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { projectsApi } from '@/lib/api';
import { Project, ProjectStats } from '@/lib/types';
import { formatDate } from '@/lib/utils';

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
      <Layout>
        <div className="p-6 text-center">Loading...</div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout>
        <div className="p-6 text-center">Project not found</div>
      </Layout>
    );
  }

  const navItems = [
    { name: 'Ideas', href: `/projects/${projectId}/ideas`, icon: '💡' },
    { name: 'Runs', href: `/projects/${projectId}/runs`, icon: '🔄' },
    { name: 'Papers', href: `/projects/${projectId}/papers`, icon: '📄' },
    { name: 'Questions', href: `/projects/${projectId}/questions`, icon: '❓' },
    { name: 'Hypotheses', href: `/projects/${projectId}/hypotheses`, icon: '🔬' },
    { name: 'Skills', href: `/projects/${projectId}/skills`, icon: '🛠️' },
    { name: 'Reports', href: `/projects/${projectId}/reports`, icon: '📊' },
    { name: 'Wiki', href: `/projects/${projectId}/wiki`, icon: '📚' },
    { name: 'Settings', href: `/projects/${projectId}/settings`, icon: '⚙️' },
  ];

  return (
    <Layout>
      <Header title={project.name} />

      <div className="p-6">
        {/* Project Info */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h2 className="text-lg font-semibold mb-2">Project Details</h2>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm text-gray-500">Domain</dt>
                  <dd className="text-sm font-medium">{project.domain}</dd>
                </div>
                {project.description && (
                  <div>
                    <dt className="text-sm text-gray-500">Description</dt>
                    <dd className="text-sm">{project.description}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm text-gray-500">Created</dt>
                  <dd className="text-sm">{formatDate(project.created_at)}</dd>
                </div>
              </dl>
            </div>
            <div>
              <h2 className="text-lg font-semibold mb-2">Settings</h2>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm text-gray-500">Default Flexibility</dt>
                  <dd className="text-sm">{project.default_flexibility}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Idle Research</dt>
                  <dd className="text-sm">
                    {project.idle_research_enabled ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Idle Trigger</dt>
                  <dd className="text-sm">{project.idle_trigger_minutes} minutes</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.total_ideas}</div>
              <div className="text-sm text-gray-500">Ideas</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{stats.total_papers}</div>
              <div className="text-sm text-gray-500">Papers</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.total_runs}</div>
              <div className="text-sm text-gray-500">Runs</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <div className="text-3xl font-bold text-orange-600">{stats.total_questions}</div>
              <div className="text-sm text-gray-500">Questions</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <div className="text-3xl font-bold text-red-600">{stats.total_hypotheses}</div>
              <div className="text-sm text-gray-500">Hypotheses</div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition flex items-center gap-3"
            >
              <span className="text-2xl">{item.icon}</span>
              <span className="font-medium">{item.name}</span>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
