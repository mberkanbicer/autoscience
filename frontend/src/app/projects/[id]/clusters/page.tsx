'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { papersApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Layers, BookOpen, Hash, AlertTriangle } from 'lucide-react';

interface Cluster {
  id: string;
  name?: string;
  description?: string;
  cluster_type?: string;
  labels: string[];
  paper_count: number;
  papers?: Record<string, unknown>[];
}

export default function ClustersPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadClusters();
  }, [projectId]);

  async function loadClusters() {
    setLoading(true);
    try {
      const data = await papersApi.clusters(projectId);
      setClusters(data || []);
    } catch (e) {
      setError('Failed to load clusters');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-white">Paper Clusters</h1>
        {[1,2,3].map(i => (
          <div key={i} className="h-28 bg-gray-800 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Paper Clusters</h1>
        <Card className="p-8 text-center">
          <AlertTriangle size={48} className="mx-auto mb-3 text-yellow-500" />
          <p className="text-gray-400">{error}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Paper Clusters</h1>
        <Badge variant="info" size="md">
          {clusters.length} clusters
        </Badge>
      </div>

      {clusters.length === 0 ? (
        <EmptyState
          title="No clusters yet"
          description="Run a research cycle to discover thematic clusters in your literature."
          icon={<Layers size={48} className="text-gray-500" />}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {clusters.map((cluster) => {
            const isExpanded = expandedId === cluster.id;
            return (
              <Card
                key={cluster.id}
                className={`p-5 cursor-pointer transition-all ${isExpanded ? 'ring-2 ring-purple-500' : 'hover:border-gray-600'}`}
                onClick={() => setExpandedId(isExpanded ? null : cluster.id)}
              >
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-white truncate">
                        {cluster.name || cluster.cluster_type || 'Unnamed Cluster'}
                      </h3>
                      {cluster.description && (
                        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{cluster.description}</p>
                      )}
                    </div>
                    {cluster.cluster_type && (
                      <Badge variant="info" size="sm" className="shrink-0 ml-2">
                        {cluster.cluster_type}
                      </Badge>
                    )}
                  </div>

                  {/* Stats row */}
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <BookOpen size={14} />
                      <span>{cluster.paper_count} papers</span>
                    </div>
                    {cluster.labels && cluster.labels.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Hash size={14} />
                        <span>{cluster.labels.length} labels</span>
                      </div>
                    )}
                  </div>

                  {/* Labels */}
                  {cluster.labels && cluster.labels.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {cluster.labels.slice(0, isExpanded ? undefined : 5).map((label, i) => (
                        <Badge key={i} variant="default" size="sm">
                          {label}
                        </Badge>
                      ))}
                      {!isExpanded && cluster.labels.length > 5 && (
                        <Badge variant="default" size="sm">+{cluster.labels.length - 5}</Badge>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
