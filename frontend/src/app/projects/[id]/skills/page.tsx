'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { skillsApi } from '@/lib/api';
import { Skill } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { GraduationCap, Zap, TrendingUp, BarChart } from 'lucide-react';

export default function SkillsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSkills();
  }, [projectId]);

  const loadSkills = async () => {
    try {
      const data = await skillsApi.list({ project_id: projectId });
      setSkills(data);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Skills"
        subtitle={`${skills.length} skills learned`}
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : skills.length === 0 ? (
          <EmptyState
            icon={<GraduationCap className="w-8 h-8 text-gray-400" />}
            title="No skills yet"
            description="Skills are automatically created from successful research cycles."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((skill) => (
              <Card key={skill.id} hover className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                    <GraduationCap className="text-orange-600" size={24} />
                  </div>
                  <StatusBadge status={skill.status} />
                </div>

                <h3 className="font-semibold text-gray-900 mb-2">{skill.name}</h3>
                {skill.purpose && (
                  <p className="text-sm text-gray-600 line-clamp-2 mb-4">{skill.purpose}</p>
                )}

                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Type</span>
                    <Badge variant="info">{skill.skill_type}</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Version</span>
                    <span className="text-gray-900">v{skill.version}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Times Used</span>
                    <div className="flex items-center gap-1 text-gray-900">
                      <Zap size={14} className="text-yellow-500" />
                      {skill.times_used}
                    </div>
                  </div>
                  {skill.times_used > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Success Rate</span>
                      <div className="flex items-center gap-1 text-gray-900">
                        <BarChart size={14} className="text-green-500" />
                        {Math.round((skill.successful_uses / skill.times_used) * 100)}%
                      </div>
                    </div>
                  )}
                  {skill.average_score_improvement !== null && skill.average_score_improvement !== undefined && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Avg Improvement</span>
                      <div className="flex items-center gap-1 text-green-600">
                        <TrendingUp size={14} />
                        +{skill.average_score_improvement.toFixed(1)}
                      </div>
                    </div>
                  )}
                </div>

                {skill.procedure.length > 0 && (
                  <div className="border-t border-gray-100 pt-4">
                    <span className="text-xs font-medium text-gray-500 uppercase">Procedure</span>
                    <ol className="mt-2 text-sm text-gray-600 space-y-1">
                      {skill.procedure.slice(0, 3).map((step, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-blue-500 font-medium">{i + 1}.</span>
                          <span className="line-clamp-1">{step}</span>
                        </li>
                      ))}
                      {skill.procedure.length > 3 && (
                        <li className="text-gray-400">+{skill.procedure.length - 3} more steps</li>
                      )}
                    </ol>
                  </div>
                )}

                {skill.trigger_conditions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {skill.trigger_conditions.slice(0, 2).map((condition, i) => (
                      <Badge key={i} variant="default" size="sm">{condition}</Badge>
                    ))}
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
