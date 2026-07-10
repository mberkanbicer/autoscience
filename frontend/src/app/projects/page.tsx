'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ProjectCreationWizard } from '@/components/ui/ProjectCreationWizard';
import { projectsApi, researchApi } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import { Plus, FolderKanban, ArrowRight, Trash2, AlertCircle } from 'lucide-react';

const queryKeys = {
  projects: ['projects'] as const,
};

export default function ProjectsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: projects = [], isLoading } = useQuery({
    queryKey: queryKeys.projects,
    queryFn: projectsApi.list,
    staleTime: 30000,
  });

  const { mutate: createProject, isPending: isCreating } = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: async (newProject) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      
      // Automatically start the first research cycle using the project description as intent
      try {
        await researchApi.start({
          project_id: newProject.id,
          idea: newProject.description || `Initial discovery for ${newProject.name}`,
          run_type: 'user_directed',
          flexibility: newProject.default_flexibility || 0.6,
        });
        
        setShowCreateModal(false);
        // Redirect to the new project's dashboard or runs view
        window.location.href = `/projects/${newProject.id}/runs`;
      } catch (err) {
        console.error('Failed to ignite initial cycle:', err);
        setShowCreateModal(false);
        window.location.href = `/projects/${newProject.id}`;
      }
    },
  });

  const { mutate: deleteProject, isPending: isDeleting } = useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
    onError: (error) => {
      console.error('Delete failed:', error);
      alert(`Failed to delete project: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const handleCreate = (data: any) => {
    createProject(data);
  };

  const handleDelete = (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      deleteProject(id);
    }
  };

  return (
    <Layout>
      <Header
        title="Active Lab Units"
        subtitle="Manage autonomous research instances"
        actions={
          <Button 
            variant="primary" 
            className="rounded-2xl px-8 py-6 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 group"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus className="mr-2 group-hover:rotate-90 transition-transform duration-500" size={16} /> 
            New Laboratory Unit
          </Button>
        }
      />

      <div className="p-10">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <Card className="glass p-20 text-center border-border/5">
            <div className="mb-8 text-muted-foreground">
              <FolderKanban className="w-20 h-20 text-stone-200 dark:text-stone-800 mx-auto" />
            </div>
            <h3 className="text-2xl font-black text-foreground tracking-tighter uppercase mb-4">No active lab units</h3>
            <p className="mt-2 text-muted-foreground font-medium max-w-sm mx-auto leading-relaxed mb-10">
              Initialize your first research unit to begin autonomous scientific synthesis.
            </p>
            <Button 
              variant="primary" 
              className="rounded-2xl px-12 py-6 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={18} className="mr-2" />
              Initialize Unit
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {projects.map((project) => (
              <div key={project.id} className="relative group">
                <Link href={`/projects/${project.id}`}>
                  <Card hover className="h-full cursor-pointer overflow-hidden border-border/5">
                    <div className="p-8">
                      <div className="flex items-start justify-between mb-8">
                        <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center shadow-inner group-hover:bg-primary group-hover:text-stone-900 transition-all duration-500 group-hover:rotate-6">
                          <FolderKanban size={32} />
                        </div>
                        <Badge variant={project.idle_research_enabled ? 'success' : 'default'} className={cn("uppercase text-[8px] font-black tracking-widest px-3 py-1", project.idle_research_enabled ? 'bg-success/10 border-success/20' : 'bg-stone-100')}>
                          {project.idle_research_enabled ? 'Idle Cognition Active' : 'Offline'}
                        </Badge>
                      </div>
                      <h3 className="text-2xl font-black text-foreground mb-2 tracking-tighter leading-tight group-hover:text-primary transition-colors">{project.name}</h3>
                      <p className="text-[10px] font-black text-muted-foreground/40 uppercase tracking-[0.2em] mb-6">{project.domain}</p>
                      {project.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-8 leading-relaxed font-medium">{project.description}</p>
                      )}
                      <div className="flex items-center justify-between pt-6 border-t border-border/5">
                        <div className="flex flex-col">
                           <span className="text-[8px] font-black text-muted-foreground/30 uppercase tracking-widest mb-1">Established</span>
                           <span className="text-xs font-black text-foreground/60">{new Date(project.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="p-3 bg-primary/5 rounded-xl group-hover:bg-primary group-hover:text-stone-900 transition-all duration-500 group-hover:translate-x-1">
                          <ArrowRight size={18} />
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
                <button
                  type="button"
                  className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity p-2 text-muted-foreground hover:text-error disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDelete(project.id, project.name);
                  }}
                  disabled={isDeleting}
                  title="Decommission unit"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Initialize New Research Foundry"
        size="lg"
      >
        <ProjectCreationWizard
          onStart={handleCreate}
          onClose={() => setShowCreateModal(false)}
          isSubmitting={isCreating}
        />
      </Modal>
    </Layout>
  );
}
