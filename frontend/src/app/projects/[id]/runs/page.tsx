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
import { ResearchRun, Idea } from '@/lib/types';
import { formatDate, formatDuration } from '@/lib/utils';
import {
  Activity, Clock, DollarSign, Play, Loader2, CheckCircle2, XCircle,
  AlertTriangle, ChevronDown, ChevronRight, RotateCw, X, Search,
  Brain, FileSearch, Network, MessageSquare, FlaskConical, Star,
  Wrench, CheckSquare,
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
  completed: CheckCircle2,
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

  const handleStartRun = async () => {
    if (!newRun.idea.trim()) return;
    setStarting(true);
    setStartResult(null);
    try {
      const apiSettings = JSON.parse(localStorage.getItem('autoscience_api_settings') || '{}');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch(
          `/api/v1/research/run?project_id=${projectId}&idea=${encodeURIComponent(newRun.idea)}&run_type=${newRun.run_type}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-OpenRouter-API-Key': apiSettings.openrouter_api_key || '',
              'X-OpenRouter-Model': apiSettings.openrouter_model || 'openai/gpt-4o',
              'X-Default-Provider': apiSettings.default_provider || 'openrouter',
            },
            signal: controller.signal,
          }
        );
        clearTimeout(timeoutId);
        if (response.ok) {
          const result = await response.json();
          setStarting(false);
          setStartResult({ success: true, message: `Done! ${result.papers_found} papers, ${result.questions_generated} questions, ${result.hypotheses_formed} hypotheses.` });
          loadRuns();
          return;
        }
      } catch (e: any) {
        if (e.name !== 'AbortError') throw e;
      }
      // Request still running, poll for it
      await new Promise(r => setTimeout(r, 2000));
      const updatedRuns = await loadRuns();
      const latestRun = updatedRuns[0];
      if (latestRun?.state === 'running') {
        setExpandedRunId(latestRun.id);
        pollLiveStatus(latestRun.id);
      }
      setStarting(false);
      setStartResult({ success: true, message: 'Research started! Watch the live progress below.' });
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
                  <CheckCircle2 size={16} className="text-green-600 mb-1" />
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
              Live Events ({status.event_count})
            </h5>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {[...status.recent_events].reverse().map((event: any, idx: number) => (
                <div key={event.id || idx} className="flex items-center gap-2 text-xs p-2 bg-white rounded border">
                  {event.event_type.includes('completed') ? (
                    <CheckCircle2 size={12} className="text-green-500 shrink-0" />
                  ) : event.event_type.includes('failed') ? (
                    <XCircle size={12} className="text-red-500 shrink-0" />
                  ) : (
                    <ChevronRight size={12} className="text-blue-500 shrink-0" />
                  )}
                  <span className="text-gray-600">{event.details?.phase_label || event.event_type}</span>
                  {event.details?.duration && (
                    <span className="text-gray-400 ml-auto">{event.details.duration}s</span>
                  )}
                </div>
              ))}
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
              {[...status.recent_tool_calls].reverse().map((tc: any, idx: number) => (
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
                    className={`flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors ${isExpanded ? 'bg-blue-50/50' : 'bg-white'}`}
                    onClick={() => toggleExpand(run.id)}
                  >
                    <div className="text-gray-400">
                      {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                    </div>
                    <Badge variant="info">{run.run_type}</Badge>
                    <StatusBadge status={run.state} />
                    <div className="flex-1" />
                    {isRunning && status && (
                      <span className="text-sm text-blue-600 font-medium">
                        {PHASE_LABELS[status.current_phase?.replace(' (done)', '')] || status.current_phase}
                      </span>
                    )}
                    {isRunning && !status && (
                      <span className="flex items-center gap-1 text-blue-600">
                        <Loader2 size={14} className="animate-spin" />
                        <span className="text-sm">Starting...</span>
                      </span>
                    )}
                    <span className="text-sm text-gray-500">
                      {run.started_at ? formatDate(run.started_at) : '—'}
                    </span>
                    {run.started_at && run.completed_at && (
                      <span className="text-sm text-gray-500 flex items-center gap-1">
                        <Clock size={14} />
                        {formatDuration(run.started_at, run.completed_at)}
                      </span>
                    )}
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <DollarSign size={14} />${run.max_cost_usd.toFixed(2)}
                    </span>
                    {isRunning && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleCancelRun(run.id); }}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-red-600"
                        title="Cancel"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="p-4 bg-gray-50 border-t">
                      {isRunning ? (
                        renderProgressTrack(run.id)
                      ) : (
                        <div className="text-sm text-gray-600">
                          {status?.recent_events && status.recent_events.length > 0 ? (
                            <div>
                              <p className="mb-2 font-medium">Run Events:</p>
                              <div className="space-y-1 max-h-48 overflow-y-auto">
                                {status.recent_events.map((event: any, idx: number) => (
                                  <div key={idx} className="flex items-center gap-2 text-xs p-2 bg-white rounded border">
                                    <CheckCircle2 size={12} className="text-green-500 shrink-0" />
                                    <span>{event.details?.phase_label || event.event_type}</span>
                                    {event.details?.duration && (
                                      <span className="text-gray-400 ml-auto">{event.details.duration}s</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="italic text-gray-500">No events recorded.</p>
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
                {startResult.success ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
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
                { value: 'idle_exploration', label: 'Idle Exploration' },
                { value: 'literature_review', label: 'Literature Review' },
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
