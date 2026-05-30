'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { runsApi } from '@/lib/api';
import { ResearchRun } from '@/lib/types';
import { formatDate, formatDuration } from '@/lib/utils';
import { Activity, Clock, DollarSign } from 'lucide-react';

export default function RunsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Runs"
        subtitle={`${runs.length} runs completed`}
      />

      <div className="p-6">
        {loading ? (
          <SkeletonTable />
        ) : runs.length === 0 ? (
          <EmptyState
            icon={<Activity className="w-8 h-8 text-gray-400" />}
            title="No research runs yet"
            description="Start a research run to begin autonomous literature analysis."
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
                <TableHead>Budget Used</TableHead>
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
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-gray-600">
                      <DollarSign size={14} />
                      <span className="text-sm">
                        {run.budget_usd ? `$${run.budget_usd.toFixed(2)}` : '—'}
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </Layout>
  );
}
