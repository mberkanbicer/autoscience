'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ValidationPlanEditor } from '@/components/ui/ValidationPlanEditor';
import { hypothesesApi } from '@/lib/api';
import { Hypothesis, ValidationPlan } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import {
  FlaskConical,
  Target,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Trash2,
  FileSearch,
  DollarSign,
  Activity,
  Loader2,
  Beaker,
} from 'lucide-react';

export default function HypothesesPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [validationPlan, setValidationPlan] = useState<ValidationPlan | null>(null);
  const [viewingValidation, setViewingValidation] = useState<string | null>(null);
  const [showValidationEditor, setShowValidationEditor] = useState<string | null>(null);

  useEffect(() => {
    loadHypotheses();
  }, [projectId]);

  const loadHypotheses = async () => {
    try {
      const data = await hypothesesApi.list(projectId);
      setHypotheses(data);
    } catch (error) {
      console.error('Failed to load hypotheses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this hypothesis?')) return;
    setDeletingId(id);
    try {
      await hypothesesApi.update(id, { status: 'rejected' });
      setHypotheses(hypotheses.filter((h) => h.id !== id));
    } catch (error) {
      console.error('Failed to delete hypothesis:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewValidation = async (id: string) => {
    setViewingValidation(id);
    try {
      const plan = await hypothesesApi.validation(id);
      setValidationPlan(plan);
    } catch (error) {
      setValidationPlan(null);
    }
  };

  const renderValidationPlanView = (hypothesis: Hypothesis) => {
    if (viewingValidation !== hypothesis.id) return null;

    return (
      <div className="mt-6 animate-in slide-in-from-top-4 duration-500">
        {validationPlan ? (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => setShowValidationEditor(hypothesis.id)}
                className="text-xs font-bold text-primary hover:text-primary/70 transition-colors flex items-center gap-1"
              >
                <Beaker size={14} />
                Open in Editor
              </button>
            </div>

            <div className="glass p-6 rounded-2xl border-primary/20 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-5">
                <FileSearch size={120} className="text-primary" />
              </div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <FileSearch size={18} className="text-primary" />
                  </div>
                  <h4 className="text-sm font-bold text-foreground uppercase tracking-[0.2em]">
                    Scientific Validation Plan
                  </h4>
                  <div className="ml-auto px-3 py-1 bg-success/10 rounded-full border border-success/20">
                    <span className="text-[10px] font-bold text-success uppercase">
                      Feasibility:{' '}
                      {validationPlan.feasibility_score != null
                        ? (validationPlan.feasibility_score * 100).toFixed(0) + '%'
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="space-y-6">
                  {validationPlan.experimental_design && (
                    <div className="bg-white/40 p-4 rounded-xl border border-border/5">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">
                        Experimental Methodology
                      </p>
                      <p className="text-sm font-medium text-foreground/80 leading-relaxed">
                        {validationPlan.experimental_design}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <p className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-widest px-1">
                        Evidence Repositories
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(validationPlan.dataset_candidates || []).map((d: any, i: number) => (
                          <span
                            key={i}
                            className="text-[10px] font-bold bg-primary/5 text-primary border border-primary/10 px-3 py-1 rounded-lg"
                          >
                            {(d.name || d).toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-widest px-1">
                        Control Benchmarks
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(validationPlan.baselines || []).map((b: string, i: number) => (
                          <span
                            key={i}
                            className="text-[10px] font-bold bg-muted text-muted-foreground/60 border border-border/10 px-3 py-1 rounded-lg"
                          >
                            {b.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-widest px-1">
                        Unit of Measurement
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(validationPlan.metrics || []).map((m: string, i: number) => (
                          <span
                            key={i}
                            className="text-[10px] font-bold bg-tertiary/5 text-tertiary border border-tertiary/10 px-3 py-1 rounded-lg"
                          >
                            {m.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border/10 flex items-center gap-8">
                    <div className="flex items-center gap-2">
                      <DollarSign size={14} className="text-success" />
                      <span className="text-[11px] font-bold text-foreground/60 uppercase">
                        Cost:{' '}
                        {validationPlan.cost_estimate != null
                          ? '$' + validationPlan.cost_estimate.toFixed(0)
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Activity size={14} className="text-warning" />
                      <span className="text-[11px] font-bold text-foreground/60 uppercase">
                        Complexity:{' '}
                        {validationPlan.difficulty_estimate != null
                          ? (validationPlan.difficulty_estimate * 100).toFixed(0) + '%'
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center glass border-dashed rounded-2xl animate-pulse">
            <Loader2 size={24} className="mx-auto mb-3 text-primary/40 animate-spin" />
            <p className="text-xs font-bold text-muted-foreground/40 uppercase tracking-[0.2em]">
              Assembling Validation Matrix...
            </p>
          </div>
        )}

        {showValidationEditor === hypothesis.id && validationPlan && (
          <div className="mt-6 animate-in slide-in-from-top-4 duration-500 border-t border-border/10 pt-6">
            <ValidationPlanEditor
              hypothesisId={hypothesis.id}
              hypothesisStatement={hypothesis.statement}
              plan={{
                hypothesis_id: hypothesis.id,
                hypothesis_statement: hypothesis.statement,
                steps: [],
                metrics: validationPlan.metrics || [],
                baselines: validationPlan.baselines || [],
                datasets: (validationPlan.dataset_candidates || []).map((d: any) =>
                  typeof d === 'string' ? d : d.name
                ),
                experimental_design: validationPlan.experimental_design || '',
                statistical_tests: validationPlan.statistical_tests || [],
                feasibility_score: validationPlan.feasibility_score,
                cost_estimate: validationPlan.cost_estimate,
              }}
            />
          </div>
        )}
      </div>
    );
  };

  const renderDetailGrid = (detail: { label: string; value: string | null | undefined }, i: number) => {
    if (!detail.value) return null;
    return (
      <div key={i} className="space-y-1">
        <p className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-[0.2em]">
          {detail.label}
        </p>
        <p className="text-xs font-bold text-foreground/60">{detail.value}</p>
      </div>
    );
  };

  const renderHypothesisCard = (hypothesis: Hypothesis) => (
    <Card key={hypothesis.id} className="p-8 group overflow-hidden">
      <div className="flex items-start justify-between gap-6 mb-6">
        <div className="flex-1 min-w-0">
          <p className="text-lg font-bold text-foreground tracking-tight leading-relaxed">
            {hypothesis.statement}
          </p>
          {hypothesis.context && (
            <p className="text-sm text-muted-foreground mt-3 font-medium leading-relaxed italic border-l-2 border-primary/20 pl-4">
              {hypothesis.context}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {hypothesis.confidence !== null && hypothesis.confidence !== undefined && (
            <Badge
              variant="info"
              className="bg-primary/5 uppercase text-[10px] font-bold tracking-[0.2em] px-3 py-1"
            >
              <TrendingUp size={12} className="mr-2 animate-pulse" />
              {Math.round(hypothesis.confidence * 100)}% Confidence
            </Badge>
          )}
          <StatusBadge status={hypothesis.status} />
          <div className="flex items-center gap-1 ml-2">
            <button
              onClick={() => handleViewValidation(hypothesis.id)}
              className="p-2 rounded-lg hover:bg-primary/10 text-primary transition-all duration-300 hover:scale-110"
              title="Cognitive Validation Plan"
            >
              <FileSearch size={18} />
            </button>
            <button
              onClick={() => handleDelete(hypothesis.id)}
              disabled={deletingId === hypothesis.id}
              className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300 hover:scale-110 disabled:opacity-30"
              title="Archive Hypothesis"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {hypothesis.independent_variable && (
          <div className="bg-primary/5 backdrop-blur-sm rounded-xl p-4 border border-primary/10 shadow-inner group-hover:bg-primary/10 transition-colors">
            <div className="flex items-center gap-2 mb-3">
              <Target size={14} className="text-primary" />
              <span className="text-[10px] font-bold text-primary uppercase tracking-[0.2em]">
                Independent Variable
              </span>
            </div>
            <p className="text-sm font-bold text-foreground/70">{hypothesis.independent_variable}</p>
          </div>
        )}
        {hypothesis.dependent_variable && (
          <div className="bg-success/5 backdrop-blur-sm rounded-xl p-4 border border-success/10 shadow-inner group-hover:bg-success/10 transition-colors">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle size={14} className="text-success" />
              <span className="text-[10px] font-bold text-success uppercase tracking-[0.2em]">
                Dependent Variable
              </span>
            </div>
            <p className="text-sm font-bold text-foreground/70">{hypothesis.dependent_variable}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 px-4 py-6 bg-muted/20 rounded-2xl border border-border/5">
        {[
          { label: 'Direction', value: hypothesis.expected_direction },
          { label: 'Baseline', value: hypothesis.baseline },
          { label: 'Metric', value: hypothesis.metric },
          { label: 'Target Dataset', value: hypothesis.dataset_requirement },
        ].map((detail, i) => renderDetailGrid(detail, i))}
      </div>

      {hypothesis.failure_condition && (
        <div className="mt-6 p-4 bg-error/5 border border-error/10 rounded-xl flex items-start gap-4">
          <div className="p-2 bg-error/10 rounded-lg">
            <AlertTriangle size={16} className="text-error" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-error uppercase tracking-[0.2em]">
              Falsification Condition
            </span>
            <p className="text-xs font-medium text-error/80 mt-1">{hypothesis.failure_condition}</p>
          </div>
        </div>
      )}

      <div className="mt-8 flex items-center justify-between pt-4 border-t border-border/5">
        <span className="text-[10px] font-mono font-bold text-muted-foreground/30 uppercase tracking-[0.3em]">
          H_VERSION {hypothesis.version}.0
        </span>
        <span className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">
          {formatDate(hypothesis.created_at)}
        </span>
      </div>

      {renderValidationPlanView(hypothesis)}
    </Card>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      );
    }

    if (hypotheses.length === 0) {
      return (
        <EmptyState
          icon={<FlaskConical className="w-8 h-8 text-gray-400" />}
          title="No hypotheses yet"
          description="Hypotheses are generated from research questions during research runs."
        />
      );
    }

    return <div className="grid gap-6">{hypotheses.map((h) => renderHypothesisCard(h))}</div>;
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Hypotheses"
        subtitle={`${hypotheses.length} hypotheses formulated`}
      />
      <div className="p-6">{renderContent()}</div>
    </Layout>
  );
}
