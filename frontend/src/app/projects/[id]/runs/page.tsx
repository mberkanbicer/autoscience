'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Input, Textarea, Select } from '@/components/ui/Input';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { runsApi, ideasApi } from '@/lib/api';
import { ResearchRun, Idea } from '@/lib/types';
import { formatDate, formatDuration } from '@/lib/utils';
import {
  Activity, Clock, DollarSign, Play, Loader2, CheckCircle2, XCircle,
  AlertTriangle, ChevronDown, ChevronRight, RotateCw, X,
} from 'lucide-react';

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
  const [polling, setPolling] = useState(false);
  const [pollingRunId, setPollingRunId] = useState<string | null>(null);
  const [startResult, setStartResult] = useState<{ success: boolean; message: string } | null>(null);
  const [newRun, setNewRun] = useState({ idea: '', run_type: 'user_directed' });
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [runEvents, setRunEvents] = useState<Record<string, any[]>>({});

  useEffect(() => {
    loadRuns();
    if (prefillIdea) {
      setNewRun(prev => ({ ...prev, idea: prefillIdea }));
      setShowCreateModal(true);
    }
  }, [projectId, prefillIdea]);

  const loadRuns = async () => {
    try {
      const data = await runsApi.list(projectId);
      setRuns(data);
      return data;
    } catch (error) {
      console.error('Failed to load runs:', error);
      return [];
    } finally {
      setLoading(false);
    }
  };

  const loadRunEvents = async (runId: string) => {
    try {
      const events = await runsApi.events(runId);
      setRunEvents(prev => ({ ...prev, [runId]: events }));
    } catch (error) {
      console.error('Failed to load run events:', error);
    }
  };

  const toggleExpand = (runId: string) => {
    if (expandedRunId === runId) {
      setExpandedRunId(null);
    } else {
      setExpandedRunId(runId);
      loadRunEvents(runId);
    }
  };

  const handleCancelRun = async (runId: string) => {
    try {
      await runsApi.cancel(runId);
      loadRuns();
    } catch (error) {
      console.error('Failed to cancel run:', error);
    }
  };

  const startPolling = (runId: string) => {
    setPolling(true);
    setPollingRunId(runId);
    let attempts = 0;
    const poll = setInterval(async () => {
      attempts++;
      const updatedRuns = await loadRuns();
      const run = updatedRuns.find((r: ResearchRun) => r.id === runId);
      if (run && (run.state === 'completed' || run.state === 'failed' || run.state === 'cancelled')) {
        clearInterval(poll);
        setPolling(false);
        setPollingRunId(null);
        setStarting(false);
        setStartResult({
          success: run.state === 'completed',
          message: run.state === 'completed'
            ? 'Research completed! Check the results below.'
            : `Research ${run.state}.`,
        });
      }
      if (attempts >= 150) {
        clearInterval(poll);
        setPolling(false);
        setPollingRunId(null);
        setStarting(false);
        setStartResult({ success: false, message: 'Research still running. Check back later.' });
      }
    }, 2000);
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

      await new Promise(r => setTimeout(r, 2000));
      const updatedRuns = await loadRuns();
      const latestRun = updatedRuns[0];
      if (latestRun?.state === 'running') startPolling(latestRun.id);
      else { setStarting(false); setStartResult({ success: true, message: 'Research submitted.' }); }
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

  const getEventIcon = (type: string) => {
    if (type.includes('start') || type.includes('created')) return <Play size={14} className="text-green-500" />;
    if (type.includes('complete') || type.includes('success')) return <CheckCircle2 size={14} className="text-green-600" />;
    if (type.includes('fail') || type.includes('error')) return <XCircle size={14} className="text-red-500" />;
    if (type.includes('cancel')) return <X size={14} className="text-gray-500" />;
    return <ChevronRight size={14} className="text-blue-500" />;
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Runs"
        subtitle={`${runs.length} runs`}
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={loadRuns} disabled={starting}>
              <RotateCw size={16} className="mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setShowCreateModal(true)} disabled={starting}>
              <Play size={18} className="mr-2" />
              Start Research
            </Button>
          </div>
        }
      />

      <div className="p-6">
        {loading ? (
          <SkeletonTable />
        ) : runs.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-8 h-8 text-gray-400" />}
            title="No research runs yet"
            description="Start a research run to begin autonomous literature analysis."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Play size={18} className="mr-2" />
                Start First Run
              </Button>
            }
          />
        ) : (
          <div className="space-y-2">
            {runs.map((run) => (
              <div key={run.id}>
                {/* Run Row */}
                <div
                  className={`flex items-center gap-4 p-4 bg-white border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${expandedRunId === run.id ? 'border-blue-300 bg-blue-50' : ''}`}
                  onClick={() => toggleExpand(run.id)}
                >
                  <div className="text-gray-400">
                    {expandedRunId === run.id ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                  </div>
                  <Badge variant="info">{run.run_type}</Badge>
                  <StatusBadge status={run.state} />
                  <div className="flex-1" />
                  <span className="text-sm text-gray-500">
                    {run.started_at ? formatDate(run.started_at) : '—'}
                  </span>
                  {run.started_at && run.completed_at && (
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <Clock size={14} />
                      {formatDuration(run.started_at, run.completed_at)}
                    </span>
                  )}
                  {run.state === 'running' && (
                    <span className="flex items-center gap-1 text-blue-600">
                      <Loader2 size={14} className="animate-spin" />
                      <span className="text-sm">Running</span>
                    </span>
                  )}
                  <span className="text-sm text-gray-500 flex items-center gap-1">
                    <DollarSign size={14} />
                    ${run.max_cost_usd.toFixed(2)}
                  </span>
                  {run.state === 'running' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleCancelRun(run.id); }}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-red-600 transition-colors"
                      title="Cancel run"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>

                {/* Expanded Details */}
                {expandedRunId === run.id && (
                  <div className="ml-8 mt-2 mb-4 p-4 bg-gray-50 border rounded-lg">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">Run Events</h4>
                    {runEvents[run.id] ? (
                      runEvents[run.id].length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No events recorded yet.</p>
                      ) : (
                        <div className="space-y-2">
                          {runEvents[run.id].map((event: any, idx: number) => (
                            <div key={event.id || idx} className="flex items-start gap-3 p-2 bg-white rounded border">
                              {getEventIcon(event.event_type)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium text-gray-800">{event.event_type}</span>
                                  {event.actor && (
                                    <Badge variant="default" size="sm">{event.actor}</Badge>
                                  )}
                                </div>
                                {event.details && (
                                  <p className="text-xs text-gray-500 mt-1 truncate">
                                    {typeof event.details === 'string' ? event.details : JSON.stringify(event.details).slice(0, 200)}
                                  </p>
                                )}
                              </div>
                              <span className="text-xs text-gray-400 whitespace-nowrap">
                                {event.created_at ? formatDate(event.created_at) : ''}
                              </span>
                            </div>
                          ))}
                        </div>
                      )
                    ) : (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Loader2 size={14} className="animate-spin" />
                        Loading events...
                      </div>
                    )}

                    <div className="mt-3 pt-3 border-t text-xs text-gray-400 flex items-center gap-4">
                      <span>ID: {run.id.slice(0, 8)}...</span>
                      <span>Max duration: {run.max_minutes}min</span>
                      <span>Max sources: {run.max_sources}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
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
            <h3 className="text-lg font-medium">Research in Progress</h3>
            <p className="text-sm text-gray-600 mt-1">This may take 1-3 minutes...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
              Searches literature, analyzes papers, detects conflicts, generates questions & hypotheses.
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
            <Button variant="secondary" onClick={handleCloseModal}>Close (Continues in Background)</Button>
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
