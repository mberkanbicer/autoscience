'use client';

import { useMemo } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { Brain, TrendingUp, TrendingDown, Award, BarChart3, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SkillMetrics {
  id: string;
  name: string;
  type: string;
  times_used: number;
  successful_uses: number;
  success_rate: number;
  avg_score_improvement?: number;
  status: string;
}

interface SkillRateProps {
  skills: SkillMetrics[];
  className?: string;
  onRetire?: (skillId: string) => void;
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-success/10 text-success border-success/20',
  candidate: 'bg-info/10 text-info border-info/20',
  tested: 'bg-warning/10 text-warning border-warning/20',
  deprecated: 'bg-muted/30 text-muted-foreground border-muted/40',
  retired: 'bg-error/10 text-error border-error/20',
};

export function SkillRate({ skills, className, onRetire }: SkillRateProps) {
  const totalSkills = skills.length;
  const activeSkills = skills.filter(s => s.status === 'active').length;
  const successRate = useMemo(() => {
    const totalUses = skills.reduce((sum, s) => sum + s.times_used, 0);
    const totalSuccesses = skills.reduce((sum, s) => sum + s.successful_uses, 0);
    return totalUses > 0 ? Math.round((totalSuccesses / totalUses) * 100) : 0;
  }, [skills]);

  const topSkills = useMemo(() =>
    [...skills].sort((a, b) => (b.success_rate || 0) - (a.success_rate || 0)).slice(0, 5),
    [skills]
  );

  if (skills.length === 0) {
    return (
      <Card className={cn('p-8 text-center', className)}>
        <Brain size={24} className="text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground/50">No skills developed yet</p>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Brain size={18} className="text-primary" />
          <h3 className="font-bold text-sm">Skill Utilization</h3>
        </div>
        <Badge variant="info" className="text-[9px]">
          {activeSkills}/{totalSkills} active
        </Badge>
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-3 bg-stone-50 dark:bg-stone-900 rounded-xl">
          <div className="text-2xl font-black">{totalSkills}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Total Skills</div>
        </div>
        <div className="text-center p-3 bg-success/[0.05] rounded-xl">
          <div className="text-2xl font-black text-success">{successRate}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Success Rate</div>
        </div>
        <div className="text-center p-3 bg-stone-50 dark:bg-stone-900 rounded-xl">
          <div className="text-2xl font-black">{skills.reduce((s, sk) => s + sk.times_used, 0)}</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Total Uses</div>
        </div>
      </div>

      {/* Top skills */}
      <div className="space-y-2">
        <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-2">Top Performing Skills</div>
        {topSkills.map((skill) => (
          <div key={skill.id} className="flex items-center gap-3 p-3 bg-stone-50 dark:bg-stone-900 rounded-xl">
            <Award size={16} className={cn(
              skill.success_rate >= 80 ? 'text-success' :
              skill.success_rate >= 60 ? 'text-primary' : 'text-muted-foreground'
            )} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs truncate">{skill.name}</span>
                <Badge variant="default" className={cn('text-[8px]', STATUS_COLORS[skill.status] || '')}>
                  {skill.status}
                </Badge>
              </div>
              <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground/50">
                <span>Uses: {skill.times_used}</span>
                <span>Success: {skill.successful_uses}</span>
                {skill.avg_score_improvement && (
                  <span className="flex items-center gap-0.5">
                    <TrendingUp size={10} />
                    +{skill.avg_score_improvement.toFixed(1)}
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className={cn(
                'text-sm font-black',
                skill.success_rate >= 80 ? 'text-success' :
                skill.success_rate >= 60 ? 'text-primary' : 'text-muted-foreground'
              )}>
                {skill.success_rate}%
              </div>
            </div>
            {/* Success rate bar */}
            <div className="w-16 h-1.5 bg-stone-200 dark:bg-stone-700 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full',
                  skill.success_rate >= 80 ? 'bg-success' :
                  skill.success_rate >= 60 ? 'bg-primary' : 'bg-muted'
                )}
                style={{ width: `${skill.success_rate}%` }}
              />
            </div>
            {onRetire && skill.status === 'active' && skill.success_rate < 50 && (
              <Button variant="ghost" size="sm" onClick={() => onRetire(skill.id)} className="text-error">
                <RefreshCw size={12} />
              </Button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
