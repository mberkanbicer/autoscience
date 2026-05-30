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
import { FlaskConical, Target, AlertTriangle, CheckCircle } from 'lucide-react';

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
                    {hypothesis.rationale && (
                      <p className="text-sm text-gray-600 mb-3">{hypothesis.rationale}</p>
                    )}
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <StatusBadge status={hypothesis.status} />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Independent Variables */}
                  {hypothesis.independent_variables && hypothesis.independent_variables.length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Target size={14} className="text-blue-600" />
                        <span className="text-xs font-medium text-blue-600 uppercase">Independent Variables</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {hypothesis.independent_variables.map((v, i) => (
                          <Badge key={i} variant="info" size="sm">{v}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Dependent Variables */}
                  {hypothesis.dependent_variables && hypothesis.dependent_variables.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle size={14} className="text-green-600" />
                        <span className="text-xs font-medium text-green-600 uppercase">Dependent Variables</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {hypothesis.dependent_variables.map((v, i) => (
                          <Badge key={i} variant="success" size="sm">{v}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Baseline Comparison */}
                {hypothesis.baseline_comparison && (
                  <div className="text-sm text-gray-600 mb-3">
                    <span className="font-medium">Baseline:</span> {hypothesis.baseline_comparison}
                  </div>
                )}

                {/* Failure Conditions */}
                {hypothesis.failure_conditions && hypothesis.failure_conditions.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={14} className="text-red-600" />
                      <span className="text-xs font-medium text-red-600 uppercase">Failure Conditions</span>
                    </div>
                    <ul className="text-sm text-red-700 space-y-1">
                      {hypothesis.failure_conditions.map((condition, i) => (
                        <li key={i}>• {condition}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="mt-4 text-xs text-gray-400">
                  Created {formatDate(hypothesis.created_at)}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
