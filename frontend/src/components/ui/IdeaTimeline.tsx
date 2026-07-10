'use client';

import { useState } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { Lightbulb, GitBranch, ArrowRight, RotateCcw, Archive, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';

interface TimelineEvent {
  date: string;
  type: 'created' | 'refined' | 'scored' | 'decision' | 'pivot' | 'archived';
  description: string;
  detail?: string;
  score?: number;
  decision?: string;
}

interface IdeaTimelineProps {
  idea: {
    id: string;
    initial_text: string;
    current_text: string;
    created_at: string;
    status: string;
    classification?: string;
    overall_score?: number;
  };
  events?: TimelineEvent[];
  className?: string;
}

const DECISION_ICONS: Record<string, React.ReactNode> = {
  promote: <CheckCircle2 size={14} className="text-success" />,
  continue: <ArrowRight size={14} className="text-primary" />,
  revise: <RotateCcw size={14} className="text-warning" />,
  pivot: <GitBranch size={14} className="text-tertiary" />,
  archive: <Archive size={14} className="text-muted-foreground" />,
  reject: <XCircle size={14} className="text-error" />,
};

const EVENT_COLORS: Record<string, string> = {
  created: 'border-success/30 bg-success/[0.03]',
  refined: 'border-primary/30 bg-primary/[0.03]',
  scored: 'border-amber/30 bg-amber/[0.03]',
  decision: 'border-tertiary/30 bg-tertiary/[0.03]',
  pivot: 'border-warning/30 bg-warning/[0.03]',
  archived: 'border-muted/30 bg-muted/[0.03]',
};

export function IdeaTimeline({ idea, events, className }: IdeaTimelineProps) {
  const [expanded, setExpanded] = useState(false);
  const defaultEvents: TimelineEvent[] = events || [
    { date: idea.created_at, type: 'created', description: 'Idea created', detail: idea.initial_text.slice(0, 200) },
  ];

  const visibleEvents = expanded ? defaultEvents : defaultEvents.slice(0, 5);

  return (
    <Card className={cn('p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Lightbulb size={18} className="text-primary" />
          <h3 className="font-bold text-sm">Idea Evolution</h3>
          <Badge variant={idea.status === 'active' ? 'success' : 'default'} className="text-[9px]">
            {idea.status}
          </Badge>
        </div>
        {idea.overall_score && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Score:</span>
            <span className={cn(
              'font-bold',
              (idea.overall_score || 0) >= 7 ? 'text-success' : (idea.overall_score || 0) >= 5 ? 'text-warning' : 'text-error'
            )}>
              {idea.overall_score?.toFixed(1)}
            </span>
          </div>
        )}
      </div>

      {/* Current state */}
      <div className="mb-6 p-4 bg-primary/[0.03] border border-primary/10 rounded-xl">
        <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50 mb-1">Current</div>
        <p className="text-sm font-medium leading-relaxed">{idea.current_text}</p>
      </div>

      {/* Timeline */}
      <div className="relative space-y-0">
        {visibleEvents.map((event, i) => (
          <div key={i} className="relative flex gap-4 pb-6 last:pb-0">
            {/* Timeline line */}
            {i < visibleEvents.length - 1 && (
              <div className="absolute left-[17px] top-8 bottom-0 w-px bg-border/30" />
            )}

            {/* Dot */}
            <div className="relative z-10 mt-1">
              <div className={cn(
                'w-[34px] h-[34px] rounded-full flex items-center justify-center border-2',
                EVENT_COLORS[event.type]?.split(' ')[0] || 'border-muted/30'
              )}>
                <div className={cn(
                  'w-[14px] h-[14px] rounded-full',
                  event.type === 'created' ? 'bg-success' :
                  event.type === 'refined' ? 'bg-primary' :
                  event.type === 'scored' ? 'bg-amber' :
                  event.type === 'decision' ? 'bg-tertiary' : 'bg-muted'
                )} />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-bold capitalize">{event.type}</span>
                <span className="text-[10px] text-muted-foreground/50">{formatDate(event.date)}</span>
                {event.decision && DECISION_ICONS[event.decision] && (
                  <span className="ml-auto flex items-center gap-1 text-[10px] text-muted-foreground">
                    {DECISION_ICONS[event.decision]}
                    {event.decision}
                  </span>
                )}
              </div>
              <p className="text-xs text-foreground/70">{event.description}</p>
              {event.detail && (
                <p className="text-xs text-muted-foreground/50 mt-1 line-clamp-2">{event.detail}</p>
              )}
              {event.score && (
                <div className="mt-1 flex items-center gap-1">
                  <div className="h-1.5 w-16 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${(event.score / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-muted-foreground">{event.score.toFixed(1)}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {defaultEvents.length > 5 && (
        <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} className="w-full mt-2">
          {expanded ? 'Show less' : `Show ${defaultEvents.length - 5} more events`}
        </Button>
      )}
    </Card>
  );
}
