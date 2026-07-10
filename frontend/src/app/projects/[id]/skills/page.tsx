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
import { SkillPerformancePanel } from '@/components/ui/SkillPerformancePanel';
import { SkillPerformanceChart } from '@/components/ui/SkillPerformanceChart';
import { SkillEvalSettings } from '@/components/ui/SkillEvalSettings';
import { SkillEvalHistory } from '@/components/ui/SkillEvalHistory';
import { useSkillEvalStream } from '@/hooks/use-skill-eval-stream';
import { GraduationCap, Zap, TrendingUp, BarChart, Trash2, Pause } from 'lucide-react';

export default function SkillsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Connect to real-time skill evaluation event stream
  useSkillEvalStream();

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

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this skill?')) return;
    setDeletingId(id);
    try {
      await skillsApi.delete(id);
      setSkills(skills.filter(s => s.id !== id));
    } catch (error) {
      console.error('Failed to delete skill:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const handleRetire = async (id: string) => {
    if (!window.confirm('Retire this skill?')) return;
    try {
      await skillsApi.retire(id);
      loadSkills();
    } catch (error) {
      console.error('Failed to retire skill:', error);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Skills"
        subtitle={`${skills.length} skills learned`}
      />

      <div className="p-6 space-y-8">
        {/* Skill Performance Panel */}
        <SkillPerformancePanel
          projectId={projectId}
          onEvaluationComplete={loadSkills}
        />

        {/* Scheduler Settings */}
        <SkillEvalSettings />

        {/* Evaluation History */}
        <SkillEvalHistory />

        {/* Performance Trend Chart */}
        <SkillPerformanceChart
          projectId={projectId}
        />

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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {skills.map((skill) => (
              <Card key={skill.id} hover className="group transition-all duration-500 hover:scale-[1.02] relative overflow-hidden">
                <div className="p-8">
                  <div className="flex items-start justify-between mb-8">
                    <div className="w-14 h-14 bg-warning/10 rounded-2xl flex items-center justify-center shadow-inner group-hover:bg-warning/20 transition-all duration-500 group-hover:rotate-6">
                      <GraduationCap className="text-warning" size={28} />
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <StatusBadge status={skill.status} />
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0">
                        <button
                          onClick={() => handleRetire(skill.id)}
                          className="p-2 rounded-lg hover:bg-warning/10 text-warning transition-all duration-300 hover:scale-110"
                          title="Retire Skill"
                        >
                          <Pause size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(skill.id)}
                          disabled={deletingId === skill.id}
                          className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300 hover:scale-110 disabled:opacity-30"
                          title="Purge Skill"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>

                  <h3 className="text-xl font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">{skill.name}</h3>
                  {skill.purpose && (
                    <p className="text-sm text-muted-foreground font-medium line-clamp-2 mb-6 leading-relaxed italic">{skill.purpose}</p>
                  )}

                  <div className="space-y-3 mb-8 bg-muted/20 p-4 rounded-xl border border-border/5 shadow-inner">
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
                      <span className="text-muted-foreground/40">Classification</span>
                      <Badge variant="info" className="bg-primary/5 px-2 py-0">{skill.skill_type}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
                      <span className="text-muted-foreground/40">Calibration</span>
                      <span className="text-foreground/60">Version {skill.version}.0</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
                      <span className="text-muted-foreground/40">Utilization</span>
                      <div className="flex items-center gap-1.5 text-foreground/60">
                        <Zap size={12} className="text-warning animate-pulse" />
                        {skill.times_used} cycles
                      </div>
                    </div>
                    {skill.times_used > 0 && (
                      <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest">
                        <span className="text-muted-foreground/40">Reliability Index</span>
                        <div className="flex items-center gap-1.5 text-success">
                          <BarChart size={12} />
                          {Math.round((skill.successful_uses / skill.times_used) * 100)}%
                        </div>
                      </div>
                    )}
                  </div>

                  {skill.procedure.length > 0 && (
                    <div className="border-t border-border/10 pt-6">
                      <span className="text-[9px] font-bold text-muted-foreground/30 uppercase tracking-[0.2em] mb-4 block">Operational Protocol</span>
                      <ol className="text-xs text-foreground/70 space-y-3 font-medium">
                        {skill.procedure.slice(0, 3).map((step, i) => (
                          <li key={i} className="flex items-start gap-3 group/step">
                            <span className="text-primary/40 font-mono text-[10px] mt-0.5 group-hover/step:text-primary transition-colors">{i + 1}.0</span>
                            <span className="line-clamp-1">{step}</span>
                          </li>
                        ))}
                        {skill.procedure.length > 3 && (
                          <li className="text-muted-foreground/40 italic pl-8">+{skill.procedure.length - 3} additional procedural steps</li>
                        )}
                      </ol>
                    </div>
                  )}

                  {skill.trigger_conditions.length > 0 && (
                    <div className="mt-6 flex flex-wrap gap-2">
                      {skill.trigger_conditions.slice(0, 2).map((condition, i) => (
                        <Badge key={i} variant="default" size="sm" className="bg-muted text-[9px] font-bold uppercase tracking-widest px-2 py-0 opacity-60">
                           IF_{condition.toUpperCase()}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
