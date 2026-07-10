'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { papersApi } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Layers, BookOpen, Hash, AlertTriangle, ArrowRight, X, FileText, ExternalLink, GitBranch, Network, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Project, Paper, ClusterConflict, PaperCluster, ClusterLabel } from '@/lib/types';
import { SemanticMap } from '@/components/ui/SemanticMap';

type TabType = 'overview' | 'map' | 'corpus' | 'conflicts';

export default function ClustersPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [clusters, setClusters] = useState<PaperCluster[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedCluster, setSelectedCluster] = useState<PaperCluster | null>(null);
  const [clusterPapers, setClusterPapers] = useState<Paper[]>([]);
  const [clusterConflicts, setClusterConflicts] = useState<ClusterConflict[]>([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  useEffect(() => {
    loadClusters();
  }, [projectId]);

  async function loadClusters() {
    setLoading(true);
    try {
      const data = await papersApi.clusters(projectId);
      setClusters(data || []);
    } catch (e) {
      setError('Failed to load clusters');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }
const openClusterDetails = async (cluster: PaperCluster) => {
  setSelectedCluster(cluster);
  setModalLoading(true);
  setActiveTab('overview');
  try {
     // Fetch conflicts related to this cluster
     const conflicts = await papersApi.conflicts(projectId, undefined, cluster.id);
     setClusterConflicts(conflicts);

     // Fetch papers belonging specifically to this cluster
     const papers = await papersApi.list(projectId, undefined, cluster.id);
     setClusterPapers(papers);
  } catch (e) {
       console.error("Failed to load cluster details", e);
    } finally {
       setModalLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout projectId={projectId}>
        <Header title="Thematic Clusters" />
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1,2,3,4,5,6].map(i => (
              <div key={i} className="h-64 bg-stone-50 dark:bg-stone-900/40 border border-stone-200/10 rounded-3xl animate-pulse" />
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout projectId={projectId}>
        <Header title="Thematic Clusters" />
        <div className="p-6">
          <Card className="glass p-12 text-center border-error/10">
            <div className="w-20 h-20 bg-error/10 rounded-full flex items-center justify-center mx-auto mb-6">
               <AlertTriangle size={40} className="text-error" />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-2 uppercase tracking-tight">Clustering Synchronization Failed</h3>
            <p className="text-muted-foreground font-medium">{error}</p>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout projectId={projectId}>
      <Header 
        title="Thematic Clusters" 
        subtitle="Semantic mapping of identified literature frontier"
        actions={
          <Badge variant="info" className="bg-primary/5 uppercase text-[10px] font-bold tracking-[0.2em] px-4 py-1.5 border border-primary/10 shadow-inner">
            {clusters.length} Core Nodes Identified
          </Badge>
        }
      />
      <div className="p-6 space-y-8 animate-in fade-in duration-700">
        {clusters.length === 0 ? (
          <EmptyState
            title="No thematic clusters synthesized"
            description="Autonomous research cycles will discover semantic patterns and group publications by research vector."
            icon={<Layers size={48} className="text-muted-foreground/30" />}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clusters.map((cluster) => {
              const isExpanded = expandedId === cluster.id;
              return (
                <Card
                  key={cluster.id}
                  hover
                  className={cn(
                    'transition-all duration-500 overflow-hidden group cursor-pointer border-border/5',
                    isExpanded ? 'ring-2 ring-primary/30 shadow-2xl scale-[1.02]' : ''
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : cluster.id)}
                >
                  <div className="p-8 h-full flex flex-col">
                    {/* Header */}
                    <div className="space-y-4 mb-6">
                      <div className="flex items-start justify-between">
                        <div className={cn(
                          "p-3 rounded-xl shadow-inner transition-all duration-500",
                          isExpanded ? "bg-primary text-stone-900 scale-110 rotate-6" : "bg-primary/10 text-primary group-hover:bg-primary/20"
                        )}>
                           <Layers size={24} />
                        </div>
                        {cluster.cluster_type && (
                          <Badge variant="info" size="sm" className="bg-primary/5 uppercase text-[9px] font-bold tracking-widest border border-primary/10">
                            {cluster.cluster_type}
                          </Badge>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-foreground tracking-tight leading-tight group-hover:text-primary transition-colors">
                          {cluster.name || cluster.cluster_type || 'Synthetic Node'}
                        </h3>
                        {cluster.description && (
                          <p className="text-sm text-muted-foreground font-medium mt-3 line-clamp-3 leading-relaxed">{cluster.description}</p>
                        )}
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="flex items-center gap-6 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-[0.2em] mb-6 pt-6 border-t border-border/5">
                      <div className="flex items-center gap-2">
                        <BookOpen size={14} className="text-primary/40" />
                        <span>{cluster.paper_ids?.length || 0} Corpus Entries</span>
                      </div>
                      {cluster.labels && cluster.labels.length > 0 && (
                        <div className="flex items-center gap-2">
                          <Hash size={14} className="text-tertiary/40" />
                          <span>{cluster.labels.length} Vector Labels</span>
                        </div>
                      )}
                    </div>

                    {/* Labels */}
                    {cluster.labels && cluster.labels.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-auto">
                        {cluster.labels.slice(0, isExpanded ? undefined : 6).map((l, i) => (
                          <Badge key={i} variant="default" size="sm" className="bg-stone-100 dark:bg-stone-800 text-foreground/70 text-[9px] font-black uppercase tracking-widest px-2.5 py-1 border border-border/5">
                            {l.label}
                          </Badge>
                        ))}
                        {!isExpanded && cluster.labels.length > 6 && (
                          <Badge variant="default" size="sm" className="bg-muted text-[9px] font-black tracking-widest px-2.5 py-1 opacity-40">+{cluster.labels.length - 6}</Badge>
                        )}
                      </div>
                    )}
                    
                    {isExpanded && (
                       <div className="mt-8 pt-6 border-t border-border/5 animate-in slide-in-from-top-2 duration-500">
                          <Button 
                            variant="primary" 
                            size="sm" 
                            className="w-full justify-center text-[10px] font-black tracking-[0.2em] uppercase rounded-xl py-6 shadow-xl shadow-primary/20"
                            onClick={(e) => {
                              e.stopPropagation();
                              openClusterDetails(cluster);
                            }}
                          >
                             View Semantic Mapping <ArrowRight size={14} className="ml-2" />
                          </Button>
                       </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Cluster Details Modal */}
      <Modal
        isOpen={!!selectedCluster}
        onClose={() => setSelectedCluster(null)}
        title={selectedCluster?.name || 'Cluster Details'}
        size="lg"
      >
        {selectedCluster && (
          <div className="space-y-8 py-4">
            {/* Tabs */}
            <div className="flex items-center gap-2 p-1.5 bg-stone-100 dark:bg-stone-900 rounded-2xl border border-border/5">
              {[
                { id: 'overview', label: 'Overview', icon: Layers },
                { id: 'map', label: 'Semantic Map', icon: Network },
                { id: 'corpus', label: 'Corpus', icon: BookOpen },
                { id: 'conflicts', label: 'Conflicts', icon: GitBranch },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={cn(
                    "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-300",
                    activeTab === tab.id 
                      ? "bg-white dark:bg-stone-800 text-primary shadow-lg shadow-black/5" 
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <tab.icon size={14} />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="animate-in fade-in duration-500">
              {activeTab === 'overview' && (
                <div className="space-y-8">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-[10px] font-black text-primary uppercase tracking-[0.3em]">
                        <Layers size={14} />
                        <span>Thematic Context</span>
                    </div>
                    <p className="text-base text-foreground/80 leading-relaxed font-medium bg-stone-50 dark:bg-stone-900/50 p-6 rounded-2xl border border-border/5 shadow-inner">
                      {selectedCluster.description}
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-[10px] font-black text-tertiary uppercase tracking-[0.3em]">
                        <Hash size={14} />
                        <span>Semantic Vector Labels</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedCluster.labels.map((l, i) => (
                          <div key={i} className="p-5 bg-white dark:bg-stone-900/60 rounded-2xl border border-border/5 shadow-sm hover:border-primary/20 transition-all group">
                            <Badge className="mb-3 bg-primary/10 text-primary border-primary/20 group-hover:bg-primary group-hover:text-white transition-colors">{l.label}</Badge>
                            {l.rationale && (
                               <p className="text-xs text-muted-foreground leading-relaxed font-medium italic">&ldquo;{l.rationale}&rdquo;</p>
                            )}
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'map' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-[10px] font-black text-primary uppercase tracking-[0.3em]">
                        <Network size={14} />
                        <span>Vector Topology</span>
                    </div>
                    {modalLoading && <Loader2 size={14} className="animate-spin text-primary" />}
                  </div>
                  <SemanticMap cluster={selectedCluster} papers={clusterPapers} />
                </div>
              )}

              {activeTab === 'corpus' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em]">
                        <BookOpen size={14} />
                        <span>Corpus Entries ({selectedCluster.paper_ids?.length || 0})</span>
                      </div>
                      {modalLoading && <Loader2 size={14} className="animate-spin text-primary" />}
                  </div>
                  
                  <div className="space-y-3 max-h-[450px] overflow-y-auto custom-scrollbar pr-2">
                      {clusterPapers.length > 0 ? clusterPapers.map(paper => (
                        <div key={paper.id} className="flex items-center justify-between p-4 bg-stone-50 dark:bg-stone-900/40 rounded-xl border border-border/5 group hover:border-primary/20 transition-all">
                          <div className="flex-1 min-w-0 pr-4">
                              <h4 className="text-sm font-bold text-foreground truncate group-hover:text-primary transition-colors">{paper.title}</h4>
                              <p className="text-[10px] text-muted-foreground/60 uppercase font-bold mt-1">
                                {paper.authors.slice(0, 2).join(', ')} {paper.authors.length > 2 && 'et al.'} • {paper.year || 'N/A'}
                              </p>
                          </div>
                          <a 
                            href={paper.url || paper.doi ? (paper.url || `https://doi.org/${paper.doi}`) : '#'} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="p-2 bg-white dark:bg-stone-800 rounded-lg shadow-sm text-muted-foreground hover:text-primary transition-colors"
                          >
                              <ExternalLink size={14} />
                          </a>
                        </div>
                      )) : (
                        <div className="py-20 text-center border-2 border-dashed border-border/10 rounded-3xl italic text-[10px] text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                          {modalLoading ? "Synchronizing corpus..." : "No papers linked to this node"}
                        </div>
                      )}
                  </div>
                </div>
              )}

              {activeTab === 'conflicts' && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-[10px] font-black text-error uppercase tracking-[0.3em]">
                      <GitBranch size={14} />
                      <span>Active Scientific Tensions ({clusterConflicts.length})</span>
                  </div>
                  {clusterConflicts.length > 0 ? (
                    <div className="space-y-3">
                        {clusterConflicts.map(conflict => (
                          <div key={conflict.id} className="p-6 bg-error/5 dark:bg-error/[0.02] rounded-2xl border border-error/10 hover:border-error/30 transition-all">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-[10px] font-black uppercase text-error tracking-widest">{conflict.conflict_type}</span>
                                <Badge variant="danger" size="sm" className="bg-error text-white font-black px-3 py-1">Severity: {conflict.severity?.toFixed(2)}</Badge>
                            </div>
                            <p className="text-sm text-foreground/80 leading-relaxed font-bold tracking-tight mb-4">{conflict.description}</p>
                            {conflict.supporting_papers.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-error/10">
                                   <p className="text-[9px] font-black text-error/60 uppercase tracking-widest mb-2">Affected Research Vectors</p>
                                   <div className="flex flex-wrap gap-2">
                                      {conflict.supporting_papers.slice(0, 3).map((p, i) => (
                                         <Badge key={i} variant="default" className="text-[8px] font-bold border-error/20 text-error/70">CORPUS_ID: {p.slice(0,8)}</Badge>
                                      ))}
                                   </div>
                                </div>
                            )}
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="py-20 text-center border-2 border-dashed border-border/10 rounded-3xl italic text-[10px] text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                        {modalLoading ? "Analyzing tensions..." : "No internal contradictions detected"}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}
