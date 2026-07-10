'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Input, Textarea, Select } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';
import { runsApi, ideasApi } from '@/lib/api';
import { getAuthHeaders } from '@/lib/api';
import { getLlmHeaders } from '@/lib/apiSettings';
import { ResearchRun, Idea } from '@/lib/types';
import { AppEvent, ToolCall } from '@/lib/types';
import { formatDate, formatDuration, cn } from '@/lib/utils';
import { LivePreview } from '@/components/LivePreview';
import {
  Activity, Clock, DollarSign, Play, Loader2, CheckCircle, XCircle,
  AlertTriangle, ChevronDown, ChevronRight, RotateCw, X, Search,
  Brain, FileSearch, Network, MessageSquare, FlaskConical, Star,
  Wrench, CheckSquare, Trash2, ChevronUp,
} from 'lucide-react';

const PHASE_ICONS: Record<string, any> = {
  interpret_intent: Brain,
  plan_search: Search,
  retrieve_literature: FileSearch,
  analyze_papers: FileSearch,
  cluster_papers: Network,
  detect_conflicts: AlertTriangle,
  generate_questions: MessageSquare,
  form_hypotheses: FlaskConical,
  plan_validation: CheckSquare,
  score_idea: Star,
  make_decision: Brain,
  create_skills: Wrench,
  generate_report: FileSearch,
  completed: CheckCircle,
};

const PHASE_LABELS: Record<string, string> = {
  interpret_intent: 'Interpreting Intent',
  plan_search: 'Planning Search',
  retrieve_literature: 'Searching Literature',
  analyze_papers: 'Analyzing Papers',
  cluster_papers: 'Clustering Papers',
  detect_conflicts: 'Detecting Conflicts',
  generate_questions: 'Generating Questions',
  form_hypotheses: 'Forming Hypotheses',
  plan_validation: 'Planning Validation',
  score_idea: 'Scoring Idea',
  make_decision: 'Making Decisions',
  create_skills: 'Creating Skills',
  generate_report: 'Generating Report',
  completed: 'Completed',
};

const ALL_PHASES = Object.keys(PHASE_LABELS).filter(p => p !== 'completed');

export default function RunsPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = params.id as string;
  const prefillIdea = searchParams.get('idea') || '';

  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startResult, setStartResult] = useState<{ success: boolean; message: string } | null>(null);
  const [newRun, setNewRun] = useState({ idea: '', run_type: 'user_directed' });
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [expandedEventIds, setExpandedEventIds] = useState<Set<string>>(new Set());
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);

  // Live progress state
  const [liveStatus, setLiveStatus] = useState<Record<string, any>>({});
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadRuns();
    if (prefillIdea) {
      setNewRun(prev => ({ ...prev, idea: prefillIdea }));
      setShowCreateModal(true);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [projectId, prefillIdea]);

  const loadRuns = async () => {
    try {
      const data = await runsApi.list(projectId);
      setRuns(data);
      // Auto-expand any running run
      const running = data.find((r: ResearchRun) => r.state === 'running');
      if (running && !expandedRunId) setExpandedRunId(running.id);
      return data;
    } catch (error) {
      console.error('Failed to load runs:', error);
      return [];
    } finally {
      setLoading(false);
    }
  };

  const pollLiveStatus = useCallback((runId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    const poll = setInterval(async () => {
      try {
        const status = await runsApi.status(runId);
        setLiveStatus(prev => ({ ...prev, [runId]: status }));

        if (status.state !== 'running') {
          clearInterval(poll);
          pollRef.current = null;
          loadRuns();
        }
      } catch (e) {
        console.error('Poll error:', e);
      }
    }, 5000);

    pollRef.current = poll;

    // Initial fetch
    runsApi.status(runId).then(status => {
      setLiveStatus(prev => ({ ...prev, [runId]: status }));
    }).catch(() => {});
  }, []);

  const toggleExpand = (runId: string) => {
    if (expandedRunId === runId) {
      setExpandedRunId(null);
    } else {
      setExpandedRunId(runId);
      const run = runs.find(r => r.id === runId);
      if (run?.state === 'running') {
        pollLiveStatus(runId);
      } else {
        // Fetch status once
        runsApi.status(runId).then(status => {
          setLiveStatus(prev => ({ ...prev, [runId]: status }));
        }).catch(() => {});
      }
    }
  };

  // Auto-poll running runs
  useEffect(() => {
    const runningRuns = runs.filter(r => r.state === 'running');
    if (runningRuns.length > 0) {
      const firstRunning = runningRuns[0];
      if (!expandedRunId) setExpandedRunId(firstRunning.id);
      pollLiveStatus(firstRunning.id);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [runs, pollLiveStatus]);

  const handleCancelRun = async (runId: string) => {
    try {
      await runsApi.cancel(runId);
      loadRuns();
    } catch (error) {
      console.error('Failed to cancel run:', error);
    }
  };

  const handleDeleteRun = async (runId: string) => {
    if (!window.confirm('Are you sure you want to delete this run? This action cannot be undone.')) return;
    try {
      setDeletingRunId(runId);
      await runsApi.delete(runId);
      await loadRuns();
    } catch (error) {
      console.error('Failed to delete run:', error);
    } finally {
      setDeletingRunId(null);
    }
  };

  const toggleEventExpand = (eventId: string) => {
    setExpandedEventIds(prev => {
      const next = new Set(prev);
      if (next.has(eventId)) next.delete(eventId);
      else next.add(eventId);
      return next;
    });
  };

  const handleStartRun = async () => {
    if (!newRun.idea.trim()) return;
    setStarting(true);
    setStartResult(null);
    try {
      const response = await fetch(
        `/api/v1/research/run`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
            ...getLlmHeaders(),
          },
          body: JSON.stringify({
            project_id: projectId,
            idea: newRun.idea,
            run_type: newRun.run_type,
          }),
        }
      );
      if (response.ok) {
        const result = await response.json();
        setStarting(false);
        setStartResult({ success: true, message: `Research started! Run ID: ${result.run_id}` });
        setShowCreateModal(false);
        setStartResult(null);
        // Reload runs and expand the new one
        const updatedRuns = await loadRuns();
        if (result.run_id) {
          setExpandedRunId(result.run_id);
        }
        return;
      }
      const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    } catch (error: any) {
      setStarting(false);
      setStartResult({ success: false, message: error.message || 'Failed to start.' });
    }
  };

  const handleCloseModal = () => {
    if (!starting) {
      setShowCreateModal(false);
      setStartResult(null);
      setNewRun({ idea: '', run_type: 'user_directed' });
      router.replace(`/projects/${projectId}/runs`);
    }
  };

  const getPhaseIndex = (phase: string): number => {
    return ALL_PHASES.indexOf(phase.replace(' (done)', ''));
  };

  const renderProgressTrack = (runId: string) => {
    const status = liveStatus[runId];
    if (!status) return null;

    const currentPhase = status.current_phase?.replace(' (done)', '') || '';
    const currentIdx = getPhaseIndex(currentPhase);

    return (
      <div className="space-y-4">
        {/* Progress bar */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {PHASE_LABELS[currentPhase] || currentPhase}
            </span>
            <span className="text-xs text-gray-500">
              {Math.round(((currentIdx + 1) / ALL_PHASES.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${((currentIdx + 1) / ALL_PHASES.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Phase steps */}
        <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
          {ALL_PHASES.map((phase, idx) => {
            const Icon = PHASE_ICONS[phase] || Brain;
            const isDone = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            const isPending = idx > currentIdx;

            return (
              <div
                key={phase}
                className={`flex flex-col items-center p-2 rounded-lg text-center ${
                  isDone ? 'bg-green-50 text-green-700' :
                  isCurrent ? 'bg-blue-50 text-blue-700 ring-2 ring-blue-300' :
                  'bg-gray-50 text-gray-400'
                }`}
              >
                {isDone ? (
                  <CheckCircle size={16} className="text-green-600 mb-1" />
                ) : isCurrent ? (
                  <Loader2 size={16} className="animate-spin text-blue-600 mb-1" />
                ) : (
                  <Icon size={16} className="mb-1" />
                )}
                <span className="text-xs leading-tight">{PHASE_LABELS[phase]}</span>
              </div>
            );
          })}
        </div>

        {/* Live Events */}
        {status.recent_events && status.recent_events.length > 0 && (
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Recent Events ({status.event_count})
            </h5>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {[...status.recent_events].reverse().map((event: AppEvent, idx: number) => {
                const eventId = event.id || `event-${idx}`;
                const isExpanded = expandedEventIds.has(eventId);
                return (
                  <div key={eventId} className="bg-white rounded border">
                    <div
                      className="flex items-center gap-2 text-xs p-2 cursor-pointer hover:bg-gray-50"
                      onClick={() => toggleEventExpand(eventId)}
                    >
                      {event.event_type?.includes('completed') ? (
                        <CheckCircle size={12} className="text-green-500 shrink-0" />
                      ) : event.event_type?.includes('failed') ? (
                        <XCircle size={12} className="text-red-500 shrink-0" />
                      ) : (
                        <ChevronRight size={12} className="text-blue-500 shrink-0" />
                      )}
                      <span className="text-gray-500 font-mono shrink-0">{event.event_type}</span>
                      <span className="text-gray-700">{(event.details as any)?.phase_label ?? ''}</span>
                      <span className="text-gray-400 ml-auto">{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}</span>
                      {isExpanded ? <ChevronUp size={12} className="text-gray-400" /> : <ChevronDown size={12} className="text-gray-400" />}
                    </div>
                    {isExpanded && (
                      <pre className="px-3 pb-2 text-xs text-gray-600 bg-gray-50 rounded-b border-t overflow-x-auto max-h-40 overflow-y-auto">
                        {JSON.stringify(event.details || {}, null, 2)}
                      </pre>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tool Calls */}
        {status.recent_tool_calls && status.recent_tool_calls.length > 0 && (
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              Agent Activity ({status.tool_call_count})
            </h5>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {[...status.recent_tool_calls].reverse().map((tc: ToolCall, idx: number) => (
                <div key={tc.id || idx} className="flex items-center gap-2 text-xs p-2 bg-white rounded border">
                  <Wrench size={12} className={tc.success ? 'text-green-500' : 'text-red-500'} />
                  <Badge variant="default" size="sm">{tc.agent_role}</Badge>
                  <span className="text-gray-600">{tc.tool_name}</span>
                  {tc.duration_ms && (
                    <span className="text-gray-400 ml-auto">{(tc.duration_ms / 1000).toFixed(1)}s</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Runs"
        subtitle={`${runs.length} runs · ${runs.filter(r => r.state === 'running').length} active`}
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={loadRuns}>
              <RotateCw size={16} className="mr-2" /> Refresh
            </Button>
            <Button onClick={() => setShowCreateModal(true)} disabled={starting}>
              <Play size={18} className="mr-2" /> Start Research
            </Button>
          </div>
        }
      />

      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-blue-600" />
          </div>
        ) : runs.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-8 h-8 text-gray-400" />}
            title="No research runs yet"
            description="Start a research run from here or from an Idea card."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Play size={18} className="mr-2" /> Start First Run
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {runs.map((run) => {
              const isExpanded = expandedRunId === run.id;
              const isRunning = run.state === 'running';
              const status = liveStatus[run.id];

              return (
                <div key={run.id} className="border rounded-lg overflow-hidden">
                  {/* Run Row */}
                  <div
                    className={cn(
                      'flex items-center gap-6 p-5 cursor-pointer transition-all duration-500 rounded-xl border border-border/10 mb-2',
                      isExpanded ? 'glass shadow-lg scale-[1.01] border-primary/20' : 'bg-white/60 hover:bg-white/80'
                    )}
                    onClick={() => toggleExpand(run.id)}
                  >
                    <div className={cn('transition-transform duration-500', isExpanded && 'rotate-90')}>
                      {isExpanded ? <ChevronDown size={20} className="text-primary" /> : <ChevronRight size={20} className="text-muted-foreground/40" />}
                    </div>
                    <div className="flex flex-col gap-1">
                       <Badge variant="info" className="w-fit bg-primary/5 uppercase text-[9px] font-bold tracking-widest">{run.run_type || 'user_directed'}</Badge>
                       <div className="flex items-center gap-3">
                          <StatusBadge status={run.state} />
                          {isRunning && status && (
                            <span className="text-xs text-primary font-bold uppercase tracking-wider animate-pulse">
                              {PHASE_LABELS[status.current_phase?.replace(' (done)', '')] || status.current_phase}
                            </span>
                          )}
                       </div>
                    </div>
                    
                    <div className="flex-1" />
                    
                    <div className="flex items-center gap-8">
                       <div className="text-right">
                          <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest mb-0.5">Chronology</p>
                          <p className="text-xs font-semibold text-foreground/70">{run.started_at ? formatDate(run.started_at) : '—'}</p>
                       </div>
                       {run.started_at && run.completed_at && (
                         <div className="text-right hidden md:block">
                            <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest mb-0.5">Duration</p>
                            <p className="text-xs font-semibold text-foreground/70 flex items-center justify-end gap-1">
                               <Clock size={12} className="text-primary" />
                               {formatDuration(run.started_at, run.completed_at)}
                            </p>
                         </div>
                       )}
                       <div className="text-right">
                          <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest mb-0.5">Resources</p>
                          <p className="text-xs font-bold text-foreground/70 flex items-center justify-end gap-0.5">
                             <DollarSign size={12} className="text-success" />{run.max_cost_usd.toFixed(2)}
                          </p>
                       </div>
                    </div>

                    <div className="flex items-center gap-1 pl-4 border-l border-border/10">
                      {isRunning ? (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleCancelRun(run.id); }}
                          className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300"
                          title="Terminate Run"
                        >
                          <X size={18} />
                        </button>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteRun(run.id); }}
                          className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300 disabled:opacity-30"
                          title="Purge Record"
                          disabled={deletingRunId === run.id}
                        >
                          {deletingRunId === run.id ? (
                            <Loader2 size={18} className="animate-spin" />
                          ) : (
                            <Trash2 size={18} />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="p-8 bg-muted/20 border-t border-border/10 animate-in slide-in-from-top-4 duration-500">
                      {isRunning ? (
                        <div className="space-y-8">
                          {/* Live Search Preview */}
                          <LivePreview runId={run.id} isActive={isRunning} onComplete={loadRuns} />
                          <div className="glass p-8 rounded-2xl shadow-inner">
                             <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 bg-primary/10 rounded-lg">
                                   <Activity size={20} className="text-primary animate-pulse" />
                                </div>
                                <h4 className="text-sm font-bold text-foreground uppercase tracking-[0.2em]">Cognitive Phase Analysis</h4>
                             </div>
                             {renderProgressTrack(run.id)}
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-6">
                          <div className="flex items-center gap-3">
                             <div className="p-2 bg-muted rounded-lg border border-border/10">
                                <Clock size={18} className="text-muted-foreground/60" />
                             </div>
                             <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em]">Archived Execution Log</h4>
                          </div>
                          {status?.recent_events && status.recent_events.length > 0 ? (
                            <div className="grid gap-2">
                                {status.recent_events.map((event: any, idx: number) => {
                                  const eventId = event.id || `event-${idx}`;
                                  const isExpanded = expandedEventIds.has(eventId);
                                  return (
                                    <div key={eventId} className="bg-white/40 backdrop-blur-sm rounded-xl border border-border/10 shadow-sm transition-all duration-300 overflow-hidden">
                                      <div
                                        className="flex items-center gap-4 text-[11px] p-4 cursor-pointer hover:bg-white/60 transition-colors"
                                        onClick={() => toggleEventExpand(eventId)}
                                      >
                                        {event.event_type?.includes('completed') ? (
                                          <CheckCircle size={14} className="text-success shrink-0" />
                                        ) : event.event_type?.includes('failed') ? (
                                          <XCircle size={14} className="text-error shrink-0" />
                                        ) : (
                                          <ChevronRight size={14} className="text-primary shrink-0" />
                                        )}
                                        <span className="text-muted-foreground font-mono font-bold shrink-0 opacity-60">{event.event_type}</span>
                                        <span className="text-foreground font-bold tracking-tight">{(event.details as any)?.phase_label ?? ''}</span>
                                        <span className="text-muted-foreground/40 ml-auto font-mono">{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}</span>
                                        {isExpanded ? <ChevronUp size={14} className="text-muted-foreground/40" /> : <ChevronDown size={14} className="text-muted-foreground/40" />}
                                      </div>
                                      {isExpanded && (
                                        <pre className="p-5 text-xs text-foreground/60 bg-muted/30 border-t border-border/10 overflow-x-auto max-h-60 custom-scrollbar font-mono leading-relaxed">
                                          {JSON.stringify(event.details || {}, null, 2)}
                                        </pre>
                                      )}
                                    </div>
                                  );
                                })}
                            </div>
                          ) : (
                            <div className="py-12 text-center glass rounded-xl border-dashed">
                               <p className="text-sm font-bold text-muted-foreground/40 uppercase tracking-widest">No persistent event telemetry found</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Start Research Run Modal */}
      <Modal isOpen={showCreateModal} onClose={handleCloseModal} title="Start Research Run" size="lg">
        {startResult ? (
          <div className="space-y-4">
            <div className={`rounded-lg p-4 text-sm ${startResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
              <div className="flex items-center gap-2 mb-2">
                {startResult.success ? <CheckCircle size={20} /> : <XCircle size={20} />}
                <strong>{startResult.success ? 'Done!' : 'Failed'}</strong>
              </div>
              <p>{startResult.message}</p>
            </div>
          </div>
        ) : starting ? (
          <div className="flex flex-col items-center py-8">
            <Loader2 size={48} className="animate-spin text-blue-600 mb-4" />
            <h3 className="text-lg font-medium">Research Starting...</h3>
            <p className="text-sm text-gray-600 mt-1">Watch the runs list for live progress.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
              Searches literature, analyzes papers, detects conflicts, generates questions & hypotheses. Live progress shown in the runs list.
            </div>
            <Textarea
              label="Research Idea"
              placeholder="Describe what you want to research..."
              rows={4}
              value={newRun.idea}
              onChange={(e) => setNewRun({ ...newRun, idea: e.target.value })}
            />
            <Select
              label="Run Type"
              value={newRun.run_type}
              onChange={(e) => setNewRun({ ...newRun, run_type: e.target.value })}
              options={[
                { value: 'user_directed', label: 'User Directed' },
                { value: 'idle_autonomous', label: 'Idle Autonomous' },
                { value: 'validation', label: 'Validation' },
              ]}
            />
          </div>
        )}
        <ModalFooter>
          {starting ? (
            <Button variant="secondary" onClick={handleCloseModal}>Close</Button>
          ) : startResult ? (
            <Button onClick={handleCloseModal}>Done</Button>
          ) : (
            <>
              <Button variant="secondary" onClick={handleCloseModal}>Cancel</Button>
              <Button onClick={handleStartRun} disabled={!newRun.idea.trim()}>
                <Play size={16} className="mr-2" /> Start Research
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
