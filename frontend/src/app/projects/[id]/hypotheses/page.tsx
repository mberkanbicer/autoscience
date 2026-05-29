'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { hypothesesApi } from '@/lib/api';
import { Hypothesis } from '@/lib/types';
import { truncate } from '@/lib/utils';

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
    <Layout>
      <Header title="Hypotheses" />

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : hypotheses.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No hypotheses found</div>
        ) : (
          <div className="space-y-6">
            {hypotheses.map((hypothesis) => (
              <div
                key={hypothesis.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        hypothesis.status === 'validated'
                          ? 'bg-green-100 text-green-800'
                          : hypothesis.status === 'rejected'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {hypothesis.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      Confidence: {hypothesis.confidence?.toFixed(2) || 'N/A'}
                    </span>
                    <span className="text-sm text-gray-500">
                      Version: {hypothesis.version}
                    </span>
                  </div>
                </div>

                <p className="text-gray-800 mb-4 font-medium">
                  {hypothesis.statement}
                </p>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Independent Variable:</span>
                    <p className="text-gray-600">{hypothesis.independent_variable || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Dependent Variable:</span>
                    <p className="text-gray-600">{hypothesis.dependent_variable || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Baseline:</span>
                    <p className="text-gray-600">{hypothesis.baseline || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Metric:</span>
                    <p className="text-gray-600">{hypothesis.metric || 'N/A'}</p>
                  </div>
                </div>

                {hypothesis.failure_condition && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg">
                    <span className="text-sm font-medium text-red-800">
                      Failure Condition:
                    </span>
                    <p className="text-sm text-red-700 mt-1">
                      {hypothesis.failure_condition}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
