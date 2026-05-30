'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Input, Textarea } from '@/components/ui/Input';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { projectsApi } from '@/lib/api';
import { Project } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Plus, FolderKanban, ArrowRight, Loader2 } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    domain: '',
    description: '',
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await projectsApi.list();
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newProject.name || !newProject.domain) return;
    setCreating(true);
    try {
      await projectsApi.create(newProject);
      setShowCreateModal(false);
      setNewProject({ name: '', domain: '', description: '' });
      loadProjects();
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Layout>
      <Header
        title="Projects"
        subtitle="Manage your research projects"
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus size={18} className="mr-2" />
            New Project
          </Button>
        }
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <EmptyState
            icon={<FolderKanban className="w-8 h-8 text-gray-400" />}
            title="No projects yet"
            description="Create your first research project to get started with autonomous research."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus size={18} className="mr-2" />
                Create Project
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <Card hover className="h-full">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                        <FolderKanban className="text-white" size={24} />
                      </div>
                      <Badge variant={project.idle_research_enabled ? 'success' : 'default'}>
                        {project.idle_research_enabled ? 'Idle Active' : 'Idle Off'}
                      </Badge>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{project.name}</h3>
                    <p className="text-sm text-gray-500 mb-4">{project.domain}</p>
                    {project.description && (
                      <p className="text-sm text-gray-600 line-clamp-2 mb-4">{project.description}</p>
                    )}
                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <span>Created {formatDate(project.created_at)}</span>
                      <ArrowRight size={16} className="text-blue-500" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Project"
      >
        <div className="space-y-4">
          <Input
            label="Project Name"
            placeholder="e.g., AI Research Initiative"
            value={newProject.name}
            onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
          />
          <Input
            label="Domain"
            placeholder="e.g., machine learning, computational biology"
            value={newProject.domain}
            onChange={(e) => setNewProject({ ...newProject, domain: e.target.value })}
          />
          <Textarea
            label="Description"
            placeholder="Brief description of your research focus..."
            rows={3}
            value={newProject.description}
            onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} loading={creating}>
            Create Project
          </Button>
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
