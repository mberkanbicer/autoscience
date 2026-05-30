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
import { FlaskConical, Target, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';

export default function HypothesesPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);

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
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
