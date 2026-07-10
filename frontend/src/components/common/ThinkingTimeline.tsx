'use client';

import React, { useEffect, useState, useRef } from 'react';
import { 
  Brain, 
  Search, 
  FileText, 
  CheckCircle2, 
  Loader2,
  Sparkles,
  AlertCircle,
  Clock,
  Zap,
  Network,
  FlaskConical,
  MessageSquare,
  ShieldAlert
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ThinkingEvent {
  type: string;
  timestamp: string;
  data: Record<string, any>;
}

interface ThinkingTimelineProps {
  events: ThinkingEvent[];
  isComplete: boolean;
}

const eventIcons: Record<string, any> = {
  connected: Sparkles,
  keywords: Zap,
  search_started: Search,
  search_results: FileText,
  paper_found: FileText,
  search_complete: CheckCircle2,
  run_completed: CheckCircle2,
  run_failed: ShieldAlert,
  step_started: Brain,
  step_completed: CheckCircle2,
  thinking: Brain,
  cognitive_update: Brain,
  approval_required: ShieldAlert,
  papers_clustered: Network,
  tool_call: FlaskConical,
  paper_clustered: Network,
  conflict_detected: ShieldAlert,
  hypothesis_formed: FlaskConical,
  question_generated: MessageSquare,
};

const getEventIcon = (type: string) => {
  return eventIcons[type] || MessageSquare;
};

const getEventColor = (type: string) => {
  switch (type) {
    case 'keywords': return 'text-warning bg-warning/10';
    case 'search_started': return 'text-primary bg-primary/10';
    case 'paper_found': return 'text-primary bg-primary/10';
    case 'run_completed': return 'text-success bg-success/10';
    case 'run_failed': return 'text-error bg-error/10';
    case 'step_started': return 'text-tertiary bg-tertiary/10';
    case 'thinking': return 'text-primary bg-primary/10';
    case 'conflict_detected': return 'text-error bg-error/10';
    default: return 'text-muted-foreground bg-muted/10';
  }
};

const getEventTitle = (event: ThinkingEvent) => {
  const { type, data } = event;
  switch (type) {
    case 'connected': return 'System Connected';
    case 'keywords': return 'Synthesizing Search Vectors';
    case 'search_started': return 'Initiating Global Search';
    case 'search_results': return 'Search Payload Received';
    case 'paper_found': return 'Corpus Node Identified';
    case 'search_complete': return 'Search Protocol Finalized';
    case 'run_completed': return 'Research Cycle Complete';
    case 'run_failed': return 'Protocol Failure';
    case 'step_started': return data.label || 'Executing Cognitive Step';
    case 'step_completed': return `${data.phase_label || data.step} Complete`;
    case 'thinking': return 'Internal Reasoning';
    case 'cognitive_update': return 'Cognitive Metrics Updated';
    case 'approval_required': return 'Approval Gate';
    case 'papers_clustered': return 'Topological Clustering';
    case 'paper_clustered': return 'Topological Clustering';
    case 'conflict_detected': return 'Cognitive Dissonance Identified';
    case 'hypothesis_formed': return 'Hypothesis Synthesis';
    case 'question_generated': return 'Research Inquiry Forged';
    default: return type.replace(/_/g, ' ').toUpperCase();
  }
};

export function ThinkingTimeline({ events, isComplete }: ThinkingTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current && !isComplete) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, isComplete]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-1.5 bg-primary/10 rounded-lg">
          <Clock size={14} className="text-primary" />
        </div>
        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">Temporal Log</span>
      </div>

      <div className="space-y-3 relative">
        {/* Timeline Line */}
        <div className="absolute left-[19px] top-4 bottom-4 w-px bg-border/20 z-0" />

        {events.map((event, index) => (
          <TimelineItem 
            key={index} 
            event={event} 
            index={index} 
            isLast={index === events.length - 1} 
            isLive={!isComplete} 
          />
        ))}
        <div ref={scrollRef} />
      </div>
    </div>
  );
}

function TimelineItem({ event, index, isLast, isLive }: { event: ThinkingEvent, index: number, isLast: boolean, isLive: boolean }) {
  const Icon = getEventIcon(event.type);
  const colorClass = getEventColor(event.type);
  const title = getEventTitle(event);
  
  // Staggered animation
  const [isVisible, setIsVisible] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={cn(
      "relative flex items-start gap-4 transition-all duration-700 ease-out z-10",
      isVisible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4"
    )}>
      <div className={cn(
        "p-2 rounded-full border border-border/5 shadow-sm backdrop-blur-md",
        colorClass
      )}>
        <Icon size={14} className={cn(isLast && isLive && event.type !== 'run_completed' ? "animate-pulse" : "")} />
      </div>

      <div className="flex-1 pt-1">
        <div className="flex items-center gap-2">
          <h4 className="text-[11px] font-black text-foreground tracking-tight uppercase">
            {title}
          </h4>
          {isLast && isLive && event.type !== 'run_completed' && event.type !== 'run_failed' && (
            <Loader2 size={10} className="animate-spin text-primary" />
          )}
          <span className="text-[9px] font-medium text-muted-foreground/40 ml-auto">
            {new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </div>

        <div className="mt-1">
          {renderEventData(event)}
        </div>
      </div>
    </div>
  );
}

function renderEventData(event: ThinkingEvent) {
  const { type, data } = event;

  switch (type) {
    case 'keywords':
      return (
        <div className="flex flex-wrap gap-1.5 mt-1">
          {data.keywords?.slice(0, 8).map((kw: string, i: number) => (
            <span key={i} className="text-[8px] font-bold text-muted-foreground/60 bg-muted/5 px-2 py-0.5 rounded-full border border-border/5">
              {kw}
            </span>
          ))}
          {data.keywords?.length > 8 && (
             <span className="text-[8px] font-bold text-muted-foreground/30 px-1">+ {data.keywords.length - 8} more</span>
          )}
        </div>
      );
    case 'search_started':
      return (
        <p className="text-[10px] text-muted-foreground/70 italic">
           Querying {data.sources?.join(', ')} for &ldquo;{data.query}&rdquo;
        </p>
      );
    case 'paper_found':
      return (
        <p className="text-[10px] font-bold text-foreground/80 line-clamp-1">
          {data.title}
        </p>
      );
    case 'search_results':
      return (
        <p className="text-[10px] text-muted-foreground/70">
          Synthesized {data.papers_count} nodes from {data.total_found} global results.
        </p>
      );
    case 'step_started':
      return (
        <p className="text-[10px] text-muted-foreground/50 uppercase tracking-widest font-black">
          Executing Protocol {data.step}
        </p>
      );
    case 'step_completed':
      return (
        <p className="text-[10px] text-success/70 font-bold">
          Step verified in {data.duration}s
        </p>
      );
    case 'thinking':
      return (
        <p className="text-[10px] text-muted-foreground/70 italic whitespace-pre-wrap border-l-2 border-primary/20 pl-3 py-1">
          {data.thought}
        </p>
      );
    case 'cognitive_update':
    case 'papers_clustered':
      return (
        <p className="text-[10px] text-muted-foreground/70">
          Entropy {Math.round((data.entropy ?? 0) * 100)}% · Mode {data.mode || 'unknown'}
          {data.clusters ? ` · ${data.clusters} clusters` : ''}
        </p>
      );
    case 'approval_required':
      return (
        <p className="text-[10px] text-warning/80 font-bold">
          {data.message || `Paused at ${data.step}`}
        </p>
      );
    case 'run_failed':
      return (
        <p className="text-[10px] text-error/80 font-bold">
          Error: {data.error}
        </p>
      );
    default:
      return null;
  }
}
