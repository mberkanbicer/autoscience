'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { projectsApi } from '@/lib/api';
import { Project } from '@/lib/types';

export default function SettingsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const data = await projectsApi.get(projectId);
      setProject(data);
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!project) return;
    setSaving(true);
    try {
      await projectsApi.update(projectId, project);
    } catch (error) {
      console.error('Failed to save project:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-6 text-center">Loading...</div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout>
        <div className="p-6 text-center">Project not found</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <Header
        title="Project Settings"
        actions={
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        }
      />

      <div className="p-6">
        <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Name
              </label>
              <input
                type="text"
                value={project.name}
                onChange={(e) => setProject({ ...project, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Domain
              </label>
              <input
                type="text"
                value={project.domain}
                onChange={(e) => setProject({ ...project, domain: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={project.description || ''}
                onChange={(e) =>
                  setProject({ ...project, description: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Flexibility ({project.default_flexibility})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={project.default_flexibility}
                onChange={(e) =>
                  setProject({
                    ...project,
                    default_flexibility: parseFloat(e.target.value),
                  })
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Strict (0)</span>
                <span>Flexible (1)</span>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-lg font-medium mb-4">Idle Research Settings</h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    Enable Idle Research
                  </label>
                  <input
                    type="checkbox"
                    checked={project.idle_research_enabled}
                    onChange={(e) =>
                      setProject({
                        ...project,
                        idle_research_enabled: e.target.checked,
                      })
                    }
                    className="h-4 w-4 text-blue-600 rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Idle Trigger (minutes): {project.idle_trigger_minutes}
                  </label>
                  <input
                    type="range"
                    min="30"
                    max="480"
                    step="30"
                    value={project.idle_trigger_minutes}
                    onChange={(e) =>
                      setProject({
                        ...project,
                        idle_trigger_minutes: parseInt(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Idle Cycles Per Day
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={project.max_idle_cycles_per_day}
                    onChange={(e) =>
                      setProject({
                        ...project,
                        max_idle_cycles_per_day: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Sources Per Cycle
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="200"
                    value={project.max_sources_per_cycle}
                    onChange={(e) =>
                      setProject({
                        ...project,
                        max_sources_per_cycle: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-lg font-medium mb-4">Safety Settings</h3>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Require Approval for External Actions
                </label>
                <input
                  type="checkbox"
                  checked={project.approval_required_for_external_actions}
                  onChange={(e) =>
                    setProject({
                      ...project,
                      approval_required_for_external_actions: e.target.checked,
                    })
                  }
                  className="h-4 w-4 text-blue-600 rounded"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
