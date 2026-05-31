'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { hypothesesApi } from '@/lib/api';
import { Hypothesis } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { FlaskConical, Target, AlertTriangle, CheckCircle, TrendingUp, Trash2, FileSearch } from 'lucide-react';

export default function HypothesesPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [validationPlan, setValidationPlan] = useState<any>(null);
  const [viewingValidation, setViewingValidation] = useState<string | null>(null);

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
      setHypotheses(hypotheses.filter(h => h.id !== id));
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

  return (
    <Layout projectId={projectId}>
      <Header
        title="Hypotheses"
        subtitle={`${hypotheses.length} hypotheses formulated`}
      />

      <div className="p-6">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : hypotheses.length === 0 ? (
          <EmptyState
            icon={<FlaskConical className="w-8 h-8 text-gray-400" />}
            title="No hypotheses yet"
            description="Hypotheses are generated from research questions during research runs."
          />
        ) : (
          <div className="space-y-4">
            {hypotheses.map((hypothesis) => (
              <Card key={hypothesis.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium mb-2">{hypothesis.statement}</p>
                    {hypothesis.context && (
                      <p className="text-sm text-gray-600 mb-3">{hypothesis.context}</p>
                    )}
                  </div>
                  <div className="ml-4 flex-shrink-0 flex items-center gap-2">
                    {hypothesis.confidence !== null && hypothesis.confidence !== undefined && (
                      <Badge variant="info">
                        <TrendingUp size={12} className="mr-1" />
                        {(hypothesis.confidence * 100).toFixed(0)}%
                      </Badge>
                    )}
                    <StatusBadge status={hypothesis.status} />
                    <button
                      onClick={() => handleViewValidation(hypothesis.id)}
                      className="text-blue-500 hover:text-blue-700"
                      title="View validation plan"
                    >
                      <FileSearch size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(hypothesis.id)}
                      disabled={deletingId === hypothesis.id}
                      className="text-red-500 hover:text-red-700 disabled:opacity-50"
                      title="Delete hypothesis"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Independent Variable */}
                  {hypothesis.independent_variable && (
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Target size={14} className="text-blue-600" />
                        <span className="text-xs font-medium text-blue-600 uppercase">Independent Variable</span>
                      </div>
                      <p className="text-sm text-blue-800">{hypothesis.independent_variable}</p>
                    </div>
                  )}

                  {/* Dependent Variable */}
                  {hypothesis.dependent_variable && (
                    <div className="bg-green-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle size={14} className="text-green-600" />
                        <span className="text-xs font-medium text-green-600 uppercase">Dependent Variable</span>
                      </div>
                      <p className="text-sm text-green-800">{hypothesis.dependent_variable}</p>
                    </div>
                  )}
                </div>

                {/* Additional Details */}
                <div className="space-y-2 text-sm">
                  {hypothesis.expected_direction && (
                    <div>
                      <span className="font-medium text-gray-700">Expected Direction:</span>{' '}
                      <span className="text-gray-600">{hypothesis.expected_direction}</span>
                    </div>
                  )}
                  {hypothesis.baseline && (
                    <div>
                      <span className="font-medium text-gray-700">Baseline:</span>{' '}
                      <span className="text-gray-600">{hypothesis.baseline}</span>
                    </div>
                  )}
                  {hypothesis.metric && (
                    <div>
                      <span className="font-medium text-gray-700">Metric:</span>{' '}
                      <span className="text-gray-600">{hypothesis.metric}</span>
                    </div>
                  )}
                  {hypothesis.dataset_requirement && (
                    <div>
                      <span className="font-medium text-gray-700">Dataset:</span>{' '}
                      <span className="text-gray-600">{hypothesis.dataset_requirement}</span>
                    </div>
                  )}
                </div>

                {/* Failure Condition */}
                {hypothesis.failure_condition && (
                  <div className="mt-4 bg-red-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={14} className="text-red-600" />
                      <span className="text-xs font-medium text-red-600 uppercase">Failure Condition</span>
                    </div>
                    <p className="text-sm text-red-700">{hypothesis.failure_condition}</p>
                  </div>
                )}

                <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
                  <span>Version {hypothesis.version}</span>
                  <span>Created {formatDate(hypothesis.created_at)}</span>
                </div>

                {/* Validation Plan Display */}
                {viewingValidation === hypothesis.id && validationPlan && (
                  <div className="mt-4 bg-blue-50 rounded-lg p-4 border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <FileSearch size={14} className="text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">Validation Plan</span>
                    </div>
                    {validationPlan.experiment_design && (
                      <p className="text-sm text-blue-700 mb-2">{validationPlan.experiment_design}</p>
                    )}
                    {validationPlan.datasets && (
                      <p className="text-xs text-blue-600">Datasets: {validationPlan.datasets}</p>
                    )}
                    {validationPlan.baselines && (
                      <p className="text-xs text-blue-600">Baselines: {validationPlan.baselines}</p>
                    )}
                  </div>
                )}
                {viewingValidation === hypothesis.id && !validationPlan && (
                  <div className="mt-4 bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">No validation plan available for this hypothesis.</p>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
