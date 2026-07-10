'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { CognitiveEntropy } from '@/components/ui/CognitiveEntropy';
import { runsApi, projectsApi, manuscriptsApi, papersApi, hypothesesApi } from '@/lib/api';
import { ResearchRun, Project, Paper, PaperCluster, ClusterConflict, Manuscript, Hypothesis } from '@/lib/types';
import { KnowledgeGraph } from '@/components/ui/KnowledgeGraph';
import { KnowledgeCard } from '@/components/ui/KnowledgeCard';
import { LaTeXPrism } from '@/components/ui/LaTeXPrism';
import { GenerateManuscriptButton } from '@/components/ui/GenerateManuscriptButton';
import { ExperimentTelemetry, ExperimentData } from '@/components/common/ExperimentTelemetry';
import { Modal } from '@/components/ui/Modal';
import { SandboxEditor, ResultsViewer } from '@/components/ui';
import type { SandboxOutput, ExperimentResult } from '@/components/ui';
import {
  Network,
  Layers,
  FlaskConical,
  FileText,
  Activity,
  ChevronRight,
  Zap,
  Loader2,
  ShieldAlert,
  Cpu,
  Beaker,
  Play,
  CheckCircle2,
  XCircle
} from 'lucide-react';

export default function StudyStudioPage() {
  const params = useParams();
  const projectId = params.id as string;
  const runId = params.runId as string;

  const [project, setProject] = useState<Project | null>(null);
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [clusters, setClusters] = useState<PaperCluster[]>([]);
  const [conflicts, setClusterConflicts] = useState<ClusterConflict[]>([]);
  const [manuscript, setManuscript] = useState<Manuscript | null>(null);
  const [experiment, setExperiment] = useState<ExperimentData | null>(null);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [selectedHypothesisId, setSelectedHypothesisId] = useState<string | null>(null);
  const [sandboxOutput, setSandboxOutput] = useState<any>(null);
  const [sandboxRunning, setSandboxRunning] = useState(false);

  const [loading, setLoading] = useState(true);
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);

  useEffect(() => {
    loadStudioData();
  }, [projectId, runId]);

  const loadStudioData = async () => {
    setLoading(true);
    try {
      const [projData, runData, graph, runClusters, runConflicts, runManuscripts, experimentData, hyps] = await Promise.all([
        projectsApi.get(projectId),
        runsApi.get(runId),
        projectsApi.graph(projectId),
        papersApi.clusters(projectId, runId),
        papersApi.conflicts(projectId, undefined, undefined, runId),
        manuscriptsApi.list(projectId, runId),
        runsApi.experiment(runId),
        hypothesesApi.list(projectId, { limit: '20' }).catch(() => []),
      ]);

      setProject(projData);
      setRun(runData);
      setGraphData(graph);
      setClusters(runClusters);
      setClusterConflicts(runConflicts);
      setManuscript(runManuscripts[0] || null);
      setExperiment(experimentData as unknown as ExperimentData);
      setHypotheses(hyps as unknown as Hypothesis[]);

    } catch (error) {
      console.error('Failed to load studio data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateManuscript = async (newContent: string) => {
    if (!manuscript) return;
    try {
      const updated = await manuscriptsApi.update(manuscript.id, { content_latex: newContent });
      setManuscript(updated);
    } catch (err) {
      console.error('Failed to update manuscript:', err);
    }
  };

  const handleFinalize = async () => {
    if (!manuscript || !window.confirm('Finalize this study? This will lock the manuscript for submission.')) return;
    try {
      const updated = await manuscriptsApi.finalize(manuscript.id);
      setManuscript(updated);
    } catch (err) {
      console.error('Failed to finalize study:', err);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Initializing Studio..." />
        <div className="p-10 flex flex-col items-center justify-center min-h-[60vh] gap-6">
           <div className="w-32 h-32 bg-primary/10 rounded-[3rem] flex items-center justify-center animate-pulse shadow-2xl shadow-primary/20">
              <Activity size={64} className="text-primary animate-spin" />
           </div>
           <p className="text-[10px] font-black uppercase tracking-[0.5em] text-muted-foreground animate-pulse">Synchronizing Synthesis Results...</p>
        </div>
      </Layout>
    );
  }

  if (!run || !project) return null;

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Study Studio"
        subtitle={`Cycle analysis for: ${run.id.slice(0, 8)}`}
        actions={
          <div className="flex items-center gap-4">
            <CognitiveEntropy
              entropy={run.cognitive_entropy || 0.5}
              mode={run.cognitive_mode as any}
              size="sm"
            />
            {manuscript?.status !== 'finalized' ? (
              <Button
                variant="primary"
                className="rounded-xl px-6 py-5 text-[9px] font-black uppercase tracking-widest shadow-xl shadow-primary/20"
                onClick={handleFinalize}
              >
                Finalize Study <ChevronRight size={14} className="ml-2" />
              </Button>
            ) : (
              <Badge variant="success" className="bg-success/10 text-success border-success/20 uppercase text-[10px] font-black tracking-widest px-4 py-2">
                STUDY_LOCKED
              </Badge>
            )}
          </div>
        }
      />

      <div className="p-8">
        <Tabs defaultValue="corpus" className="space-y-8">
          <TabsList className="p-1.5 bg-stone-100 dark:bg-stone-900 rounded-[1.5rem] border border-border/5 w-fit">
            <TabsTrigger value="corpus" className="rounded-xl px-8 py-3 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
               <Network size={14} /> Corpus Surface
            </TabsTrigger>
            <TabsTrigger value="engine" className="rounded-xl px-8 py-3 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
               <Cpu size={14} /> Discovery Engine
            </TabsTrigger>
            <TabsTrigger value="prism" className="rounded-xl px-8 py-3 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
               <FlaskConical size={14} /> Prism Synthesis
            </TabsTrigger>
            <TabsTrigger value="experiment" className="rounded-xl px-8 py-3 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
               <Beaker size={14} /> Experiment Validation
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Corpus Surface */}
          <TabsContent value="corpus" className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
               <div className="lg:col-span-3 space-y-6">
                  <div className="flex items-center gap-3 ml-2">
                     <div className="w-8 h-px bg-primary/20" />
                     <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Interactive Knowledge Topology</h3>
                  </div>
                  {graphData && (
                    <KnowledgeGraph data={graphData} onNodeClick={setSelectedPaperId} />
                  )}
               </div>

               <div className="space-y-8">
                  <div className="flex items-center gap-3 ml-2">
                     <div className="w-8 h-px bg-tertiary/20" />
                     <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Thematic Nodes</h3>
                  </div>
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                     {clusters.map(cluster => (
                       <Card key={cluster.id} className="p-6 bg-white/40 dark:bg-stone-900/40 border-border/5 hover:border-primary/20 transition-all cursor-pointer group">
                          <div className="flex items-start justify-between mb-4">
                             <div className="p-2 bg-primary/10 rounded-lg text-primary group-hover:rotate-6 transition-transform">
                                <Layers size={16} />
                             </div>
                             <Badge className="bg-stone-100 dark:bg-stone-800 text-[8px] font-black tracking-tighter uppercase">{cluster.cluster_type}</Badge>
                          </div>
                          <h4 className="font-bold text-sm text-foreground mb-2 line-clamp-1">{cluster.name}</h4>
                          <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed">{cluster.description}</p>
                       </Card>
                     ))}
                     {clusters.length === 0 && (
                        <div className="py-20 text-center glass border-2 border-dashed border-border/10 rounded-[2rem] italic text-[10px] text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                           No nodes in this cycle.
                        </div>
                     )}
                  </div>
               </div>
            </div>
          </TabsContent>

          {/* Tab 2: Discovery Engine */}
          <TabsContent value="engine" className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
             <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                   <div className="flex items-center gap-3 ml-2">
                      <div className="w-8 h-px bg-success/20" />
                      <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Empirical Sandbox Telemetry</h3>
                   </div>
                   <ExperimentTelemetry
                     experiment={experiment}
                     onExport={() => {
                       if (!experiment?.stdout) return;
                       const blob = new Blob([experiment.stdout], { type: 'text/plain' });
                       const url = URL.createObjectURL(blob);
                       const anchor = document.createElement('a');
                       anchor.href = url;
                       anchor.download = `experiment_${runId.slice(0, 8)}.txt`;
                       anchor.click();
                       URL.revokeObjectURL(url);
                     }}
                   />
                </div>

                <div className="space-y-6">
                   <div className="flex items-center gap-3 ml-2">
                      <div className="w-8 h-px bg-error/20" />
                      <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Active Scientific Tensions</h3>
                   </div>
                   <div className="space-y-4">
                      {conflicts.map(conflict => (
                        <Card key={conflict.id} className="p-8 border-error/10 bg-error/5 dark:bg-error/[0.02] rounded-3xl relative overflow-hidden group hover:border-error/30 transition-all">
                           <div className="absolute top-0 right-0 p-6 opacity-[0.03] group-hover:opacity-[0.08] transition-all">
                              <ShieldAlert size={60} className="text-error" />
                           </div>
                           <div className="relative z-10">
                              <div className="flex items-center justify-between mb-4">
                                 <span className="text-[10px] font-black uppercase text-error tracking-[0.2em]">{conflict.conflict_type} detected</span>
                                 <Badge className="bg-error text-white text-[9px] font-black">Severity: {conflict.severity?.toFixed(2)}</Badge>
                              </div>
                              <p className="text-sm text-foreground/90 font-bold tracking-tight mb-4 leading-relaxed">{conflict.description}</p>
                              {conflict.research_opportunity && (
                                <div className="mt-6 p-4 bg-white/50 dark:bg-stone-900/50 rounded-xl border border-error/10">
                                   <p className="text-[9px] font-black text-error/60 uppercase tracking-widest mb-1">Synthetic Opportunity</p>
                                    <p className="text-xs text-muted-foreground font-medium italic">&ldquo;{conflict.research_opportunity}&rdquo;</p>
                                </div>
                              )}
                           </div>
                        </Card>
                      ))}
                      {conflicts.length === 0 && (
                         <div className="py-20 text-center glass border-2 border-dashed border-border/10 rounded-[2.5rem] italic text-[10px] text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                            No critical contradictions detected in this cycle.
                         </div>
                      )}
                   </div>
                </div>
             </div>
          </TabsContent>

          {/* Tab 3: Prism Synthesis */}
          <TabsContent value="prism" className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
             <div className="space-y-6">
                <div className="flex items-center gap-3 ml-2">
                   <div className="w-8 h-px bg-primary/20" />
                   <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Iterative Manuscript Synthesis</h3>
                </div>
                {manuscript ? (
                  <LaTeXPrism content={manuscript.content_latex || ''} onUpdate={updateManuscript} />
                ) : (
                  <div className="space-y-6">
                    <Card className="p-20 text-center glass border-border/5 rounded-[3rem]">
                      <div className="w-24 h-24 bg-stone-100 dark:bg-stone-900 rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-inner">
                        <FileText size={48} className="text-muted-foreground/20" />
                      </div>
                      <h3 className="text-2xl font-black text-foreground mb-4 tracking-tighter uppercase">No Manuscript Generated</h3>
                      <p className="text-muted-foreground font-medium max-w-md mx-auto leading-relaxed mb-10">
                        Generate a scientific manuscript from your research cycle results. This will synthesize papers, hypotheses, and findings into an IMRaD-structured document.
                      </p>
                      <GenerateManuscriptButton runId={runId} projectId={projectId} onGenerated={(m) => setManuscript(m)} />
                    </Card>
                  </div>
                )}
             </div>
          </TabsContent>

          {/* Tab 4: Experiment Validation */}
          <TabsContent value="experiment" className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              {/* Hypothesis selector — left sidebar */}
              <div className="lg:col-span-1 space-y-6">
                <div className="flex items-center gap-3 ml-2">
                  <div className="w-8 h-px bg-tertiary/20" />
                  <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Hypotheses</h3>
                </div>
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                  {hypotheses.length === 0 && (
                    <div className="py-10 text-center glass border-2 border-dashed border-border/10 rounded-[1.5rem] text-[10px] text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                      No hypotheses generated for this project yet.
                    </div>
                  )}
                  {hypotheses.map((hyp) => (
                    <Card
                      key={hyp.id}
                      className={`p-4 cursor-pointer transition-all border ${
                        selectedHypothesisId === hyp.id
                          ? 'border-primary/40 bg-primary/[0.03] shadow-lg shadow-primary/5'
                          : 'border-border/5 hover:border-primary/20 bg-white/40 dark:bg-stone-900/40'
                      }`}
                      onClick={() => setSelectedHypothesisId(hyp.id)}
                    >
                      <div className="flex items-start gap-2">
                        <div className={`p-1.5 rounded-lg shrink-0 ${
                          hyp.status === 'validated' ? 'bg-success/10 text-success' :
                          hyp.status === 'rejected' ? 'bg-error/10 text-error' :
                          'bg-tertiary/10 text-tertiary'
                        }`}>
                          {hyp.status === 'validated' ? <CheckCircle2 size={14} /> :
                           hyp.status === 'rejected' ? <XCircle size={14} /> :
                           <Beaker size={14} />}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold leading-snug line-clamp-2">{hyp.statement}</p>
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="text-[9px] uppercase tracking-wider text-muted-foreground/50 font-bold">{hyp.status}</span>
                            {hyp.confidence && (
                              <span className="text-[9px] font-mono text-muted-foreground/40">
                                {(hyp.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Experiment tools — main area */}
              <div className="lg:col-span-4 space-y-8">
                {selectedHypothesisId ? (
                  <>
                    {/* Sandbox Editor */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-3 ml-2">
                        <div className="w-8 h-px bg-primary/20" />
                        <h3 className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.4em]">Python Experiment Sandbox</h3>
                      </div>
                      <SandboxEditor
                        hypothesisId={selectedHypothesisId}
                        projectId={projectId}
                        onRun={async (code) => {
                          setSandboxRunning(true);
                          try {
                            const response = await fetch('/api/v1/sandbox/plotly', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ project_id: projectId, code, title: 'Experiment Run' }),
                            });
                            if (response.ok) {
                              const data = await response.json();
                              const out: SandboxOutput = {
                                success: true,
                                stdout: JSON.stringify(data, null, 2),
                                stderr: '',
                                duration_ms: data.duration_ms || 0,
                              };
                              setSandboxOutput(out);
                              return out;
                            } else {
                              const errData = await response.json().catch(() => ({}));
                              const out: SandboxOutput = {
                                success: false,
                                stdout: '',
                                stderr: errData.detail || `HTTP ${response.status}`,
                                duration_ms: 0,
                                error_message: errData.detail || 'API error',
                              };
                              setSandboxOutput(out);
                              return out;
                            }
                          } catch (err: any) {
                            const out: SandboxOutput = {
                              success: false,
                              stdout: '',
                              stderr: String(err),
                              duration_ms: 0,
                              error_message: String(err),
                            };
                            setSandboxOutput(out);
                            return out;
                          } finally {
                            setSandboxRunning(false);
                          }
                        }}
                      />
                    </div>

                    {/* Results Viewer */}
                    {sandboxOutput && (
                      <ResultsViewer
                        result={{
                          success: sandboxOutput.success,
                          stdout: sandboxOutput.stdout,
                          stderr: sandboxOutput.stderr,
                          exit_code: sandboxOutput.success ? 0 : 1,
                          duration_ms: sandboxOutput.duration_ms || 0,
                          error_message: sandboxOutput.error_message,
                        }}
                        hypothesisLabel={hypotheses.find(h => h.id === selectedHypothesisId)?.statement}
                      />
                    )}
                  </>
                ) : (
                  <div className="py-20 text-center glass border-2 border-dashed border-border/10 rounded-[2.5rem]">
                    <Beaker size={48} className="mx-auto mb-6 text-muted-foreground/20" />
                    <h3 className="text-xl font-black text-foreground mb-3 tracking-tight uppercase">Select a Hypothesis</h3>
                    <p className="text-muted-foreground font-medium max-w-md mx-auto leading-relaxed text-sm">
                      Choose a hypothesis from the left panel to write and run validation experiments.
                    </p>
                  </div>
                )}

                {/* Cross-mode workflow links */}
                <div className="flex items-center justify-center gap-4 pt-4 border-t border-border/5">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(`/projects/${projectId}/datasets`, '_self')}
                  >
                    <FlaskConical className="h-3.5 w-3.5 mr-2" />
                    Browse Datasets
                  </Button>
                  {manuscript ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        // Open manuscript in article studio for full editing
                        window.open(`/projects/${projectId}/manuscripts`, '_self');
                      }}
                    >
                      <FileText className="h-3.5 w-3.5 mr-2" />
                      Open in Article Studio
                    </Button>
                  ) : (
                    <GenerateManuscriptButton
                      runId={runId}
                      projectId={projectId}
                      onGenerated={(m) => { setManuscript(m); }}
                    />
                  )}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Node Detail Modal */}
      <Modal
        isOpen={!!selectedPaperId}
        onClose={() => setSelectedPaperId(null)}
        title="Knowledge Node Analysis"
        size="lg"
      >
        {selectedPaperId && <KnowledgeCard paperId={selectedPaperId} />}
      </Modal>
    </Layout>
  );
}