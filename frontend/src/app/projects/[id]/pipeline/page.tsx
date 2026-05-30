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
  Lightbulb,
  FileSearch,
  BarChart3,
  Network,
  AlertTriangle,
  MessageSquare,
  FlaskConical,
  Star,
  CheckCircle2,
  Clock,
  ArrowRight,
  Loader2,
  Activity,
} from 'lucide-react';

interface PipelineStage {
  id: string;
  name: string;
  icon: any;
  color: string;
  bgColor: string;
  description: string;
  count: number;
  items: any[];
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
  }, [projectId]);

  const loadPipelineData = async () => {
    try {
      const [ideas, runs, papers, questions, hypotheses] = await Promise.all([
        ideasApi.list(projectId),
        runsApi.list(projectId),
        papersApi.list(projectId),
        questionsApi.list(projectId),
        hypothesesApi.list(projectId),
      ]);

      // Find latest run
      const latestRun = runs[0];
      const isRunning = latestRun?.state === 'running';

      const pipelineStages: PipelineStage[] = [
        {
          id: 'ideas',
          name: 'Ideas',
          icon: Lightbulb,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          description: 'Research ideas and hypotheses to explore',
          count: ideas.length,
          items: ideas.map(i => ({
            id: i.id,
            title: i.current_text || i.initial_text,
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
          items: papers.slice(0, 10).map(p => ({
            id: p.id,
            title: p.title,
            subtitle: `${p.authors || 'Unknown'} (${p.year || 'N/A'})`,
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
          count: papers.filter((p: any) => p.analysis).length,
          items: papers.filter((p: any) => p.analysis).slice(0, 5).map((p: any) => ({
            id: p.id,
            title: p.title,
            subtitle: `Methods: ${p.analysis.methods?.length || 0} | Findings: ${p.analysis.findings?.length || 0}`,
          })),
          status: papers.some((p: any) => p.analysis) ? 'completed' : isRunning ? 'active' : 'idle',
        },
        {
          id: 'clustering',
          name: 'Clustering',
          icon: Network,
          color: 'text-indigo-600',
          bgColor: 'bg-indigo-100',
          description: 'Papers grouped by theme',
          count: 0, // Would need cluster data
          items: [],
          status: papers.length > 5 ? 'completed' : 'idle',
        },
        {
          id: 'conflicts',
          name: 'Conflict Detection',
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          description: 'Contradictions between papers',
          count: 0, // Would need conflict data
          items: [],
          status: isRunning ? 'active' : 'idle',
        },
        {
          id: 'questions',
          name: 'Research Questions',
          icon: MessageSquare,
          color: 'text-teal-600',
          bgColor: 'bg-teal-100',
          description: 'Generated research questions',
          count: questions.length,
          items: questions.slice(0, 5).map(q => ({
            id: q.id,
            title: q.text || q.question,
            subtitle: q.priority ? `Priority: ${q.priority}` : '',
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
          items: hypotheses.slice(0, 5).map(h => ({
            id: h.id,
            title: h.statement || h.text,
            subtitle: h.testability ? `Testability: ${(h.testability * 100).toFixed(0)}%` : '',
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
          count: ideas.filter(i => i.overall_score != null).length,
          items: ideas.filter(i => i.overall_score != null).slice(0, 3).map(i => ({
            id: i.id,
            title: i.current_text?.slice(0, 60) + '...',
            subtitle: `Score: ${(i.overall_score! * 100).toFixed(0)}% | ${i.classification || 'unclassified'}`,
          })),
          status: ideas.some(i => i.overall_score != null) ? 'completed' : 'idle',
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
        return <CheckCircle2 size={20} className="text-green-600" />;
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
                      {selectedStageData.items.map((item) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                            {item.subtitle && (
                              <p className="text-xs text-gray-500">{item.subtitle}</p>
                            )}
                          </div>
                          {item.score != null && (
                            <Badge variant="info" size="sm">
                              {item.score}
                            </Badge>
                          )}
                          {item.status && (
                            <Badge variant={item.status === 'active' ? 'success' : 'default'} size="sm">
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
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
}
