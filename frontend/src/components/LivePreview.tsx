'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Search, FileText, CheckCircle, AlertCircle, Loader2, Zap } from 'lucide-react';

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
  const [events, setEvents] = useState<SearchEvent[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [papers, setPapers] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [totalFound, setTotalFound] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [searchSources, setSearchSources] = useState<string[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
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
    setSearchSources([]);
  }, []);

  useEffect(() => {
    if (!runId || !isActive) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    clearPreview();

    const eventSource = new EventSource(`/api/v1/search/stream/${runId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const searchEvent: SearchEvent = JSON.parse(event.data);
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
            setIsComplete(true);
            break;
          case 'run_completed':
            setCurrentStep('Research run completed');
            setIsComplete(true);
            onCompleteRef.current?.();
            eventSource.close();
            break;
          case 'run_failed':
            setCurrentStep(`Run failed: ${searchEvent.data.error}`);
            setIsComplete(true);
            eventSource.close();
            break;
          case 'step_started':
            setCurrentStep(searchEvent.data.label || searchEvent.data.step);
            break;
        }

        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      } catch (e) {
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [runId, isActive]);  // REMOVED onComplete and clearPreview from deps

  if (!runId || !isActive) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search size={16} className="text-blue-600" />
            <span className="text-sm font-medium text-gray-900">Live Search Preview</span>
          </div>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Badge variant="success" size="sm">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1 animate-pulse" />
                Connected
              </Badge>
            ) : (
              <Badge variant="default" size="sm">Disconnected</Badge>
            )}
            {isComplete && (
              <Badge variant="info" size="sm">
                <CheckCircle size={12} className="mr-1" />
                Done
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div ref={containerRef} className="max-h-96 overflow-y-auto p-4 space-y-4">
        {/* Keywords */}
        {keywords.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap size={14} className="text-yellow-500" />
              <span className="text-xs font-medium text-gray-500 uppercase">Keywords</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {keywords.map((kw, i) => (
                <Badge key={i} variant="info" size="sm">{kw}</Badge>
              ))}
            </div>
          </div>
        )}

        {/* Current Status */}
        {currentStep && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            {!isComplete ? (
              <Loader2 size={14} className="animate-spin text-blue-500" />
            ) : (
              <CheckCircle size={14} className="text-green-500" />
            )}
            <span>{currentStep}</span>
          </div>
        )}

        {/* Search Sources */}
        {searchSources.length > 0 && (
          <div>
            <span className="text-xs font-medium text-gray-500 uppercase">Sources</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {searchSources.map((src, i) => (
                <Badge key={i} variant="default" size="sm">{src}</Badge>
              ))}
            </div>
          </div>
        )}

        {/* Papers */}
        {papers.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FileText size={14} className="text-purple-500" />
              <span className="text-xs font-medium text-gray-500 uppercase">
                Papers ({papers.length})
              </span>
              {totalFound > 0 && (
                <span className="text-xs text-gray-400">
                  of {totalFound} total
                </span>
              )}
            </div>
            <div className="space-y-2">
              {papers.slice(-20).map((paper, i) => (
                <div
                  key={paper.id || i}
                  className="p-2 bg-gray-50 rounded-lg text-sm border border-gray-100 animate-in fade-in slide-in-from-bottom-1"
                >
                  <p className="font-medium text-gray-800 line-clamp-1">{paper.title}</p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    {paper.source && <span className="text-blue-500">{paper.source}</span>}
                    {paper.year && <span>{paper.year}</span>}
                    {paper.authors?.length > 0 && (
                      <span className="truncate">
                        {paper.authors.slice(0, 2).join(', ')}
                        {paper.authors.length > 2 && '...'}
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
          <div className="text-center py-6 text-gray-400">
            <Loader2 size={20} className="animate-spin mx-auto mb-2" />
            <p className="text-sm">Waiting for search events...</p>
          </div>
        )}
      </div>
    </div>
  );
}
