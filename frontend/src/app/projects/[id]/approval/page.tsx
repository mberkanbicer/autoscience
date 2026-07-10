'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { approvalsApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import { DecisionGate } from '@/components/ui/DecisionGate';
import { EmptyState } from '@/components/ui/EmptyState';
import { CheckCircle, Clock, AlertTriangle, XCircle } from 'lucide-react';

interface ApprovalItem {
  id: string;
  action_type: string;
  action_description?: string;
  status: string;
  created_at: string;
  reviewer_notes?: string;
  action_payload?: Record<string, unknown>;
}

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
      setApprovals(data as unknown as ApprovalItem[]);
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

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Approval Queue" />
        <div className="space-y-6 p-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="h-32 bg-muted/40 glass rounded-2xl animate-pulse" />
          ))}
        </div>
      </Layout>
    );
  }

  const pending = approvals.filter(a => a.status === 'pending');
  const history = approvals.filter(a => a.status !== 'pending');

  return (
    <Layout projectId={projectId}>
      <Header 
        title="Approval Queue" 
        subtitle="Manual oversight of sensitive laboratory operations"
        actions={
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-3 h-3 rounded-full",
              pending.length > 0 ? "bg-warning animate-ping" : "bg-muted"
            )} />
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">
              {pending.length} Pending Actions
            </span>
            {pending.length > 0 && (
              <span className="text-[10px] font-black text-warning uppercase tracking-[0.2em]">
                REQUIRES_ATTENTION
              </span>
            )}
          </div>
        }
      />
      <div className="space-y-12 p-6 animate-in fade-in duration-700">
        {approvals.length === 0 ? (
          <EmptyState
            title="Oversight Queue Empty"
            description="Autonomous operations requiring manual confirmation will appear here."
            icon={<CheckCircle size={48} className="text-muted-foreground/30" />}
          />
        ) : (
          <>
            {pending.length > 0 && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 mb-6">
                   <div className="p-2 bg-warning/10 rounded-lg">
                      <AlertTriangle size={18} className="text-warning animate-pulse" />
                   </div>
                   <h2 className="text-sm font-bold text-foreground uppercase tracking-[0.2em]">Priority Oversight Required</h2>
                </div>
                <div className="grid gap-4">
                  {pending.map(a => (
                    <DecisionGate
                      key={a.id}
                      actionType={a.action_type}
                      status="pending"
                      description={a.action_description}
                      costUsd={a.action_payload?.projected_cost_usd as number}
                    >
                      <div className="flex gap-3 pt-4">
                        <button
                          onClick={() => handleApprove(a.id)}
                          disabled={processingId === a.id}
                          className="px-6 py-3 rounded-xl bg-success text-white font-bold text-[10px] uppercase tracking-widest shadow-lg shadow-success/20 hover:scale-105 transition-all"
                        >
                          <CheckCircle size={16} className="inline mr-2" />
                          Commit Action
                        </button>
                        <button
                          onClick={() => handleDeny(a.id)}
                          disabled={processingId === a.id}
                          className="px-6 py-3 rounded-xl bg-error text-white font-bold text-[10px] uppercase tracking-widest shadow-lg shadow-error/20 hover:scale-105 transition-all"
                        >
                          <XCircle size={16} className="inline mr-2" />
                          Halt Action
                        </button>
                      </div>
                    </DecisionGate>
                  ))}
                </div>
              </div>
            )}

            {history.length > 0 && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 mb-6">
                   <div className="p-2 bg-muted rounded-lg border border-border/10">
                      <Clock size={18} className="text-muted-foreground/60" />
                   </div>
                   <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.2em]">Archived Decisions</h2>
                </div>
                <div className="grid gap-2">
                  {history.map(a => (
                    <DecisionGate
                      key={a.id}
                      actionType={a.action_type}
                      status={a.status as any}
                      description={a.action_description}
                      costUsd={a.action_payload?.projected_cost_usd as number}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
