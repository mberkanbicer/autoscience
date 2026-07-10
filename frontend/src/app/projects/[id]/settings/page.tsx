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
import { Project, DomainPack } from '@/lib/types';
import { Save, Settings, Shield, Clock, Zap, FlaskConical } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

export default function SettingsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [domainPacks, setDomainPacks] = useState<DomainPack[]>([]);
  const [applyingPack, setApplyingPack] = useState<string | null>(null);

  useEffect(() => {
    loadProject();
    projectsApi.domainPacks().then(setDomainPacks).catch(console.error);
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
      await projectsApi.update(projectId, project as any);
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
        <Card className="glass overflow-hidden border-border/10">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center shadow-inner">
                <Settings className="text-primary" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">General Parameters</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Basic Intellectual Framework</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="Project Designation"
              value={project.name}
              onChange={(e) => setProject({ ...project, name: e.target.value })}
            />
            <Input
              label="Scientific Domain"
              value={project.domain}
              onChange={(e) => setProject({ ...project, domain: e.target.value })}
              helperText="The primary research vector for this laboratory instance."
            />
            <Textarea
              label="Research Abstract"
              value={project.description || ''}
              onChange={(e) => setProject({ ...project, description: e.target.value })}
              rows={3}
            />
            <div className="pt-2">
              <label className="block text-sm font-bold text-foreground/80 mb-4 ml-1 uppercase tracking-wider">
                Cognitive Flexibility ({project.default_flexibility.toFixed(1)})
              </label>
              <div className="px-2">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={project.default_flexibility}
                  onChange={(e) =>
                    setProject({ ...project, default_flexibility: parseFloat(e.target.value) })
                  }
                  className="w-full h-2 bg-muted rounded-full appearance-none cursor-pointer accent-primary transition-all duration-300 hover:scale-[1.01]"
                />
                <div className="flex justify-between mt-3 px-1 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">
                  <span>Strict Logic</span>
                  <span>Creative Drift</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass overflow-hidden border-border/10">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center shadow-inner">
                <FlaskConical className="text-primary" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Domain Pack</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">
                  Physics · Biology · Chemistry presets
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 p-8">
            {domainPacks.map((pack) => (
              <div
                key={pack.id}
                className="p-4 rounded-xl border border-border/10 bg-white/40 space-y-3"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-bold">{pack.name}</p>
                    <p className="text-sm text-muted-foreground mt-1">{pack.description}</p>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={applyingPack === pack.id}
                    onClick={async () => {
                      setApplyingPack(pack.id);
                      try {
                        const updated = await projectsApi.applyDomainPack(projectId, pack.id);
                        setProject(updated);
                        setSaved(true);
                        setTimeout(() => setSaved(false), 2000);
                      } catch (error) {
                        console.error('Failed to apply domain pack:', error);
                      } finally {
                        setApplyingPack(null);
                      }
                    }}
                  >
                    {applyingPack === pack.id ? 'Applying...' : 'Apply'}
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {pack.validation_methods.slice(0, 3).map((method) => (
                    <Badge key={method} variant="info">
                      {method}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Idle Research Settings */}
        <Card className="glass overflow-hidden border-border/10">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-success/10 rounded-xl flex items-center justify-center shadow-inner">
                <Clock className="text-success" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Autonomous Cognition</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Background Laboratory Cycles</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <div className="flex items-center justify-between p-4 bg-white/40 rounded-xl border border-border/5">
              <div>
                <label className="font-bold text-foreground tracking-tight">Enable Idle Research</label>
                <p className="text-xs font-medium text-muted-foreground mt-0.5">Automatically trigger research cycles during laboratory inactivity.</p>
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
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border/40 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-success shadow-inner"></div>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Input
                label="Inactivity Threshold"
                type="number"
                min="30"
                max="480"
                step="30"
                value={project.idle_trigger_minutes}
                onChange={(e) =>
                  setProject({ ...project, idle_trigger_minutes: parseInt(e.target.value) })
                }
                helperText="Wait time (min) before autonomous start."
              />

              <Input
                label="Daily Cycle Cap"
                type="number"
                min="1"
                max="10"
                value={project.max_idle_cycles_per_day}
                onChange={(e) =>
                  setProject({ ...project, max_idle_cycles_per_day: parseInt(e.target.value) })
                }
                helperText="Maximum cycles in 24h."
              />

              <Input
                label="Intellectual Depth"
                type="number"
                min="10"
                max="200"
                value={project.max_sources_per_cycle}
                onChange={(e) =>
                  setProject({ ...project, max_sources_per_cycle: parseInt(e.target.value) })
                }
                helperText="Papers per autonomous run."
              />
            </div>

            <div className="pt-4 border-t border-border/5">
              <Button
                variant="secondary"
                size="sm"
                className="px-6 py-2 rounded-xl text-[10px] uppercase font-bold tracking-[0.2em] shadow-lg shadow-primary/5"
                onClick={async () => {
                  try {
                    setSaving(true);
                    await idleApi.trigger(projectId);
                    alert('Idle cycle initialized!');
                  } catch (e) {
                    alert('Initialization failed. Verify API credentials.');
                  } finally {
                    setSaving(false);
                  }
                }}
                disabled={saving || !project.idle_research_enabled}
              >
                <Zap size={14} className="mr-2 text-primary" />
                Initialize Manual Cycle
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Safety Settings */}
        <Card className="glass overflow-hidden border-border/10">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-error/10 rounded-xl flex items-center justify-center shadow-inner">
                <Shield className="text-error" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Security & Oversight</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Control Human-in-the-Loop</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-8">
            <div className="flex items-center justify-between p-4 bg-white/40 rounded-xl border border-border/5">
              <div>
                <label className="font-bold text-foreground tracking-tight">Strict Action Approval</label>
                <p className="text-xs font-medium text-muted-foreground mt-0.5">Require manual validation before committing external state or costs.</p>
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
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border/40 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary shadow-inner"></div>
              </label>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
