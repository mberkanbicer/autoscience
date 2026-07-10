'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { CognitiveEntropy } from '@/components/ui/CognitiveEntropy';
import { FocusMetric } from '@/components/ui/FocusMetric';
import { IdeaTimeline } from '@/components/ui/IdeaTimeline';
import { NoveltyDistribution } from '@/components/ui/NoveltyDistribution';
import { ConflictDensity } from '@/components/ui/ConflictDensity';
import { ConflictHeatmap } from '@/components/ui/ConflictHeatmap';
import type { ConflictHeatmapEntry } from '@/components/ui/ConflictHeatmap';
import { SkillRate } from '@/components/ui/SkillRate';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { SystemHealth } from '@/components/ui/SystemHealth';
import { projectsApi, papersApi, ideasApi, skillsApi } from '@/lib/api';
import { Project, ProjectStats, Idea, Skill } from '@/lib/types';
import { Brain, BarChart3, GitBranch, Award, TrendingUp, Lightbulb, Activity, RefreshCw, ArrowRight, Server } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function HealthDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<ConflictHeatmapEntry[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, [projectId]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [projData, statsData, ideasData, skillsData, conflictsData, clustersData] = await Promise.all([
        projectsApi.get(projectId),
        projectsApi.stats(projectId),
        ideasApi.list(projectId, { limit: '5' }).catch(() => []),
        skillsApi.list({ project_id: projectId }).catch(() => []),
        papersApi.conflicts(projectId).catch(() => []),
        papersApi.clusters(projectId).catch(() => []),
      ]);

      setProject(projData);
      setStats(statsData);
      setIdeas(ideasData as unknown as Idea[]);
      setSkills(skillsData as unknown as Skill[]);
      setConflicts(conflictsData);
      setClusters(clustersData);

      // Build heatmap data from conflicts
      const heatmap: ConflictHeatmapEntry[] = [];
      const clusterMap = new Map<string, string>();
      clustersData.forEach((c: any) => clusterMap.set(c.id, c.name || c.id));

      conflictsData.forEach((conflict: any) => {
        const clusterName = conflict.cluster_id ? (clusterMap.get(conflict.cluster_id) || conflict.cluster_id) : 'Unassigned';
        const key = `${clusterName}::${conflict.conflict_type}`;
        const existing = heatmap.find((h) => h.cluster_name === clusterName && h.conflict_type === conflict.conflict_type);
        if (existing) {
          existing.count += 1;
          existing.max_severity = Math.max(existing.max_severity, conflict.severity || 0);
          existing.avg_severity = (existing.avg_severity * (existing.count - 1) + (conflict.severity || 0)) / existing.count;
        } else {
          heatmap.push({
            cluster_name: clusterName,
            cluster_id: conflict.cluster_id || 'unassigned',
            conflict_type: conflict.conflict_type || 'unknown',
            count: 1,
            max_severity: conflict.severity || 0,
            avg_severity: conflict.severity || 0,
          });
        }
      });
      setHeatmapData(heatmap);
    } catch (err) {
      console.error('Failed to load health dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Cognitive Health Dashboard" subtitle="Loading diagnostics..." />
        <div className="p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonCard key={i} />)}
        </div>
      </Layout>
    );
  }

  const conflictByType = conflicts.reduce<Record<string, number>>((acc, c: any) => {
    const t = c.conflict_type || 'unknown';
    acc[t] = (acc[t] || 0) + 1;
    return acc;
  }, {});

  const avgSeverity = conflicts.length > 0
    ? conflicts.reduce((s: number, c: any) => s + (c.severity || 0), 0) / conflicts.length
    : 0;

  const hasScoreData = ideas.length > 0 && ideas.some((i: any) => i.overall_score !== undefined);

  return (
    <Layout projectId={projectId}>
      <Header
        title="Cognitive Health Dashboard"
        subtitle={`Real-time diagnostics for ${project?.name || 'project'}`}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={loadDashboard}>
              <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              Refresh
            </Button>              <Button
                  variant="primary"
                  size="sm"
                  className="rounded-xl px-5 py-4 text-[9px] font-black uppercase tracking-widest"
                  onClick={() => router.push(`/projects/${projectId}`)}
                >
                  <Activity className="h-3.5 w-3.5 mr-1.5" />
                  Project Overview
                </Button>
          </div>
        }
      />

      <div className="p-8 space-y-10 animate-in fade-in duration-700">
        {/* Cognitive Entropy Bar */}
        <div className="p-6 glass border border-border/5 rounded-2xl space-y-6">
          <CognitiveEntropy
            entropy={stats?.latest_cognitive_entropy || 0.5}
            mode={(stats?.latest_cognitive_mode as any) || 'balanced'}
            size="md"
          />
          <div className="w-full h-px bg-border/5" />
          <FocusMetric
            focusScore={stats?.latest_focus_score ?? (stats?.latest_cognitive_entropy != null ? 1 - stats.latest_cognitive_entropy : 0.5)}
            focusLabel={(stats?.latest_focus_label as any) || undefined}
            size="md"
          />
        </div>

        <Tabs defaultValue="overview" className="space-y-8">
          <TabsList className="p-1 bg-stone-100 dark:bg-stone-900 rounded-[1.2rem] border border-border/5 flex-wrap">
            <TabsTrigger value="overview" className="rounded-xl px-6 py-2.5 text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
              <Brain size={14} /> Overview
            </TabsTrigger>
            <TabsTrigger value="system" className="rounded-xl px-6 py-2.5 text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
              <Server size={14} /> System
            </TabsTrigger>
            <TabsTrigger value="conflicts" className="rounded-xl px-6 py-2.5 text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
              <GitBranch size={14} /> Conflicts
            </TabsTrigger>
            <TabsTrigger value="ideas" className="rounded-xl px-6 py-2.5 text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
              <Lightbulb size={14} /> Ideas
            </TabsTrigger>
            <TabsTrigger value="skills" className="rounded-xl px-6 py-2.5 text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5">
              <Award size={14} /> Skills
            </TabsTrigger>
          </TabsList>

          {/* System Health Tab */}
          <TabsContent value="system" className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <SystemHealth pollInterval={30000} />
          </TabsContent>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Quick stats row */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
              {[
                { label: 'Ideas', value: stats?.total_ideas || 0, icon: Lightbulb, color: 'text-primary bg-primary/10' },
                { label: 'Papers', value: stats?.total_papers || 0, icon: BarChart3, color: 'text-info bg-info/10' },
                { label: 'Conflicts', value: stats?.total_conflicts || 0, icon: GitBranch, color: 'text-error bg-error/10' },
                { label: 'Hypotheses', value: stats?.total_hypotheses || 0, icon: TrendingUp, color: 'text-tertiary bg-tertiary/10' },
                { label: 'Skills', value: stats?.total_skills || 0, icon: Award, color: 'text-success bg-success/10' },
              ].map((stat) => {
                const Icon = stat.icon;
                return (
                  <Card key={stat.label} className="p-5 bg-white/40 dark:bg-stone-900/40 border-border/5">
                    <div className="flex items-center gap-3">
                      <div className={cn('p-2.5 rounded-xl', stat.color)}>
                        <Icon size={18} />
                      </div>
                      <div>
                        <div className="text-2xl font-black">{stat.value}</div>
                        <div className="text-[9px] font-bold text-muted-foreground/60 uppercase tracking-wider">{stat.label}</div>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Conflict Density */}
              <ConflictDensity
                data={{
                  total: stats?.total_conflicts || 0,
                  by_type: conflictByType,
                  severity_avg: avgSeverity * 10,
                }}
              />

              {/* Novelty Distribution (from latest idea) */}
              {hasScoreData ? (
                <NoveltyDistribution
                  scores={ideas.map((i: any) => ({
                    dimension: 'overall',
                    score: i.overall_score || 5,
                    weight: 1,
                    is_risk: false,
                  }))}
                  overallValue={Math.max(...ideas.map((i: any) => i.overall_score || 0))}
                  classification={ideas[0]?.classification}
                />
              ) : (
                <Card className="p-10 text-center border-border/5">
                  <BarChart3 size={32} className="mx-auto mb-4 text-muted-foreground/20" />
                  <h3 className="text-sm font-bold text-muted-foreground mb-2">No Scoring Data</h3>
                  <p className="text-xs text-muted-foreground/50">Score ideas to see novelty distribution.</p>
                  <Button variant="secondary" size="sm" className="mt-4" onClick={() => router.push(`/projects/${projectId}/ideas`)}>
                    <Lightbulb className="h-3.5 w-3.5 mr-1.5" /> View Ideas
                  </Button>
                </Card>
              )}
            </div>

            {/* Idea Timeline */}
            {ideas.length > 0 && (
              <IdeaTimeline
                idea={ideas[0] as any}
              />
            )}
          </TabsContent>

          {/* Conflicts Tab */}
          <TabsContent value="conflicts" className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <ConflictHeatmap data={heatmapData} />

            {/* Quick link to clusters */}
            <div className="flex justify-center">
              <Button variant="ghost" size="sm" onClick={() => router.push(`/projects/${projectId}/clusters`)}>
                View all clusters <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            </div>
          </TabsContent>

          {/* Ideas Tab */}
          <TabsContent value="ideas" className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {ideas.length > 0 ? (
                ideas.slice(0, 4).map((idea: any) => (
                  <IdeaTimeline key={idea.id} idea={idea} />
                ))
              ) : (
                <div className="lg:col-span-2 py-20 text-center glass border-2 border-dashed border-border/10 rounded-[2.5rem]">
                  <Lightbulb size={48} className="mx-auto mb-6 text-muted-foreground/20" />
                  <h3 className="text-xl font-black text-foreground mb-3 tracking-tight uppercase">No Ideas Yet</h3>
                  <p className="text-muted-foreground font-medium text-sm">Start a research run to generate ideas.</p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Skills Tab */}
          <TabsContent value="skills" className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <SkillRate
              skills={skills.map((s: any) => ({
                id: s.id,
                name: s.name,
                type: s.skill_type || 'general',
                times_used: s.times_used || 0,
                successful_uses: s.successful_uses || 0,
                success_rate: (s.times_used || 0) > 0 ? Math.round(((s.successful_uses || 0) / (s.times_used || 1)) * 100) : 0,
                avg_score_improvement: s.average_score_improvement || undefined,
                status: s.status || 'active',
              }))}
            />
          </TabsContent>
        </Tabs>

        {/* Cross-mode navigation footer */}
        <div className="flex items-center justify-center gap-6 pt-8 border-t border-border/10">
          <Button variant="ghost" size="sm" onClick={() => router.push(`/projects/${projectId}/ideas`)}>
            <Lightbulb className="h-3.5 w-3.5 mr-1.5" /> Ideas
          </Button>
          <Button variant="ghost" size="sm" onClick={() => router.push(`/projects/${projectId}/runs`)}>
            <Activity className="h-3.5 w-3.5 mr-1.5" /> Research Runs
          </Button>
          <Button variant="ghost" size="sm" onClick={() => router.push(`/projects/${projectId}/datasets`)}>
            <BarChart3 className="h-3.5 w-3.5 mr-1.5" /> Datasets
          </Button>
          <Button variant="ghost" size="sm" onClick={() => router.push(`/projects/${projectId}/manuscripts`)}>
            <Award className="h-3.5 w-3.5 mr-1.5" /> Manuscripts
          </Button>
        </div>
      </div>
    </Layout>
  );
}
