'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { papersApi, projectsApi } from '@/lib/api';
import { Paper, ArxivSearchResult } from '@/lib/types';
import { FileText, ExternalLink, Trash2, Loader2, Network, List, Search, X, GitCompare, Quote, Download, BookPlus } from 'lucide-react';
import { CommentThread } from '@/components/common/CommentThread';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';
import { KnowledgeGraph } from '@/components/ui/KnowledgeGraph';
import { CitationGraph } from '@/components/ui/CitationGraph';
import { KnowledgeCard } from '@/components/ui/KnowledgeCard';
import { SearchBar } from '@/components/ui/search-bar';
import type { SemanticSearchResult, CitationGraph as CitationGraphData } from '@/lib/types';

type ViewMode = 'list' | 'graph' | 'citations';

export default function PapersPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [papers, setPapers] = useState<Paper[]>([]);
  const [graphData, setGraphData] = useState<any>(null);
  const [citationData, setCitationData] = useState<CitationGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [graphLoading, setGraphLoading] = useState(false);
  const [citationLoading, setCitationLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SemanticSearchResult[] | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [importDoi, setImportDoi] = useState('');
  const [importingDoi, setImportingDoi] = useState(false);
  const [arxivQuery, setArxivQuery] = useState('');
  const [arxivResults, setArxivResults] = useState<ArxivSearchResult[] | null>(null);
  const [arxivLoading, setArxivLoading] = useState(false);
  const [importingArxivId, setImportingArxivId] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);

  useEffect(() => {
    loadPapers();
  }, [projectId]);

  useEffect(() => {
    if (viewMode === 'graph' && !graphData) {
      loadGraph();
    }
    if (viewMode === 'citations' && !citationData) {
      loadCitationGraph();
    }
  }, [viewMode, projectId]);

  const loadPapers = async () => {
    try {
      setLoading(true);
      const data = await papersApi.list(projectId);
      setPapers(data);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadGraph = async () => {
    try {
      setGraphLoading(true);
      const data = await projectsApi.graph(projectId);
      setGraphData(data);
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadCitationGraph = async () => {
    try {
      setCitationLoading(true);
      const data = await papersApi.citationGraph(projectId);
      setCitationData(data);
    } catch (error) {
      console.error('Failed to load citation graph:', error);
    } finally {
      setCitationLoading(false);
    }
  };

  const handleSemanticSearch = async (query: string) => {
    const trimmed = query.trim();
    setSearchQuery(trimmed);
    if (trimmed.length < 3) {
      setSearchResults(null);
      setSearchError(trimmed ? 'Enter at least 3 characters' : null);
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    try {
      const response = await papersApi.semanticSearch(projectId, trimmed);
      setSearchResults(response.results);
      setViewMode('list');
    } catch (error) {
      console.error('Semantic search failed:', error);
      setSearchResults([]);
      setSearchError('Semantic search unavailable. Ensure papers are embedded.');
    } finally {
      setSearchLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
    setSearchError(null);
  };

  const displayedPapers =
    searchResults !== null
      ? searchResults
          .map((result) => {
            const paper = papers.find((p) => p.id === result.paper_id);
            return paper ? { paper, score: result.score } : null;
          })
          .filter((item): item is { paper: Paper; score: number } => item !== null)
      : papers.map((paper) => ({ paper, score: null as number | null }));

  const handleArxivSearch = async () => {
    const trimmed = arxivQuery.trim();
    if (trimmed.length < 2) return;
    setArxivLoading(true);
    setImportError(null);
    try {
      const response = await papersApi.arxivSearch(trimmed);
      setArxivResults(response.papers);
    } catch (error) {
      console.error('arXiv search failed:', error);
      setImportError('arXiv search failed');
      setArxivResults([]);
    } finally {
      setArxivLoading(false);
    }
  };

  const handleImportDoi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importDoi.trim()) return;
    setImportingDoi(true);
    setImportError(null);
    try {
      const paper = await papersApi.resolveDoi(projectId, importDoi.trim());
      setPapers((prev) => (prev.some((p) => p.id === paper.id) ? prev : [paper, ...prev]));
      setImportDoi('');
    } catch (error) {
      console.error('DOI import failed:', error);
      setImportError('Could not resolve DOI');
    } finally {
      setImportingDoi(false);
    }
  };

  const handleImportArxiv = async (sourceId: string) => {
    setImportingArxivId(sourceId);
    setImportError(null);
    try {
      const paper = await papersApi.importArxiv(projectId, sourceId);
      setPapers((prev) => (prev.some((p) => p.id === paper.id) ? prev : [paper, ...prev]));
    } catch (error) {
      console.error('arXiv import failed:', error);
      setImportError('Could not import arXiv paper');
    } finally {
      setImportingArxivId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this paper?')) return;
    setDeletingId(id);
    try {
      await papersApi.delete(id);
      setPapers(papers.filter(p => p.id !== id));
      // Invalidate graph data so it reloads
      setGraphData(null);
      setCitationData(null);
    } catch (error) {
      console.error('Failed to delete paper:', error);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Literature Corpus"
        subtitle={`${papers.length} scientific nodes identified`}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="sm" onClick={() => setShowImport((v) => !v)}>
              <BookPlus className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Link href={`/projects/${projectId}/papers/compare`}>
              <Button variant="secondary" size="sm">
                <GitCompare className="h-4 w-4 mr-2" />
                Compare
              </Button>
            </Link>
            <div className="flex items-center gap-2 p-1 bg-stone-100 dark:bg-stone-900 rounded-2xl border border-border/5 shadow-inner">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  "p-2 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-300 flex items-center gap-2",
                  viewMode === 'list' ? "bg-white dark:bg-stone-800 text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <List size={14} />
                <span>List</span>
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={cn(
                  "p-2 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-300 flex items-center gap-2",
                  viewMode === 'graph' ? "bg-white dark:bg-stone-800 text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Network size={14} />
                <span>Graph</span>
              </button>
              <button
                onClick={() => setViewMode('citations')}
                className={cn(
                  "p-2 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-300 flex items-center gap-2",
                  viewMode === 'citations' ? "bg-white dark:bg-stone-800 text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Quote size={14} />
                <span>Citations</span>
              </button>
            </div>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {showImport && (
          <div className="glass rounded-[2rem] p-6 border border-stone-200/10 space-y-6">
            <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
              Import Literature
            </h3>
            {importError && (
              <p className="text-sm text-error">{importError}</p>
            )}
            <form onSubmit={handleImportDoi} className="flex flex-col sm:flex-row gap-3 items-end">
              <div className="flex-1 w-full">
                <Input
                  label="DOI"
                  value={importDoi}
                  onChange={(e) => setImportDoi(e.target.value)}
                  placeholder="10.1234/example.doi"
                />
              </div>
              <Button type="submit" disabled={importingDoi}>
                {importingDoi ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Resolve DOI
              </Button>
            </form>
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row gap-3 items-end">
                <div className="flex-1 w-full">
                  <Input
                    label="arXiv Search"
                    value={arxivQuery}
                    onChange={(e) => setArxivQuery(e.target.value)}
                    placeholder="transformer attention"
                  />
                </div>
                <Button onClick={handleArxivSearch} disabled={arxivLoading}>
                  {arxivLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4 mr-2" />
                  )}
                  Search arXiv
                </Button>
              </div>
              {arxivResults && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {arxivResults.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No arXiv results.</p>
                  ) : (
                    arxivResults.map((result) => (
                      <div
                        key={result.source_id}
                        className="flex items-start justify-between gap-4 p-3 rounded-xl border border-border/10 bg-white/30"
                      >
                        <div className="min-w-0">
                          <p className="font-bold text-sm line-clamp-2">{result.title}</p>
                          <p className="text-[10px] text-muted-foreground mt-1">
                            {result.source_id} · {result.year || '—'}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleImportArxiv(result.source_id)}
                          disabled={importingArxivId === result.source_id}
                        >
                          {importingArxivId === result.source_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            'Import'
                          )}
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {!loading && papers.length > 0 && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex-1 max-w-xl">
              <SearchBar
                placeholder="Semantic search across corpus..."
                onSearch={handleSemanticSearch}
              />
            </div>
            {(searchQuery || searchResults !== null) && (
              <button
                onClick={clearSearch}
                className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={14} />
                Clear search
              </button>
            )}
          </div>
        )}

        {searchLoading && (
          <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-muted-foreground animate-pulse">
            <Loader2 size={14} className="animate-spin" />
            Searching semantic vectors...
          </div>
        )}

        {searchError && !searchLoading && (
          <p className="text-sm text-muted-foreground">{searchError}</p>
        )}

        {searchResults !== null && !searchLoading && searchResults.length === 0 && !searchError && (
          <EmptyState
            icon={<Search className="w-12 h-12 text-muted-foreground/20" />}
            title="No semantic matches"
            description={`No papers matched "${searchQuery}". Try broader terms or run research to embed more literature.`}
          />
        )}

        {loading ? (
          <SkeletonTable />
        ) : papers.length === 0 && searchResults === null ? (
          <EmptyState
            icon={<FileText className="w-12 h-12 text-muted-foreground/20" />}
            title="Evidence ledger is empty"
            description="Start a research run to discover and map scientific literature related to your hypothesis."
          />
        ) : displayedPapers.length > 0 ? (
          <div className="animate-in fade-in duration-700">
            {viewMode === 'list' ? (
              <div className="glass rounded-[2.5rem] overflow-hidden border border-stone-200/10 shadow-2xl">
                <Table>
                  <TableHeader className="bg-stone-50 dark:bg-stone-900/50">
                    <TableRow>
                      <TableHead className="py-6 px-8 text-[10px] font-black uppercase tracking-widest">Scientific Title</TableHead>
                      <TableHead className="py-6 text-[10px] font-black uppercase tracking-widest">Authors</TableHead>
                      <TableHead className="py-6 text-[10px] font-black uppercase tracking-widest">Year</TableHead>
                      <TableHead className="py-6 text-[10px] font-black uppercase tracking-widest text-center">Impact</TableHead>
                      <TableHead className="py-6 text-[10px] font-black uppercase tracking-widest">Type</TableHead>
                      {searchResults !== null && (
                        <TableHead className="py-6 text-[10px] font-black uppercase tracking-widest text-center">Match</TableHead>
                      )}
                      <TableHead className="py-6 px-8 text-right text-[10px] font-black uppercase tracking-widest">Intelligence</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {displayedPapers.map(({ paper, score }) => (
                      <TableRow 
                        key={paper.id}
                        className="group hover:bg-primary/[0.02] cursor-pointer transition-colors duration-500"
                        onClick={() => setSelectedPaperId(paper.id)}
                      >
                        <TableCell className="py-6 px-8">
                          <div className="max-w-xl">
                            <p className="font-bold text-foreground tracking-tight line-clamp-2 leading-snug group-hover:text-primary transition-colors">{paper.title}</p>
                            {paper.venue && (
                              <p className="text-[10px] font-black text-muted-foreground/40 mt-2 uppercase tracking-widest">{paper.venue}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-xs truncate text-muted-foreground font-bold text-[10px] uppercase tracking-wider opacity-60">
                            {Array.isArray(paper.authors) ? paper.authors.slice(0, 2).join(', ') : paper.authors}
                            {Array.isArray(paper.authors) && paper.authors.length > 2 && ' et al.'}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-black text-[10px] text-muted-foreground tracking-widest">{paper.year || '—'}</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col items-center gap-1">
                             <span className="font-black text-foreground text-sm leading-none">{paper.citation_count || 0}</span>
                             <span className="text-[8px] font-black text-muted-foreground/30 uppercase tracking-tighter">Citations</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="info" className="bg-primary/5 uppercase text-[9px] font-black tracking-widest px-3 py-1 border border-primary/10 shadow-inner">
                            {paper.paper_type || 'research'}
                          </Badge>
                        </TableCell>
                        {searchResults !== null && (
                          <TableCell>
                            <div className="flex flex-col items-center gap-1">
                              <span className="font-black text-foreground text-sm leading-none">
                                {score !== null ? `${Math.round(score * 100)}%` : '—'}
                              </span>
                              <span className="text-[8px] font-black text-muted-foreground/30 uppercase tracking-tighter">Similarity</span>
                            </div>
                          </TableCell>
                        )}
                        <TableCell className="px-8">
                          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-all duration-500">
                            {paper.doi && (
                              <a
                                href={`https://doi.org/${paper.doi}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="p-2.5 bg-white dark:bg-stone-800 rounded-xl shadow-lg border border-border/5 text-muted-foreground hover:text-primary transition-all duration-300 hover:scale-110"
                                title="External Link"
                              >
                                <ExternalLink size={14} />
                              </a>
                            )}
                            <button
                              onClick={(e) => { e.stopPropagation(); handleDelete(paper.id); }}
                              disabled={deletingId === paper.id}
                              className="p-2.5 bg-white dark:bg-stone-800 rounded-xl shadow-lg border border-border/5 text-muted-foreground hover:text-error transition-all duration-300 hover:scale-110 disabled:opacity-30"
                              title="Delete Corpus Entry"
                            >
                              {deletingId === paper.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                            </button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : viewMode === 'graph' ? (
              <div className="relative">
                {graphLoading && (
                  <div className="absolute inset-0 z-10 glass rounded-[2.5rem] flex flex-col items-center justify-center gap-4 animate-in fade-in duration-500">
                    <Loader2 className="animate-spin text-primary" size={48} />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-muted-foreground animate-pulse">Mapping Knowledge Vectors...</p>
                  </div>
                )}
                {graphData ? (
                   <KnowledgeGraph 
                    data={graphData} 
                    onNodeClick={(id) => setSelectedPaperId(id)} 
                   />
                ) : (
                   <div className="h-[700px] glass rounded-[2.5rem] flex items-center justify-center border-2 border-dashed border-border/10 italic text-muted-foreground/40 font-black uppercase tracking-[0.3em]">
                      Initializing Topology...
                   </div>
                )}
              </div>
            ) : (
              <div className="relative">
                {citationLoading && (
                  <div className="absolute inset-0 z-10 glass rounded-[2.5rem] flex flex-col items-center justify-center gap-4 animate-in fade-in duration-500">
                    <Loader2 className="animate-spin text-primary" size={48} />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-muted-foreground animate-pulse">Building Citation Graph...</p>
                  </div>
                )}
                {citationData && citationData.nodes.length > 0 ? (
                  <CitationGraph
                    data={citationData}
                    onNodeClick={(id) => setSelectedPaperId(id)}
                    className="h-[700px] glass rounded-[2.5rem] border border-stone-200/10"
                  />
                ) : (
                  <EmptyState
                    icon={<Quote className="w-12 h-12 text-muted-foreground/20" />}
                    title="No citation links found"
                    description="Citation edges are built from paper reference lists. Add references to papers to see the graph."
                  />
                )}
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* Knowledge Card Modal */}
      <Modal
        isOpen={!!selectedPaperId}
        onClose={() => setSelectedPaperId(null)}
        title="Knowledge Node Analysis"
        size="lg"
      >
        {selectedPaperId && (
          <>
            <KnowledgeCard paperId={selectedPaperId} />
            <CommentThread
              projectId={projectId}
              entityType="paper"
              entityId={selectedPaperId}
            />
          </>
        )}
      </Modal>
    </Layout>
  );
}
