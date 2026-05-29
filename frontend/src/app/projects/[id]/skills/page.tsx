'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { skillsApi } from '@/lib/api';
import { Skill } from '@/lib/types';

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
    <Layout>
      <Header title="Skills" />

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : skills.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No skills found</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {skills.map((skill) => (
              <div
                key={skill.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">{skill.name}</h3>
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      skill.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : skill.status === 'candidate'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {skill.status}
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-4">
                  {skill.purpose || 'No description'}
                </p>
                <div className="text-sm text-gray-500 mb-4">
                  <span className="font-medium">Type:</span> {skill.skill_type}
                  <span className="mx-2">|</span>
                  <span className="font-medium">Version:</span> {skill.version}
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="font-medium">Used:</span> {skill.times_used} times
                  </div>
                  <div>
                    <span className="font-medium">Success:</span>{' '}
                    {skill.times_used > 0
                      ? Math.round((skill.successful_uses / skill.times_used) * 100)
                      : 0}
                    %
                  </div>
                </div>
                {skill.procedure.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      Procedure ({skill.procedure.length} steps)
                    </div>
                    <ol className="text-sm text-gray-600 list-decimal list-inside">
                      {skill.procedure.slice(0, 3).map((step, i) => (
                        <li key={i} className="truncate">
                          {step}
                        </li>
                      ))}
                      {skill.procedure.length > 3 && (
                        <li className="text-gray-400">
                          +{skill.procedure.length - 3} more steps
                        </li>
                      )}
                    </ol>
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
