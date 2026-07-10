'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Search, FileText, CheckCircle, AlertCircle, Loader2, Zap, Network, ArrowRight, ListTree } from 'lucide-react';
import { ThinkingTree } from '@/components/ui/ThinkingTree';
import { ThinkingTimeline } from '@/components/common/ThinkingTimeline';
import { CognitiveEntropy } from '@/components/ui/CognitiveEntropy';
import { cn } from '@/lib/utils';

interface SearchEvent {
  type: string;
  timestamp: string;
  data: Record<string, any>;
}

interface LivePreviewProps {
  runId: string | null;
  isActive: boolean;
  onComplete?: () => void;
}

export function LivePreview({ runId, isActive, onComplete }: LivePreviewProps) {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [events, setEvents] = useState<SearchEvent[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [papers, setPapers] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [totalFound, setTotalFound] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [searchSources, setSearchSources] = useState<string[]>([]);
  const [cognitiveEntropy, setCognitiveEntropy] = useState<number | null>(null);
  const [cognitiveMode, setCognitiveMode] = useState<'exploration' | 'exploitation' | 'balanced' | undefined>();
  const [viewMode, setViewMode] = useState<'graph' | 'timeline'>('timeline');
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptRef = useRef(0);
  const isCompleteRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const clearPreview = useCallback(() => {
    setEvents([]);
    setKeywords([]);
    setPapers([]);
    setCurrentStep('');
    setTotalFound(0);
    setIsComplete(false);
    isCompleteRef.current = false;
    setSearchSources([]);
    setCognitiveEntropy(null);
    setCognitiveMode(undefined);
  }, []);

  const handleSearchEvent = useCallback((searchEvent: SearchEvent) => {
    setEvents(prev => [...prev, searchEvent]);

    switch (searchEvent.type) {
      case 'connected':
        break;
      case 'keywords':
        setKeywords(searchEvent.data.keywords || []);
        break;
      case 'search_started':
        setSearchSources(searchEvent.data.sources || []);
        setCurrentStep(`Searching ${searchEvent.data.sources?.length || 0} sources...`);
        break;
      case 'search_results':
        setTotalFound(searchEvent.data.total_found || 0);
        setCurrentStep(`Found ${searchEvent.data.papers_count} papers from ${searchEvent.data.total_found} results`);
        break;
      case 'paper_found':
        setPapers(prev => {
          const exists = prev.some(p => p.id === searchEvent.data.id);
          if (exists) return prev;
          return [...prev, searchEvent.data];
        });
        break;
      case 'search_complete':
        setCurrentStep(`Search complete — ${searchEvent.data.papers_count} papers collected`);
        break;
      case 'run_completed':
        setCurrentStep('Research run completed');
        setIsComplete(true);
        isCompleteRef.current = true;
        onCompleteRef.current?.();
        break;
      case 'run_failed':
        setCurrentStep(`Run failed: ${searchEvent.data.error}`);
        setIsComplete(true);
        isCompleteRef.current = true;
        break;
      case 'step_started':
        setCurrentStep(searchEvent.data.label || searchEvent.data.step);
        break;
      case 'step_completed':
        setCurrentStep(`${searchEvent.data.phase_label || searchEvent.data.step} complete`);
        break;
      case 'thinking':
        if (searchEvent.data.thought) {
          setCurrentStep(searchEvent.data.thought.slice(0, 120));
        }
        break;
      case 'approval_required':
        setCurrentStep(`Awaiting approval: ${searchEvent.data.message || searchEvent.data.step}`);
        break;
      case 'cognitive_update':
      case 'papers_clustered':
        if (typeof searchEvent.data.entropy === 'number') {
          setCognitiveEntropy(searchEvent.data.entropy);
        }
        if (searchEvent.data.mode) {
          setCognitiveMode(searchEvent.data.mode);
        }
        if (searchEvent.type === 'papers_clustered') {
          setCurrentStep(`Clustered into ${searchEvent.data.clusters || 0} thematic groups`);
        }
        break;
    }

    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, []);

  const connectStream = useCallback(() => {
    if (!runId || !isActive || isCompleteRef.current) {
      return;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    const eventSource = new EventSource(`/api/v1/search/stream/${runId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      reconnectAttemptRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const searchEvent: SearchEvent = JSON.parse(event.data);
        handleSearchEvent(searchEvent);

        if (searchEvent.type === 'run_failed' || searchEvent.type === 'run_completed') {
          eventSource.close();
          eventSourceRef.current = null;
          setIsConnected(false);
        }
      } catch {
        // ignore malformed frames
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
      eventSourceRef.current = null;

      if (isCompleteRef.current || !isActive) {
        return;
      }

      const delay = Math.min(1000 * 2 ** reconnectAttemptRef.current, 30000);
      reconnectAttemptRef.current += 1;
      reconnectTimerRef.current = setTimeout(() => {
        connectStream();
      }, delay);
    };
  }, [runId, isActive, handleSearchEvent]);

  useEffect(() => {
    if (!runId || !isActive) {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    clearPreview();
    reconnectAttemptRef.current = 0;
    connectStream();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setIsConnected(false);
    };
  }, [runId, isActive, clearPreview, connectStream]);

  if (!runId || !isActive) {
    return null;
  }

  return (
    <div className="glass rounded-[2rem] overflow-hidden shadow-2xl transition-all duration-1000 border border-border/5">
      {/* Header */}
      <div className="px-8 py-6 border-b border-border/5 bg-stone-50/50 dark:bg-stone-900/50 backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
               <Search size={18} className="text-primary animate-pulse" />
            </div>
            <span className="text-xs font-black text-foreground tracking-[0.2em] uppercase">Live Research Telemetry</span>
          </div>
          <div className="flex items-center gap-3">
            {isConnected ? (
              <Badge variant="success" size="sm" className="bg-success/10 text-success border-success/20 px-3 py-1">
                <span className="w-1.5 h-1.5 bg-success rounded-full mr-2 animate-ping" />
                Live Feed
              </Badge>
            ) : (
              <Badge variant="default" size="sm" className="bg-muted text-muted-foreground/40 px-3 py-1">Offline</Badge>
            )}
            {isComplete && (
              <Badge variant="info" size="sm" className="bg-primary text-stone-900 font-black animate-bounce px-3 py-1 shadow-lg shadow-primary/20">
                <CheckCircle size={12} className="mr-2" />
                Cycle Finalized
              </Badge>
            )}
          </div>
        </div>
      </div>

      {cognitiveEntropy !== null && (
        <div className="px-8 py-4 border-b border-border/5 bg-stone-50/30 dark:bg-stone-900/30">
          <CognitiveEntropy
            entropy={cognitiveEntropy}
            mode={cognitiveMode}
            size="sm"
          />
        </div>
      )}

      {/* Content */}
      <div ref={containerRef} className="max-h-[700px] overflow-y-auto p-8 space-y-10 custom-scrollbar scroll-smooth">
        {/* View Toggle */}
        {events.length > 0 && (
          <div className="flex items-center justify-between mb-4 border-b border-border/5 pb-4">
            <div className="flex gap-2">
              <Button 
                variant={viewMode === 'timeline' ? 'primary' : 'ghost'} 
                size="sm" 
                className={cn("rounded-xl px-4 py-2 text-[9px] font-black uppercase tracking-widest", viewMode !== 'timeline' && "text-muted-foreground/60")}
                onClick={() => setViewMode('timeline')}
              >
                <ListTree size={12} className="mr-2" /> Timeline View
              </Button>
              <Button 
                variant={viewMode === 'graph' ? 'primary' : 'ghost'} 
                size="sm" 
                className={cn("rounded-xl px-4 py-2 text-[9px] font-black uppercase tracking-widest", viewMode !== 'graph' && "text-muted-foreground/60")}
                onClick={() => setViewMode('graph')}
              >
                <Network size={12} className="mr-2" /> Topology Graph
              </Button>
            </div>
            
            {viewMode === 'graph' && (
              <div className="flex items-center gap-3 animate-in fade-in duration-500">
                <div className="p-1.5 bg-tertiary/10 rounded-lg">
                  <Network size={14} className="text-tertiary" />
                </div>
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">Cognitive Topology</span>
              </div>
            )}
          </div>
        )}

        {/* Cognitive Visualization */}
        {events.length > 0 && (
          <div className="animate-in fade-in zoom-in-95 duration-1000">
            {viewMode === 'graph' ? (
              <div className="h-[400px] w-full bg-stone-50/30 dark:bg-stone-900/30 rounded-[2rem] border border-border/5 overflow-hidden">
                <ThinkingTree events={events} />
              </div>
            ) : (
              <ThinkingTimeline events={events} isComplete={isComplete} />
            )}
          </div>
        )}

        {/* Current Status */}
        {currentStep && (
          <div className="flex items-center justify-between py-6 px-8 bg-stone-50 dark:bg-stone-900/50 rounded-3xl border border-border/5 animate-in slide-in-from-right-4 duration-500 shadow-inner group">
            <div className="flex items-center gap-4">
               {!isComplete ? (
                 <div className="relative">
                   <Loader2 size={20} className="animate-spin text-primary" />
                   <div className="absolute inset-0 animate-ping opacity-20 bg-primary rounded-full scale-150" />
                 </div>
               ) : (
                 <div className="p-2 bg-success/10 rounded-full">
                    <CheckCircle size={20} className="text-success" />
                 </div>
               )}
               <span className="text-base font-bold text-foreground tracking-tight">{currentStep}</span>
            </div>
            {isComplete && runId && (
               <Button 
                variant="primary" 
                size="sm" 
                className="rounded-xl px-8 py-5 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 animate-in zoom-in-95 duration-700 hover:scale-105 transition-all"
                onClick={() => router.push(`/projects/${projectId}/studio/${runId}`)}
               >
                  Open Study Studio <ArrowRight size={14} className="ml-2" />
               </Button>
            )}
          </div>
        )}

        {/* Keywords */}
        {keywords.length > 0 && (
          <div className="animate-in slide-in-from-left-4 duration-1000">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-1.5 bg-warning/10 rounded-lg">
                <Zap size={14} className="text-warning" />
              </div>
              <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">Thematic Vectors</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw, i) => (
                <Badge key={i} variant="info" size="sm" className="bg-white dark:bg-stone-800 text-foreground/70 text-[9px] font-black uppercase tracking-widest px-3 py-1.5 border border-border/5 hover:border-primary/20 transition-all cursor-default">
                  {kw}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Papers */}
        {papers.length > 0 && (
          <div className="space-y-6 animate-in fade-in duration-1000">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-primary/10 rounded-lg">
                  <FileText size={14} className="text-primary" />
                </div>
                <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">
                  Discovered Corpus ({papers.length})
                </span>
              </div>
              {totalFound > 0 && (
                <Badge className="bg-stone-100 dark:bg-stone-800 text-[8px] font-black text-muted-foreground/40 uppercase tracking-tighter">
                  Global Search Pool: {totalFound}
                </Badge>
              )}
            </div>
            <div className="grid gap-3">
              {papers.slice(-10).reverse().map((paper, i) => (
                <div
                  key={paper.id || i}
                  className="p-5 bg-white/40 dark:bg-stone-900/40 backdrop-blur-sm rounded-[1.5rem] border border-border/5 shadow-sm transition-all duration-500 hover:shadow-lg hover:border-primary/20 hover:-translate-x-1 animate-in slide-in-from-left-2"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <p className="font-bold text-foreground tracking-tight line-clamp-1 leading-snug">{paper.title}</p>
                  <div className="flex items-center gap-4 mt-3">
                    {paper.source && <Badge className="bg-primary/5 text-primary text-[8px] font-black uppercase tracking-widest">{paper.source}</Badge>}
                    <span className="text-[9px] font-black text-muted-foreground/30 uppercase tracking-widest">{paper.year || 'N/A'}</span>
                    {paper.authors?.length > 0 && (
                      <span className="text-[9px] font-bold text-muted-foreground/60 truncate italic">
                        {paper.authors.slice(0, 1).join('')}
                        {paper.authors.length > 1 && ` et al.`}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Waiting state */}
        {events.length === 0 && isConnected && (
          <div className="text-center py-20 px-6 animate-pulse">
            <div className="w-20 h-20 bg-stone-100 dark:bg-stone-800 rounded-[2.5rem] flex items-center justify-center mx-auto mb-6 border border-border/5 shadow-inner">
              <Loader2 size={32} className="animate-spin text-muted-foreground/20" />
            </div>
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.5em]">Synchronizing Lab Protocols...</p>
          </div>
        )}
      </div>
    </div>
  );
}
