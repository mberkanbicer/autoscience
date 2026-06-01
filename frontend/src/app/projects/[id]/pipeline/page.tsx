'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { projectsApi, runsApi, ideasApi, papersApi, questionsApi, hypothesesApi } from '@/lib/api';
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
          items: clusters.slice(0, 5).map((c: any) => ({
            id: c.id,
            title: c.name || 'Unnamed cluster',
            subtitle: c.description || `${c.paper_count || 0} papers`,
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
          items: conflicts.slice(0, 5).map((c: any) => ({
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
          count: hypotheses.filter((h: any) => h.has_validation_plan).length,
          items: hypotheses.filter((h: any) => h.has_validation_plan).slice(0, 3).map((h) => ({
            id: h.id,
            title: (h.statement || '').slice(0, 60),
            subtitle: 'Validation plan available',
          })),
          status: hypotheses.some((h: any) => h.has_validation_plan) ? 'completed' : isRunning ? 'active' : 'idle',
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
        return <CheckCircle size={20} className="text-green-600" />;
      case 'active':
        return <Loader2 size={20} className="text-blue-600 animate-spin" />;
      case 'error':
        return <AlertTriangle size={20} className="text-red-600" />;
      default:
        return <Clock size={20} className="text-gray-400" />;
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
            <div className="flex flex-wrap items-center gap-2">
              {stages.map((stage, idx) => {
                const Icon = stage.icon;
                return (
                  <div key={stage.id} className="flex items-center">
                    <button
                      onClick={() => setSelectedStage(selectedStage === stage.id ? null : stage.id)}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                        selectedStage === stage.id
                          ? 'ring-2 ring-blue-500 bg-blue-50'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${stage.bgColor}`}>
                        <Icon size={16} className={stage.color} />
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-medium text-gray-900">{stage.name}</div>
                        <div className="text-xs text-gray-500">{stage.count}</div>
                      </div>
                      {getStatusIcon(stage.status)}
                    </button>
                    {idx < stages.length - 1 && (
                      <ArrowRight size={16} className="text-gray-300 mx-1" />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Stage Details */}
            {selectedStageData && (
              <Card>
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${selectedStageData.bgColor}`}>
                      <selectedStageData.icon size={20} className={selectedStageData.color} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{selectedStageData.name}</h3>
                      <p className="text-sm text-gray-600">{selectedStageData.description}</p>
                    </div>
                    <div className="ml-auto">
                      <Badge variant={selectedStageData.status === 'completed' ? 'success' : selectedStageData.status === 'active' ? 'info' : 'default'}>
                        {selectedStageData.status}
                      </Badge>
                    </div>
                  </div>

                  {selectedStageData.items.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No items at this stage yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {selectedStageData.items.map((item: StageDataItem) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                            {item.subtitle && (
                              <p className="text-xs text-gray-500">{item.subtitle}</p>
                            )}
                          </div>
                          {item.score != null && (
                            <Badge variant="info" size="sm">
                              {typeof item.score === 'number' ? item.score.toFixed(2) : item.score}
                            </Badge>
                          )}
                          {item.status && (
                            <Badge variant={item.status === 'active' || item.status === 'running' ? 'success' : 'default'} size="sm">
                              {item.status}
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Pipeline Summary */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Summary</h3>
                <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {stages.find(s => s.id === 'ideas')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Ideas</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {stages.find(s => s.id === 'literature')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Papers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-indigo-600">
                      {stages.find(s => s.id === 'clustering')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Clusters</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {stages.find(s => s.id === 'conflicts')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Conflicts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-teal-600">
                      {stages.find(s => s.id === 'questions')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Questions</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-violet-600">
                      {stages.find(s => s.id === 'hypotheses')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Hypotheses</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-amber-600">
                      {stages.find(s => s.id === 'scoring')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Scored</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-600">
                      {stages.find(s => s.id === 'validation')?.count || 0}
                    </div>
                    <div className="text-xs text-gray-600">Validated</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
}
