'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { approvalsApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { CheckCircle, XCircle, Clock, AlertTriangle, ExternalLink } from 'lucide-react';

interface ApprovalItem {
  id: string;
  action_type: string;
  description: string;
  status: string;
  requested_by: string;
  created_at: string;
  reviewer_notes?: string;
}

const statusColors: Record<string, 'warning' | 'success' | 'danger' | 'default'> = {
  pending: 'warning',
  approved: 'success',
  denied: 'danger',
};

export default function ApprovalsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => { loadApprovals(); }, [projectId]);

  async function loadApprovals() {
    try {
      const data = await approvalsApi.list(projectId);
      setApprovals(data);
    } catch (e) {
      console.error('Failed to load approvals:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id: string) {
    setProcessingId(id);
    try { await approvalsApi.approve(id); await loadApprovals(); }
    catch (e) { console.error(e); }
    finally { setProcessingId(null); }
  }

  async function handleDeny(id: string) {
    setProcessingId(id);
    try { await approvalsApi.deny(id, 'Rejected by user'); await loadApprovals(); }
    catch (e) { console.error(e); }
    finally { setProcessingId(null); }
  }

  function renderActionIcon(actionType: string) {
    switch (actionType) {
      case 'external_search': return <ExternalLink size={16} />;
      case 'data_export': return <ExternalLink size={16} />;
      default: return <Clock size={16} />;
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
        {[1,2,3].map(i => (
          <div key={i} className="h-24 bg-gray-800 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const pending = approvals.filter(a => a.status === 'pending');
  const history = approvals.filter(a => a.status !== 'pending');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
        <Badge variant="warning" size="lg">
          {pending.length} pending
        </Badge>
      </div>

      {approvals.length === 0 ? (
        <EmptyState
          title="No approval requests"
          description="Approval requests will appear here when the system needs manual confirmation."
          icon={<CheckCircle size={48} className="text-gray-500" />}
        />
      ) : (
        <>
          {pending.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-white">Pending Requests</h2>
              {pending.map(a => (
                <Card key={a.id} className="p-4 border-l-4 border-yellow-500">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle size={16} className="text-yellow-500 shrink-0" />
                        <span className="text-sm font-medium text-white capitalize">{a.action_type.replace(/_/g, ' ')}</span>
                        <Badge variant="warning" size="sm">Pending</Badge>
                      </div>
                      <p className="text-sm text-gray-400">{a.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Requested {new Date(a.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleApprove(a.id)}
                        disabled={processingId === a.id}
                      >
                        <CheckCircle size={14} className="mr-1" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleDeny(a.id)}
                        disabled={processingId === a.id}
                      >
                        <XCircle size={14} className="mr-1" />
                        Deny
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {history.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-white">History</h2>
              {history.map(a => (
                <Card key={a.id} className="p-4 border-l-4 border-gray-600">
                  <div className="flex items-center gap-3">
                    {renderActionIcon(a.action_type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-300 capitalize">{a.action_type.replace(/_/g, ' ')}</span>
                        <Badge variant={statusColors[a.status] || 'default'} size="sm">
                          {a.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500">{a.description}</p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
