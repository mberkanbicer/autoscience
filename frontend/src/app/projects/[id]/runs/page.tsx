'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Input, Textarea, Select } from '@/components/ui/Input';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { runsApi } from '@/lib/api';
import { ResearchRun } from '@/lib/types';
import { formatDate, formatDuration } from '@/lib/utils';
import { Activity, Clock, DollarSign, Play, Loader2, CheckCircle2, XCircle } from 'lucide-react';

export default function RunsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [starting, setStarting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [startResult, setStartResult] = useState<{ success: boolean; message: string; runId?: string } | null>(null);
  const [newRun, setNewRun] = useState({
    idea: '',
    run_type: 'user_directed',
  });
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadRuns();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [projectId]);

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

  const startPolling = (runId: string) => {
    setPolling(true);
    let attempts = 0;
    const maxAttempts = 120; // 2 minutes max
    
    pollRef.current = setInterval(async () => {
      attempts++;
      const updatedRuns = await loadRuns();
      
      const run = updatedRuns.find((r: ResearchRun) => r.id === runId);
      if (run && (run.state === 'completed' || run.state === 'failed' || run.state === 'error')) {
        // Stop polling
        if (pollRef.current) clearInterval(pollRef.current);
        setPolling(false);
        setStarting(false);
        
        if (run.state === 'completed') {
          setStartResult({
            success: true,
            message: `Research completed successfully! Check the Ideas, Papers, Questions, and Hypotheses pages for results.`,
            runId: run.id,
          });
        } else {
          setStartResult({
            success: false,
            message: `Research run ${run.state}. Check the backend logs for details.`,
            runId: run.id,
          });
        }
      }
      
      if (attempts >= maxAttempts) {
        if (pollRef.current) clearInterval(pollRef.current);
        setPolling(false);
        setStarting(false);
        setStartResult({
          success: false,
          message: 'Research is still running. Check back in a few minutes.',
          runId,
        });
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleStartRun = async () => {
    if (!newRun.idea.trim()) return;
    setStarting(true);
    setStartResult(null);
    
    try {
      const apiSettings = JSON.parse(localStorage.getItem('autoscience_api_settings') || '{}');
      
      // Fire the request - it will take time but we don't wait for response
      // Instead, we poll for completion
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout for initial response
      
      try {
        const response = await fetch(`/api/v1/research/run?project_id=${projectId}&idea=${encodeURIComponent(newRun.idea)}&run_type=${newRun.run_type}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-OpenRouter-API-Key': apiSettings.openrouter_api_key || '',
            'X-OpenRouter-Model': apiSettings.openrouter_model || 'openai/gpt-4o',
            'X-OpenAI-API-Key': apiSettings.openai_api_key || '',
            'X-OpenAI-Model': apiSettings.openai_model || 'gpt-4o',
            'X-Anthropic-API-Key': apiSettings.anthropic_api_key || '',
            'X-Anthropic-Model': apiSettings.anthropic_model || 'claude-sonnet-4-20250514',
            'X-Default-Provider': apiSettings.default_provider || 'openrouter',
          },
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const result = await response.json();
          setStarting(false);
          setStartResult({
            success: true,
            message: `Research completed! Found ${result.papers_found} papers, ${result.questions_generated} questions, ${result.hypotheses_formed} hypotheses.`,
            runId: result.run_id,
          });
          loadRuns();
          return;
        }
      } catch (fetchError: any) {
        if (fetchError.name === 'AbortError') {
          // Expected - the request is still running in background
          console.log('Request still running, starting poll...');
        } else {
          throw fetchError;
        }
      }
      
      // If we get here, the request is still running - poll for completion
      // Wait a moment for the run to be created in the DB
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const updatedRuns = await loadRuns();
      // Find the most recent run
      const latestRun = updatedRuns[0];
      if (latestRun && latestRun.state === 'running') {
        startPolling(latestRun.id);
      } else {
        // Run might have completed very quickly
        setStarting(false);
        setStartResult({
          success: true,
          message: 'Research submitted. Check the runs list for results.',
        });
      }
      
    } catch (error: any) {
      console.error('Failed to start research run:', error);
      setStarting(false);
      setStartResult({
        success: false,
        message: error.message || 'Failed to start research run. Make sure the backend is running.',
      });
    }
  };

  const handleCloseModal = () => {
    if (!starting) {
      setShowCreateModal(false);
      setStartResult(null);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Runs"
        subtitle={`${runs.length} runs completed`}
        actions={
          <Button onClick={() => setShowCreateModal(true)} disabled={starting}>
            <Play size={18} className="mr-2" />
            Start Research Run
          </Button>
        }
      />

      <div className="p-6">
        {loading ? (
          <SkeletonTable />
        ) : runs.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-8 h-8 text-gray-400" />}
            title="No research runs yet"
            description="Start a research run to begin autonomous literature analysis, conflict detection, and hypothesis generation."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Play size={18} className="mr-2" />
                Start First Run
              </Button>
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>State</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Completed</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Budget</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>
                    <Badge variant="info">{run.run_type}</Badge>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={run.state} />
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-gray-600">
                      {run.started_at ? formatDate(run.started_at) : '—'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-gray-600">
                      {run.completed_at ? formatDate(run.completed_at) : '—'}
                    </span>
                  </TableCell>
                  <TableCell>
                    {run.started_at && run.completed_at ? (
                      <div className="flex items-center gap-1 text-gray-600">
                        <Clock size={14} />
                        <span className="text-sm">{formatDuration(run.started_at, run.completed_at)}</span>
                      </div>
                    ) : run.state === 'running' ? (
                      <div className="flex items-center gap-1 text-blue-600">
                        <Loader2 size={14} className="animate-spin" />
                        <span className="text-sm">Running...</span>
                      </div>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-gray-600">
                      <DollarSign size={14} />
                      <span className="text-sm">
                        ${run.max_cost_usd.toFixed(2)}
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Start Research Run Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={handleCloseModal}
        title="Start Research Run"
        size="lg"
      >
        {startResult ? (
          /* Result View */
          <div className="space-y-4">
            <div className={`rounded-lg p-4 text-sm ${startResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
              <div className="flex items-center gap-2 mb-2">
                {startResult.success ? (
                  <CheckCircle2 size={20} className="text-green-600" />
                ) : (
                  <XCircle size={20} className="text-red-600" />
                )}
                <strong>{startResult.success ? 'Research Completed!' : 'Research Failed'}</strong>
              </div>
              <p>{startResult.message}</p>
            </div>
          </div>
        ) : starting ? (
          /* Loading View */
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 size={48} className="animate-spin text-blue-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Research in Progress</h3>
              <p className="text-sm text-gray-600 text-center max-w-md">
                {polling 
                  ? "Searching literature, analyzing papers, generating hypotheses..."
                  : "Starting research run..."}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                This may take 1-3 minutes. You can close this dialog and check back later.
              </p>
            </div>
          </div>
        ) : (
          /* Form View */
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
              <strong>What happens:</strong> The system will search academic literature, analyze papers,
              detect conflicts, generate research questions, and form hypotheses based on your idea.
              <br /><br />
              <strong>Note:</strong> This may take 1-3 minutes depending on the complexity.
            </div>
            
            <Textarea
              label="Research Idea"
              placeholder="Describe what you want to research... (e.g., 'Using attention mechanisms for time series forecasting')"
              rows={4}
              value={newRun.idea}
              onChange={(e) => setNewRun({ ...newRun, idea: e.target.value })}
              disabled={starting}
            />
            
            <Select
              label="Run Type"
              value={newRun.run_type}
              onChange={(e) => setNewRun({ ...newRun, run_type: e.target.value })}
              disabled={starting}
              options={[
                { value: 'user_directed', label: 'User Directed - Focus on your specific idea' },
                { value: 'idle_exploration', label: 'Idle Exploration - Broader exploration' },
                { value: 'literature_review', label: 'Literature Review - Deep paper analysis' },
              ]}
            />
          </div>
        )}

        <ModalFooter>
          {starting ? (
            <Button variant="secondary" onClick={handleCloseModal}>
              Close (Research Continues in Background)
            </Button>
          ) : startResult ? (
            <Button onClick={handleCloseModal}>
              Done
            </Button>
          ) : (
            <>
              <Button variant="secondary" onClick={handleCloseModal}>
                Cancel
              </Button>
              <Button onClick={handleStartRun} disabled={!newRun.idea.trim()}>
                <Play size={16} className="mr-2" />
                Start Research
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
