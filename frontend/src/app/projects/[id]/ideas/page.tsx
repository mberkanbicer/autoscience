'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { ideasApi } from '@/lib/api';
import { Idea } from '@/lib/types';
import { formatDate, getClassificationColor, truncate } from '@/lib/utils';

export default function IdeasPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: '', classification: '' });

  useEffect(() => {
    loadIdeas();
  }, [projectId, filter]);

  const loadIdeas = async () => {
    try {
      const params: Record<string, string> = {};
      if (filter.status) params.status = filter.status;
      if (filter.classification) params.classification = filter.classification;
      const data = await ideasApi.list(projectId, params);
      setIdeas(data);
    } catch (error) {
      console.error('Failed to load ideas:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Header title="Ideas" />

      <div className="p-6">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex gap-4">
            <select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="rejected">Rejected</option>
              <option value="promoted">Promoted</option>
              <option value="archived">Archived</option>
            </select>
            <select
              value={filter.classification}
              onChange={(e) =>
                setFilter({ ...filter, classification: e.target.value })
              }
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">All Classifications</option>
              <option value="high_value">High Value</option>
              <option value="promising">Promising</option>
              <option value="incremental">Incremental</option>
              <option value="weak">Weak</option>
              <option value="reject">Reject</option>
            </select>
          </div>
        </div>

        {/* Ideas List */}
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : ideas.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No ideas found</div>
        ) : (
          <div className="space-y-4">
            {ideas.map((idea) => (
              <div
                key={idea.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-1 rounded text-xs ${getClassificationColor(
                          idea.classification || ''
                        )}`}
                      >
                        {idea.classification || 'Unclassified'}
                      </span>
                      <span className="text-sm text-gray-500">
                        Score: {idea.overall_score?.toFixed(2) || 'N/A'}
                      </span>
                      <span className="text-sm text-gray-500">
                        Origin: {idea.origin}
                      </span>
                    </div>
                    <p className="text-gray-800 mb-2">
                      {truncate(idea.current_text, 200)}
                    </p>
                    <div className="text-sm text-gray-500">
                      Created: {formatDate(idea.created_at)}
                    </div>
                  </div>
                  <div className="ml-4">
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        idea.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : idea.status === 'rejected'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {idea.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
