'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { projectsApi, idleApi } from '@/lib/api';
import { Project } from '@/lib/types';
import { Save, Settings, Bell, Shield, Clock, Zap } from 'lucide-react';

export default function SettingsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

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
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save project:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Settings" />
        <div className="p-6 space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout projectId={projectId}>
        <Header title="Settings" />
      </Layout>
    );
  }

  return (
    <Layout projectId={projectId}>
      <Header
        title="Project Settings"
        subtitle="Configure your research project"
        actions={
          <Button onClick={handleSave} loading={saving}>
            <Save size={18} className="mr-2" />
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
        }
      />

      <div className="p-6 space-y-6 max-w-3xl">
        {/* General Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <Settings className="text-blue-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">General</h3>
                <p className="text-sm text-gray-500">Basic project information</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Project Name"
              value={project.name}
              onChange={(e) => setProject({ ...project, name: e.target.value })}
            />
            <Input
              label="Domain"
              value={project.domain}
              onChange={(e) => setProject({ ...project, domain: e.target.value })}
              helperText="The research domain for this project (e.g., machine learning, biology)"
            />
            <Textarea
              label="Description"
              value={project.description || ''}
              onChange={(e) => setProject({ ...project, description: e.target.value })}
              rows={3}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Flexibility ({project.default_flexibility.toFixed(1)})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={project.default_flexibility}
                onChange={(e) =>
                  setProject({ ...project, default_flexibility: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Strict (0)</span>
                <span>Flexible (1)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Idle Research Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                <Clock className="text-green-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Idle Research</h3>
                <p className="text-sm text-gray-500">Configure background research behavior</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <label className="font-medium text-gray-900">Enable Idle Research</label>
                <p className="text-sm text-gray-500">Automatically research during idle periods</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={project.idle_research_enabled}
                  onChange={(e) =>
                    setProject({ ...project, idle_research_enabled: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <Input
              label="Idle Trigger (minutes)"
              type="number"
              min="30"
              max="480"
              step="30"
              value={project.idle_trigger_minutes}
              onChange={(e) =>
                setProject({ ...project, idle_trigger_minutes: parseInt(e.target.value) })
              }
              helperText="How long to wait before starting idle research"
            />

            <Input
              label="Max Cycles Per Day"
              type="number"
              min="1"
              max="10"
              value={project.max_idle_cycles_per_day}
              onChange={(e) =>
                setProject({ ...project, max_idle_cycles_per_day: parseInt(e.target.value) })
              }
            />

            <Input
              label="Max Sources Per Cycle"
              type="number"
              min="10"
              max="200"
              value={project.max_sources_per_cycle}
              onChange={(e) =>
                setProject({ ...project, max_sources_per_cycle: parseInt(e.target.value) })
              }
            />

            <div className="pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={async () => {
                  try {
                    setSaving(true);
                    await idleApi.trigger(projectId);
                    alert('Idle cycle started!');
                  } catch (e) {
                    alert('Failed to start idle cycle. Check that an API key is configured.');
                  } finally {
                    setSaving(false);
                  }
                }}
                disabled={saving || !project.idle_research_enabled}
              >
                <Zap size={14} className="mr-1" />
                Run Idle Cycle Now
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Safety Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
                <Shield className="text-red-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Safety</h3>
                <p className="text-sm text-gray-500">Control what the system can do</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between py-2">
              <div>
                <label className="font-medium text-gray-900">Require Approval for External Actions</label>
                <p className="text-sm text-gray-500">Ask before making API calls or running code</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={project.approval_required_for_external_actions}
                  onChange={(e) =>
                    setProject({
                      ...project,
                      approval_required_for_external_actions: e.target.checked,
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
