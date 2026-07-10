'use client';

import React, { useEffect, useState } from 'react';
import { papersApi } from '@/lib/api';
import { Paper } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { formatDate } from '@/lib/utils';
import { Loader2, BookOpen, ExternalLink, Activity, Target, AlertCircle, Bookmark } from 'lucide-react';

interface PaperAnalysis {
  problem?: string;
  method?: string;
  findings?: string[];
  limitations?: string[];
}

interface KnowledgeCardProps {
  paperId: string;
}

export function KnowledgeCard({ paperId }: KnowledgeCardProps) {
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDetails() {
      setLoading(true);
      try {
        const data = await papersApi.get(paperId);
        setPaper(data);
      } catch (err) {
        console.error('Failed to load paper details', err);
      } finally {
        setLoading(false);
      }
    }
    loadDetails();
  }, [paperId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="animate-spin text-primary" size={40} />
        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/40">Synchronizing Knowledge Node...</p>
      </div>
    );
  }

  if (!paper) return null;

  const analysis = (paper as any).analysis as PaperAnalysis | undefined;

  return (
    <div className="space-y-10 py-4 animate-in fade-in duration-700">
      {/* Header Info */}
      <div className="space-y-6">
        <div className="flex items-start justify-between">
          <Badge variant="info" className="bg-primary/5 uppercase text-[9px] font-black tracking-widest px-3 py-1 border border-primary/10 shadow-inner">
            {paper.paper_type || 'Research'} Corpus Node
          </Badge>
          <div className="flex items-center gap-3">
             {paper.year && <span className="text-[10px] font-black text-muted-foreground/40 uppercase tracking-widest">{paper.year}</span>}
             <a 
              href={paper.url || (paper.doi ? `https://doi.org/${paper.doi}` : '#')} 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-2 bg-stone-100 dark:bg-stone-800 rounded-lg hover:text-primary transition-colors"
             >
               <ExternalLink size={14} />
             </a>
          </div>
        </div>
        <h2 className="text-3xl font-black text-foreground tracking-tighter leading-tight">{paper.title}</h2>
        <div className="flex flex-wrap gap-2">
          {paper.authors.slice(0, 5).map((author, i) => (
            <span key={i} className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-stone-50 dark:bg-stone-900/50 px-3 py-1 rounded-full border border-border/5">
              {author}
            </span>
          ))}
          {paper.authors.length > 5 && <span className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest px-2 py-1 italic">+{paper.authors.length - 5} more</span>}
        </div>
      </div>

      {/* Abstract */}
      {paper.abstract && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[10px] font-black text-primary uppercase tracking-[0.3em]">
             <BookOpen size={14} />
             <span>Scientific Abstract</span>
          </div>
          <p className="text-sm text-foreground/70 leading-relaxed font-medium bg-stone-50 dark:bg-stone-900/40 p-6 rounded-2xl border border-border/5 shadow-inner">
            {paper.abstract}
          </p>
        </div>
      )}

      {/* Analysis Grid */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
           {/* Problem & Method */}
           <div className="space-y-6">
              <div className="space-y-3">
                 <div className="flex items-center gap-2 text-[10px] font-black text-tertiary uppercase tracking-[0.3em]">
                    <Target size={14} />
                    <span>Research Problem</span>
                 </div>
                 <p className="text-xs text-muted-foreground font-medium leading-relaxed">{analysis.problem || 'Not explicitly extracted'}</p>
              </div>
              <div className="space-y-3">
                 <div className="flex items-center gap-2 text-[10px] font-black text-success uppercase tracking-[0.3em]">
                    <Activity size={14} />
                    <span>Methodology</span>
                 </div>
                 <p className="text-xs text-muted-foreground font-medium leading-relaxed">{analysis.method || 'Not explicitly extracted'}</p>
              </div>
           </div>

           {/* Findings & Limitations */}
           <div className="space-y-6">
              <div className="space-y-3">
                 <div className="flex items-center gap-2 text-[10px] font-black text-primary uppercase tracking-[0.3em]">
                    <Bookmark size={14} />
                    <span>Key Findings</span>
                 </div>
                 <ul className="space-y-2">
                    {(analysis.findings || []).slice(0, 3).map((f: string, i: number) => (
                      <li key={i} className="text-xs text-muted-foreground font-medium flex gap-2">
                         <div className="w-1 h-1 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                         {f}
                      </li>
                    ))}
                    {(!analysis.findings || analysis.findings.length === 0) && <li className="text-xs text-muted-foreground/40 italic">No findings extracted yet</li>}
                 </ul>
              </div>
              <div className="space-y-3">
                 <div className="flex items-center gap-2 text-[10px] font-black text-error uppercase tracking-[0.3em]">
                    <AlertCircle size={14} />
                    <span>Limitations</span>
                 </div>
                 <p className="text-xs text-muted-foreground font-medium leading-relaxed">
                    {(analysis.limitations || [])[0] || 'No critical limitations recorded'}
                 </p>
              </div>
           </div>
        </div>
      )}

      {/* Relations footer */}
      <div className="pt-8 border-t border-border/5 flex items-center justify-between">
         <div className="flex items-center gap-4">
            <div className="text-center">
               <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Citations</p>
               <p className="text-sm font-black text-foreground">{paper.citation_count || 0}</p>
            </div>
            <div className="w-px h-8 bg-border/10" />
            <div className="text-center">
               <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Venue</p>
               <p className="text-sm font-black text-foreground truncate max-w-[150px]">{paper.venue || 'Unknown'}</p>
            </div>
         </div>
         <Badge variant="default" className="bg-stone-100 dark:bg-stone-800 text-[9px] font-bold tracking-widest">
            CORPUS_ID: {paper.id.slice(0,8)}
         </Badge>
      </div>
    </div>
  );
}
