'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StatsGrid } from '@/components/ui/StatCard';
import { SkeletonStats } from '@/components/ui/Skeleton';
import { ErrorDisplay, LoadingSpinner } from '@/components/ui/LoadState';
import { projectsApi, runsApi, researchApi } from '@/lib/api';
import { isLlmConfigured, refreshApiSettings } from '@/lib/apiSettings';
import { Project, ProjectStats, ResearchRun } from '@/lib/types';
import { cn } from '@/lib/utils';
import { DiscoveryWizard } from '@/components/ui/DiscoveryWizard';
import { Modal } from '@/components/ui/Modal';
import { FocusMetric } from '@/components/ui/FocusMetric';

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
  Brain,
  Plus,
  Layers,
  History,
  CheckCircle,
  Zap,
  FileText,
} from 'lucide-react';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [latestRun, setLatestRun] = useState<ResearchRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasApiKey, setHasApiKey] = useState(true);
  
  const [showRunWizard, setShowRunWizard] = useState(false);

  const loadProject = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectData, statsData, runsData] = await Promise.all([
        projectsApi.get(projectId),
        projectsApi.stats(projectId),
        runsApi.list(projectId, { limit: '1', state: 'completed' })
      ]);
      setProject(projectData);
      setStats(statsData);
      setLatestRun(runsData[0] || null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load project';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
    // Check if any API key is configured
    refreshApiSettings().finally(() => setHasApiKey(isLlmConfigured()));
  }, [loadProject]);

  const handleStartRun = async (config: any) => {
    try {
      await researchApi.start({
        project_id: projectId,
        idea: config.topic,
        run_type: 'user_directed',
        flexibility: config.flexibility,
      });
      setShowRunWizard(false);
      // Redirect to runs page
      window.location.href = `/projects/${projectId}/runs`;
    } catch (err) {
      console.error('Failed to start run:', err);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Synchronizing Lab..." />
        <div className="p-10">
          <SkeletonStats />
        </div>
      </Layout>
    );
  }

  if (error || !project) {
    return (
      <Layout projectId={projectId}>
        <Header title="Error" />
        <div className="p-10">
          <ErrorDisplay message={error || 'Project not found'} onRetry={loadProject} />
        </div>
      </Layout>
    );
  }

  const navItems = [
    { href: `/projects/${projectId}/ideas`, label: 'Ideas', icon: Lightbulb, color: 'text-primary bg-primary/5' },
    { href: `/projects/${projectId}/runs`, label: 'Research Runs', icon: Activity, color: 'text-success bg-success/5' },
    { href: `/projects/${projectId}/papers`, label: 'Literature', icon: FileSearch, color: 'text-primary bg-primary/5' },
    { href: `/projects/${projectId}/clusters`, label: 'Clusters', icon: Layers, color: 'text-tertiary bg-tertiary/5' },
    { href: `/projects/${projectId}/wiki`, label: 'Wiki', icon: BookOpen, color: 'text-warning bg-warning/5' },
    { href: `/projects/${projectId}/manuscripts`, label: 'Manuscripts', icon: FileText, color: 'text-success bg-success/5' },
  ];

  return (
    <Layout projectId={projectId}>
      <Header
        title={project.name}
        subtitle={project.domain}
        actions={
          <Button 
            variant="primary" 
            className="rounded-2xl px-8 py-6 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 group"
            onClick={() => setShowRunWizard(true)}
          >
            <Plus className="mr-2 group-hover:rotate-90 transition-transform duration-500" size={16} /> 
            Initialize Discovery Wizard
          </Button>
        }
      />

      <div className="p-10 space-y-12 animate-in fade-in zoom-in-95 duration-1000">
        {/* Research Wizard Modal */}
        <Modal
          isOpen={showRunWizard}
          onClose={() => setShowRunWizard(false)}
          title="Autonomous Research Wizard"
          size="lg"
        >
           <DiscoveryWizard 
            projectId={projectId} 
            onStart={handleStartRun} 
            onClose={() => setShowRunWizard(false)} 
           />
        </Modal>

        {/* Cognitive Health Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           <Card className="lg:col-span-2 p-10 glass border-border/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-10 opacity-[0.03] group-hover:opacity-[0.08] transition-all duration-1000 group-hover:scale-110">
                 <Brain size={120} />
              </div>
              <div className="relative z-10 flex flex-col h-full">
                 <div className="flex items-center gap-2 mb-8">
                    <div className="p-2 bg-primary/10 rounded-lg">
                       <Zap size={18} className="text-primary" />
                    </div>
                    <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em]">Cognitive Health</h3>
                 </div>
                 
                 <div className="flex-1 space-y-8">
                    <div className="flex items-end justify-between">
                       <div>
                          <p className="text-4xl font-black text-foreground tracking-tighter">Research Entropy</p>
                          <p className="text-muted-foreground font-medium mt-1">
                             {stats?.latest_cognitive_mode === 'exploration' 
                               ? "Broad search mode: scanning unknown frontiers." 
                               : stats?.latest_cognitive_entropy && stats.latest_cognitive_entropy < 0.3
                               ? "Focused mode: deep exploitation of specific findings."
                               : "Balanced research focus."}
                          </p>
                       </div>
                       <div className="text-right">
                          <span className="text-5xl font-black text-primary tracking-tighter">{Math.round((stats?.latest_cognitive_entropy || 0.5) * 100)}%</span>
                       </div>
                    </div>
                    
                    <div className="h-4 w-full bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden p-1 shadow-inner">
                       <div 
                        className="h-full bg-primary rounded-full shadow-[0_0_20px_rgba(217,119,6,0.4)] transition-all duration-1000 ease-out" 
                        style={{ width: `${(stats?.latest_cognitive_entropy || 0.5) * 100}%` }}
                       />
                    </div>

                    {/* Focus Metric */}
                    <div className="mt-6 pt-6 border-t border-border/10">
                      <FocusMetric
                        focusScore={stats?.latest_focus_score ?? (stats?.latest_cognitive_entropy != null ? 1 - stats.latest_cognitive_entropy : 0.5)}
                        focusLabel={(stats?.latest_focus_label as any) || undefined}
                        size="md"
                      />
                    </div>
                 </div>
              </div>
           </Card>

           <div className="space-y-6">
              <Card className="p-8 glass-panel border-border/5 flex flex-col justify-between h-full group hover:border-primary/20 transition-all duration-500">
                 <div className="space-y-4">
                    <div className="p-3 w-fit bg-primary/10 rounded-xl text-primary group-hover:rotate-6 transition-transform">
                       <History size={20} />
                    </div>
                    <h4 className="font-black uppercase tracking-widest text-foreground text-xs">Synthesis Foundry</h4>
                    <p className="text-[11px] text-muted-foreground font-medium leading-relaxed">
                       Access the high-fidelity workspace for your latest results. Refine manuscripts and map connections.
                    </p>
                 </div>
                 <div className="space-y-3 mt-6">
                    {latestRun && (
                      <Link href={`/projects/${projectId}/studio/${latestRun.id}`}>
                        <Button variant="primary" size="sm" className="w-full rounded-xl text-[9px] font-black uppercase tracking-widest shadow-lg shadow-primary/20">
                           Open Study Studio
                        </Button>
                      </Link>
                    )}
                    <Link href={`/projects/${projectId}/runs`}>
                       <Button variant="ghost" size="sm" className="w-full rounded-xl text-[9px] font-black uppercase tracking-widest border border-border/10 bg-white dark:bg-stone-800 shadow-sm">
                          View All Cycles
                       </Button>
                    </Link>
                 </div>
              </Card>
           </div>
        </div>

        {/* Dashboard Stats */}
        <div className="space-y-6">
          <div className="flex items-center gap-3">
             <div className="w-8 h-px bg-primary/20" />
             <h2 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Laboratory Metrics</h2>
          </div>
          <StatsGrid
            stats={[
              { label: 'Identified Ideas', value: stats?.total_ideas || 0, icon: <Lightbulb size={20} /> },
              { label: 'Literature Corpus', value: stats?.total_papers || 0, icon: <FileSearch size={20} /> },
              { label: 'Thematic Clusters', value: stats?.total_clusters || 0, icon: <Layers size={20} /> },
              { label: 'Active Tensions', value: stats?.total_conflicts || 0, icon: <GitBranch size={20} />, change: stats?.total_conflicts ? -12 : undefined },
            ]}
          />
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href}>
                <Card hover className="p-6 text-center group cursor-pointer border-border/5 h-full flex flex-col items-center justify-center gap-4 transition-all duration-500">
                  <div className={cn("p-4 rounded-2xl transition-all duration-500 group-hover:scale-110 group-hover:rotate-6 shadow-inner", item.color)}>
                    <Icon size={24} />
                  </div>
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground group-hover:text-primary transition-colors">
                    {item.label}
                  </span>
                </Card>
              </Link>
            );
          })}
        </div>

        {/* Abstract Section */}
        {project.description && (
          <Card className="glass p-12 relative overflow-hidden border-border/5">
            <div className="absolute top-0 right-0 p-8 opacity-[0.02]">
               <FileSearch size={160} />
            </div>
            <div className="relative z-10 max-w-3xl">
              <h3 className="text-[10px] font-black text-primary uppercase tracking-[0.3em] mb-4">Scientific Abstract</h3>
              <p className="text-foreground/80 leading-relaxed font-medium">{project.description}</p>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
}
