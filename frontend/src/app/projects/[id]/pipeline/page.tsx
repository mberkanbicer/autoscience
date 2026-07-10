'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Paper, PaperCluster, ClusterConflict, ResearchQuestion, Hypothesis } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { projectsApi, runsApi, ideasApi, papersApi, questionsApi, hypothesesApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  ArrowBigLeft,
  BarChart3,
  CheckCircle,
  Activity,
  Target,
  Cpu,
  FileSearch,
  FileText,
  FlaskConical,
  GitBranch,
  Lightbulb,
  MessageSquare,
  Network,
  Star,
  AlertTriangle,
  Clock,
  ArrowRight,
  Loader2,
} from 'lucide-react';

interface StageDataItem {
  id?: string;
  title?: string;
  name?: string;
  statement?: string;
  description?: string;
  subtitle?: string;
  authors?: string | string[];
  paper_count?: number;
  confidence?: number;
  overall_score?: number;
  score?: number | null;
  has_validation_plan?: boolean;
  status?: string;
  source?: string;
  conflict_type?: string;
  severity?: number;
}

interface PipelineStage {
  id: string;
  name: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  description: string;
  count: number;
  items: StageDataItem[];
  status: 'idle' | 'active' | 'completed' | 'error';
}

export default function PipelinePage() {
  const params = useParams();
  const projectId = params.id as string;
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  useEffect(() => {
    loadPipelineData();
    const interval = setInterval(loadPipelineData, 10000);
    return () => clearInterval(interval);
  }, [projectId]);

  const loadPipelineData = async () => {
    try {
      const [ideas, runs, papers, questions, hypotheses, clusters, conflicts] = await Promise.all([
        ideasApi.list(projectId),
        runsApi.list(projectId),
        papersApi.list(projectId),
        questionsApi.list(projectId),
        hypothesesApi.list(projectId),
        papersApi.clusters(projectId).catch(() => []),
        papersApi.conflicts(projectId).catch(() => []),
      ]);

      const latestRun = runs[0];
      const isRunning = latestRun?.state === 'running';

      const formatAuthors = (authors: string | string[] | undefined | null): string => {
        if (!authors) return 'Unknown';
        if (Array.isArray(authors)) return authors.length > 0 ? authors.join(', ') : 'Unknown';
        return String(authors);
      };

      const pipelineStages: PipelineStage[] = [
        {
          id: 'ideas',
          name: 'Ideas',
          icon: Lightbulb,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          description: 'Research ideas and hypotheses to explore',
          count: ideas.length,
          items: ideas.map((i) => ({
            id: i.id,
            title: i.current_text || i.initial_text || 'Untitled',
            subtitle: `Score: ${i.overall_score != null ? (i.overall_score * 100).toFixed(0) + '%' : 'N/A'}`,
            status: i.status,
          })),
          status: ideas.length > 0 ? 'completed' : 'idle',
        },
        {
          id: 'literature',
          name: 'Literature Search',
          icon: FileSearch,
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          description: 'Academic papers found from 5 sources',
          count: papers.length,
          items: papers.slice(0, 10).map((p) => ({
            id: p.id,
            title: p.title,
            subtitle: `${formatAuthors(p.authors)} (${p.year || 'N/A'})`,
            score: p.citation_count,
          })),
          status: papers.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'analysis',
          name: 'Paper Analysis',
          icon: BarChart3,
          color: 'text-purple-600',
          bgColor: 'bg-purple-100',
          description: 'Structured extraction from papers',
          count: papers.length,
          items: papers.slice(0, 5).map((p) => ({
            id: p.id,
            title: p.title,
            subtitle: p.abstract ? `Abstract available` : 'No abstract',
          })),
          status: papers.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'clustering',
          name: 'Clustering',
          icon: Network,
          color: 'text-indigo-600',
          bgColor: 'bg-indigo-100',
          description: 'Papers grouped by theme',
count: clusters.length,
           items: clusters.slice(0, 5).map((c: PaperCluster) => ({
             id: c.id,
             title: c.name || 'Unnamed cluster',
             subtitle: c.description || `${c.paper_ids?.length || 0} papers`,
           })),
          status: clusters.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'conflicts',
          name: 'Conflict Detection',
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          description: 'Contradictions between papers',
count: conflicts.length,
           items: conflicts.slice(0, 5).map((c: ClusterConflict) => ({
             id: c.id,
             title: c.conflict_type || 'Conflict',
             subtitle: c.description || '',
             score: c.severity,
           })),
          status: conflicts.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'questions',
          name: 'Research Questions',
          icon: MessageSquare,
          color: 'text-teal-600',
          bgColor: 'bg-teal-100',
          description: 'Generated research questions',
          count: questions.length,
          items: questions.slice(0, 5).map((q) => ({
            id: q.id,
            title: q.question || 'Untitled question',
            subtitle: q.rank ? `Priority: ${(q.rank * 100).toFixed(0)}%` : '',
          })),
          status: questions.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'hypotheses',
          name: 'Hypotheses',
          icon: FlaskConical,
          color: 'text-violet-600',
          bgColor: 'bg-violet-100',
          description: 'Testable hypotheses formed',
          count: hypotheses.length,
          items: hypotheses.slice(0, 5).map((h) => ({
            id: h.id,
            title: h.statement || 'Untitled hypothesis',
            subtitle: h.confidence != null ? `Confidence: ${(h.confidence * 100).toFixed(0)}%` : '',
          })),
          status: hypotheses.length > 0 ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'scoring',
          name: 'Idea Scoring',
          icon: Star,
          color: 'text-amber-600',
          bgColor: 'bg-amber-100',
          description: '12-dimension idea evaluation',
          count: ideas.filter((i) => i.overall_score != null).length,
          items: ideas.filter((i) => i.overall_score != null).slice(0, 3).map((i) => ({
            id: i.id,
            title: (i.current_text || i.initial_text || '').slice(0, 60) + ((i.current_text?.length || 0) > 60 ? '...' : ''),
            subtitle: `Score: ${(i.overall_score! * 100).toFixed(0)}% | ${i.classification || 'unclassified'}`,
          })),
          status: ideas.some((i) => i.overall_score != null) ? 'completed' : 'idle',
        },
        {
          id: 'validation',
          name: 'Validation Plan',
          icon: Target,
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-100',
description: 'Experimental validation design',
           count: hypotheses.filter((h: Hypothesis) => (h as any).validation_plans?.length > 0).length,
           items: hypotheses.filter((h: Hypothesis) => (h as any).validation_plans?.length > 0).slice(0, 3).map((h) => ({
             id: h.id,
             title: (h.statement || '').slice(0, 60),
             subtitle: 'Validation plan available',
           })),
           status: hypotheses.some((h: Hypothesis) => (h as any).validation_plans?.length > 0) ? 'completed' : isRunning ? 'active' : 'idle',
        },
      ];

      setStages(pipelineStages);
    } catch (error) {
      console.error('Failed to load pipeline data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={18} className="text-success" />;
      case 'active':
        return <Loader2 size={18} className="text-primary animate-spin" />;
      case 'error':
        return <AlertTriangle size={18} className="text-error" />;
      default:
        return <Clock size={18} className="text-muted-foreground/30" />;
    }
  };

  const selectedStageData = stages.find(s => s.id === selectedStage);

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Pipeline"
        subtitle="Trace the full research flow from idea to hypothesis"
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : stages.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-8 h-8 text-gray-400" />}
            title="No pipeline data"
            description="Start a research run to see the pipeline in action."
          />
        ) : (
          <div className="space-y-6">
            {/* Pipeline Flow */}
            <div className="flex flex-wrap items-center gap-4 bg-white/40 backdrop-blur-sm p-6 rounded-2xl border border-border/10 shadow-inner">
              {stages.map((stage, idx) => {
                const Icon = stage.icon;
                const isSelected = selectedStage === stage.id;
                return (
                  <div key={stage.id} className="flex items-center">
                    <button
                      onClick={() => setSelectedStage(selectedStage === stage.id ? null : stage.id)}
                      className={cn(
                        'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-500 hover:scale-105',
                        isSelected
                          ? 'ring-2 ring-primary/40 bg-white shadow-lg'
                          : 'hover:bg-white/60'
                      )}
                    >
                      <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500 shadow-inner', isSelected ? 'bg-primary text-white' : stage.bgColor)}>
                        <Icon size={20} className={isSelected ? 'text-white' : stage.color} />
                      </div>
                      <div className="text-left">
                        <div className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest leading-none mb-1">{stage.name}</div>
                        <div className="text-sm font-bold text-foreground tracking-tight">{stage.count}</div>
                      </div>
                      <div className="ml-2">
                         {getStatusIcon(stage.status)}
                      </div>
                    </button>
                    {idx < stages.length - 1 && (
                      <div className="flex items-center mx-1">
                         <div className="w-4 h-px bg-border/20" />
                         <ArrowRight size={14} className="text-muted-foreground/20" />
                         <div className="w-4 h-px bg-border/20" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Stage Details */}
            {selectedStageData && (
              <Card className="glass animate-in slide-in-from-top-6 duration-700">
                <div className="p-8">
                  <div className="flex items-center gap-4 mb-8">
                    <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner', selectedStageData.bgColor)}>
                      <selectedStageData.icon size={28} className={selectedStageData.color} />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-foreground tracking-tight">{selectedStageData.name}</h3>
                      <p className="text-sm font-medium text-muted-foreground mt-1">{selectedStageData.description}</p>
                    </div>
                    <div className="ml-auto">
                      <Badge variant={selectedStageData.status === 'completed' ? 'success' : selectedStageData.status === 'active' ? 'info' : 'default'} className="uppercase text-[10px] font-bold tracking-widest px-3 py-1 bg-opacity-10">
                        {selectedStageData.status}
                      </Badge>
                    </div>
                  </div>

                  {selectedStageData.items.length === 0 ? (
                    <div className="py-12 text-center border-2 border-dashed border-border/10 rounded-2xl">
                       <p className="text-sm font-bold text-muted-foreground/30 uppercase tracking-widest text-sm italic">No intellectual artifacts at this stage</p>
                    </div>
                  ) : (
                    <div className="grid gap-3">
                      {selectedStageData.items.map((item: StageDataItem) => (
                        <div key={item.id} className="flex items-center justify-between p-4 bg-white/40 backdrop-blur-sm border border-border/5 rounded-xl hover:bg-white/60 transition-all duration-300 group">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-foreground/80 truncate tracking-tight">{item.title}</p>
                            {item.subtitle && (
                              <p className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest mt-1.5">{item.subtitle}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                             {item.score != null && (
                               <div className="px-2 py-0.5 bg-primary/5 rounded-md border border-primary/10">
                                 <span className="text-[10px] font-bold text-primary">
                                   {typeof item.score === 'number' ? item.score.toFixed(2) : item.score}
                                 </span>
                               </div>
                             )}
                             {item.status && (
                               <Badge variant={item.status === 'active' || item.status === 'running' ? 'success' : 'default'} size="sm" className="bg-opacity-10 text-[9px] uppercase font-bold tracking-tighter">
                                 {item.status}
                               </Badge>
                             )}
                             <ArrowRight size={14} className="text-muted-foreground/0 group-hover:text-muted-foreground/20 transition-all group-hover:translate-x-1" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Pipeline Summary */}
            <Card className="glass overflow-hidden border-border/5">
              <div className="p-8">
                <div className="flex items-center gap-3 mb-8">
                   <div className="p-2 bg-muted rounded-lg border border-border/10">
                      <BarChart3 size={18} className="text-muted-foreground/60" />
                   </div>
                   <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em]">Intellectual Velocity Summary</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-6">
                  {[
                    { id: 'ideas', label: 'Ideas', color: 'text-yellow-600' },
                    { id: 'literature', label: 'Papers', color: 'text-blue-600' },
                    { id: 'clustering', label: 'Clusters', color: 'text-indigo-600' },
                    { id: 'conflicts', label: 'Conflicts', color: 'text-red-600' },
                    { id: 'questions', label: 'Questions', color: 'text-teal-600' },
                    { id: 'hypotheses', label: 'Hypotheses', color: 'text-violet-600' },
                    { id: 'scoring', label: 'Scored', color: 'text-amber-600' },
                    { id: 'validation', label: 'Validated', color: 'text-emerald-600' }
                  ].map(stat => (
                    <div key={stat.id} className="text-center group transition-all duration-500 hover:-translate-y-1">
                      <div className={cn("text-3xl font-extrabold mb-1 tracking-tight transition-colors duration-500", stat.color)}>
                        {stages.find(s => s.id === stat.id)?.count || 0}
                      </div>
                      <div className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest group-hover:text-muted-foreground transition-colors">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
}
