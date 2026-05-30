'use client';

import { useEffect, useState } from 'react';
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
import { Activity, Clock, DollarSign, Plus, Play, Loader2 } from 'lucide-react';

export default function RunsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [starting, setStarting] = useState(false);
  const [newRun, setNewRun] = useState({
    idea: '',
    run_type: 'user_directed',
    max_minutes: 30,
    max_cost_usd: 5.0,
  });

  useEffect(() => {
    loadRuns();
  }, [projectId]);

  const loadRuns = async () => {
    try {
      const data = await runsApi.list(projectId);
      setRuns(data);
    } catch (error) {
      console.error('Failed to load runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartRun = async () => {
    if (!newRun.idea.trim()) return;
    setStarting(true);
    try {
      // Create the run via the research endpoint
      const response = await fetch(`/api/v1/research/run?project_id=${projectId}&idea=${encodeURIComponent(newRun.idea)}&run_type=${newRun.run_type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) {
        throw new Error('Failed to start research run');
      }
      
      const result = await response.json();
      console.log('Research run started:', result);
      
      setShowCreateModal(false);
      setNewRun({ idea: '', run_type: 'user_directed', max_minutes: 30, max_cost_usd: 5.0 });
      
      // Reload runs after a short delay
      setTimeout(loadRuns, 1000);
    } catch (error) {
      console.error('Failed to start research run:', error);
      alert('Failed to start research run. Make sure the backend is running.');
    } finally {
      setStarting(false);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Runs"
        subtitle={`${runs.length} runs completed`}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
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
        onClose={() => !starting && setShowCreateModal(false)}
        title="Start Research Run"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
            <strong>What happens:</strong> The system will search academic literature, analyze papers,
            detect conflicts, generate research questions, and form hypotheses based on your idea.
          </div>
          
          <Textarea
            label="Research Idea"
            placeholder="Describe what you want to research... (e.g., 'Using attention mechanisms for time series forecasting')"
            rows={4}
            value={newRun.idea}
            onChange={(e) => setNewRun({ ...newRun, idea: e.target.value })}
          />
          
          <Select
            label="Run Type"
            value={newRun.run_type}
            onChange={(e) => setNewRun({ ...newRun, run_type: e.target.value })}
            options={[
              { value: 'user_directed', label: 'User Directed - Focus on your specific idea' },
              { value: 'idle_exploration', label: 'Idle Exploration - Broader exploration' },
              { value: 'literature_review', label: 'Literature Review - Deep paper analysis' },
            ]}
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Max Duration (minutes)"
              type="number"
              min="5"
              max="120"
              value={newRun.max_minutes}
              onChange={(e) => setNewRun({ ...newRun, max_minutes: parseInt(e.target.value) || 30 })}
            />
            <Input
              label="Max Cost ($)"
              type="number"
              min="0.1"
              max="50"
              step="0.5"
              value={newRun.max_cost_usd}
              onChange={(e) => setNewRun({ ...newRun, max_cost_usd: parseFloat(e.target.value) || 5.0 })}
            />
          </div>
        </div>
        
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)} disabled={starting}>
            Cancel
          </Button>
          <Button onClick={handleStartRun} loading={starting} disabled={!newRun.idea.trim()}>
            <Play size={16} className="mr-2" />
            {starting ? 'Starting...' : 'Start Research'}
          </Button>
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
