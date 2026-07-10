'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { manuscriptsApi } from '@/lib/api';
import { Manuscript } from '@/lib/types';
import { Loader2, FileText, Download, Edit3, Send, History, Eye, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LaTeXPrism } from '@/components/ui/LaTeXPrism';

export default function ManuscriptsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [manuscripts, setManuscripts] = useState<Manuscript[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedManuscript, setSelectedManuscript] = useState<Manuscript | null>(null);

  useEffect(() => {
    loadManuscripts();
  }, [projectId]);

  const loadManuscripts = async () => {
    try {
      setLoading(true);
      const data = await manuscriptsApi.list(projectId);
      setManuscripts(data);
    } catch (error) {
      console.error('Failed to load manuscripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateManuscript = async (newContent: string) => {
    if (!selectedManuscript) return;
    try {
      const updated = await manuscriptsApi.update(selectedManuscript.id, { content_latex: newContent });
      setManuscripts(manuscripts.map(m => m.id === updated.id ? updated : m));
      setSelectedManuscript(updated);
    } catch (error) {
      console.error('Failed to update manuscript:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'finalized': return 'bg-success/10 text-success border-success/20';
      case 'reviewing': return 'bg-warning/10 text-warning border-warning/20';
      default: return 'bg-primary/10 text-primary border-primary/20';
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Scientific Manuscripts"
        subtitle="Automated study synthesis and LaTeX documentation"
        actions={
          <Badge variant="info" className="bg-primary/5 uppercase text-[10px] font-black tracking-widest px-4 py-1.5 border border-primary/10">
            {manuscripts.length} Study Drafts
          </Badge>
        }
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2].map(i => (
              <div key={i} className="h-64 glass rounded-[2.5rem] animate-pulse" />
            ))}
          </div>
        ) : manuscripts.length === 0 ? (
          <Card className="glass p-20 text-center border-border/5">
             <div className="w-24 h-24 bg-stone-100 dark:bg-stone-900 rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-inner">
                <FileText size={48} className="text-muted-foreground/20" />
             </div>
             <h3 className="text-2xl font-black text-foreground mb-4 tracking-tighter uppercase">No Manuscripts Synthesized</h3>
             <p className="text-muted-foreground font-medium max-w-md mx-auto leading-relaxed mb-10">
               Complete a full validation research run to automatically generate a formatted LaTeX manuscript of your findings.
             </p>
             <Button variant="primary" className="rounded-2xl px-10 py-6 text-[10px] font-black uppercase tracking-widest">
                Initialize Research Cycle
             </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in duration-700">
            {manuscripts.map((m) => (
              <Card 
                key={m.id} 
                hover 
                className="group overflow-hidden border-border/5"
                onClick={() => setSelectedManuscript(m)}
              >
                <div className="p-8 h-full flex flex-col">
                  <div className="flex items-start justify-between mb-6">
                    <div className="p-4 bg-primary/10 text-primary rounded-2xl shadow-inner group-hover:bg-primary group-hover:text-stone-900 transition-all duration-500 group-hover:rotate-6">
                       <FileText size={24} />
                    </div>
                    <Badge variant="info" className={cn("uppercase text-[8px] font-black tracking-widest px-3 py-1 border shadow-sm", getStatusColor(m.status))}>
                      {m.status}
                    </Badge>
                  </div>
                  
                  <h3 className="text-xl font-black text-foreground tracking-tighter mb-4 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                    {m.title}
                  </h3>
                  
                  <div className="flex items-center gap-6 mt-auto pt-6 border-t border-border/5">
                     <div className="flex flex-col">
                        <span className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Version</span>
                        <span className="text-sm font-black text-foreground">{m.version}.0.0</span>
                     </div>
                     <div className="w-px h-8 bg-border/10" />
                     <div className="flex flex-col">
                        <span className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Drafted</span>
                        <span className="text-sm font-black text-foreground">{new Date(m.created_at).toLocaleDateString()}</span>
                     </div>
                  </div>

                  <div className="mt-8 flex items-center gap-3">
                     <Button variant="ghost" size="sm" className="flex-1 rounded-xl text-[9px] font-black uppercase tracking-widest border border-border/10 bg-white dark:bg-stone-800 shadow-sm">
                        <Eye size={14} className="mr-2" /> View
                     </Button>
                     <Button variant="ghost" size="sm" className="flex-1 rounded-xl text-[9px] font-black uppercase tracking-widest border border-border/10 bg-white dark:bg-stone-800 shadow-sm">
                        <Download size={14} className="mr-2" /> .TEX
                     </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Manuscript Viewer Modal */}
      <Modal
        isOpen={!!selectedManuscript}
        onClose={() => setSelectedManuscript(null)}
        title={selectedManuscript?.title || 'Manuscript Analysis'}
        size="lg"
      >
        {selectedManuscript && (
          <div className="space-y-10 py-4 animate-in fade-in duration-500">
             {/* Stats Row */}
             <div className="flex items-center gap-4 p-6 bg-stone-50 dark:bg-stone-900 rounded-[2rem] border border-border/5 shadow-inner">
                <div className="flex-1 text-center border-r border-border/10">
                   <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Status</p>
                   <p className="text-sm font-black text-primary uppercase">{selectedManuscript.status}</p>
                </div>
                <div className="flex-1 text-center border-r border-border/10">
                   <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Revision</p>
                   <p className="text-sm font-black text-foreground">v{selectedManuscript.version}</p>
                </div>
                <div className="flex-1 text-center">
                   <p className="text-[9px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Compliance</p>
                   <p className="text-sm font-black text-success uppercase">IMRAD Standard</p>
                </div>
             </div>

             {/* Action Bar */}
             <div className="flex flex-wrap gap-4">
                <Button variant="ghost" className="rounded-2xl px-6 py-5 text-[9px] font-black uppercase tracking-widest border border-border/10 bg-white dark:bg-stone-800 shadow-sm">
                   <History size={14} className="mr-2" /> Revision History
                </Button>
                <Button variant="ghost" className="ml-auto rounded-2xl px-6 py-5 text-[9px] font-black uppercase tracking-widest text-success hover:bg-success/5">
                   <CheckCircle size={14} className="mr-2" /> Mark as Finalized
                </Button>
             </div>

             <LaTeXPrism 
                content={selectedManuscript.content_latex || '% NO CONTENT GENERATED'} 
                onUpdate={updateManuscript}
             />
          </div>
        )}
      </Modal>
    </Layout>
  );
}
