'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { wikiApi } from '@/lib/api';
import { KnowledgeNote, WikiSemanticResult, WikiGraph } from '@/lib/types';
import { KnowledgeGraph } from '@/components/ui/KnowledgeGraph';
import { formatDate } from '@/lib/utils';
import { useArtifact } from '@/lib/ArtifactContext';
import { BookOpen, ArrowLeft, ArrowRight, Search, Trash2, Box, Sparkles, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

type SearchMode = 'text' | 'semantic' | 'graph';

export default function WikiPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { openArtifact } = useArtifact();
  const [notes, setNotes] = useState<KnowledgeNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState<KnowledgeNote | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchMode, setSearchMode] = useState<SearchMode>('text');
  const [semanticResults, setSemanticResults] = useState<WikiSemanticResult[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [wikiGraph, setWikiGraph] = useState<WikiGraph | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);

  useEffect(() => {
    loadNotes();
  }, [projectId]);

  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (searchMode === 'graph') {
      return;
    }

    const minLength = searchMode === 'semantic' ? 3 : 2;

    if (trimmed.length < minLength) {
      setSemanticResults(null);
      setSearchError(null);
      if (trimmed.length === 0) loadNotes();
      return;
    }

    const timer = setTimeout(async () => {
      setSearchLoading(true);
      setSearchError(null);
      try {
        if (searchMode === 'semantic') {
          const response = await wikiApi.semanticSearch(projectId, trimmed);
          setSemanticResults(response.results);
          setNotes([]);
        } else {
          const data = await wikiApi.search(projectId, trimmed);
          setSemanticResults(null);
          setNotes(data);
        }
      } catch (error) {
        console.error('Wiki search failed:', error);
        setSearchError(
          searchMode === 'semantic'
            ? 'Semantic search unavailable. Ensure wiki notes are embedded.'
            : 'Text search failed.',
        );
      } finally {
        setSearchLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, projectId, searchMode]);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await wikiApi.list(projectId);
      setNotes(data);
    } catch (error) {
      console.error('Failed to load wiki notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!window.confirm('Are you sure you want to delete this wiki note? This action cannot be undone.')) return;
    try {
      setDeletingId(noteId);
      await wikiApi.delete(noteId);
      setNotes(prev => prev.filter(n => n.id !== noteId));
      if (selectedNote?.id === noteId) setSelectedNote(null);
    } catch (error) {
      console.error('Failed to delete wiki note:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const groupedNotes = notes.reduce((acc, note) => {
    const type = note.note_type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(note);
    return acc;
  }, {} as Record<string, KnowledgeNote[]>);

  const semanticNoteCards: KnowledgeNote[] =
    semanticResults?.map((result) => ({
      id: result.note_id,
      project_id: projectId,
      note_type: result.note_type,
      run_id: result.run_id,
      title: result.title,
      content: result.snippet,
      linked_notes: [],
      created_at: new Date().toISOString(),
    })) ?? [];

  const displayNotes =
    searchMode === 'semantic' && semanticResults !== null
      ? semanticNoteCards
      : searchQuery.trim().length >= 2
        ? notes
        : notes.filter(
            (note) =>
              (note.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
              (note.content || '').toLowerCase().includes(searchQuery.toLowerCase())
          );

  const noteTypes = Object.keys(groupedNotes);

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Wiki"
        subtitle={`${notes.length} notes documented`}
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : selectedNote ? (
          <div>
            <div className="flex items-center gap-4 mb-6">
              <Button
                variant="ghost"
                onClick={() => setSelectedNote(null)}
              >
                <ArrowLeft size={18} className="mr-2" />
                Back to wiki
              </Button>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge variant="info">{selectedNote.note_type}</Badge>
                  {selectedNote.run_id && (
                    <Badge variant="default" className="text-[9px] uppercase tracking-widest">
                      Run {selectedNote.run_id.slice(0, 8)}
                    </Badge>
                  )}
                </div>
                <h2 className="text-xl font-bold text-gray-900">{selectedNote.title}</h2>
                <p className="text-sm text-gray-500">{formatDate(selectedNote.created_at)}</p>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => openArtifact({
                  id: selectedNote.id,
                  type: 'latex',
                  title: selectedNote.title || 'Note LaTeX',
                  content: selectedNote.content || ''
                })}>
                  <Box size={16} className="mr-2" />
                  Artifact
                </Button>
                <Button variant="danger" size="sm" onClick={() => handleDeleteNote(selectedNote.id)}>
                  <Trash2 size={16} className="mr-2" />
                  Delete
                </Button>
              </div>
            </div>
            <Card className="p-8">
              <div className="prose prose-gray max-w-none">
                <ReactMarkdown>{selectedNote.content}</ReactMarkdown>
              </div>
            </Card>
          </div>
        ) : notes.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-8 h-8 text-gray-400" />}
            title="No wiki notes yet"
            description="The wiki is automatically populated with insights from your research."
          />
        ) : (
          <>
            {searchLoading && (
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-center mb-4 animate-pulse">
                Searching wiki...
              </p>
            )}

            <div className="max-w-2xl mx-auto mb-10 space-y-4">
              <div className="flex items-center justify-center gap-2 p-1 bg-stone-100 dark:bg-stone-900 rounded-2xl border border-border/5 shadow-inner w-fit mx-auto">
                <button
                  type="button"
                  onClick={() => {
                    setSearchMode('text');
                    setSemanticResults(null);
                  }}
                  className={cn(
                    'px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2',
                    searchMode === 'text'
                      ? 'bg-white dark:bg-stone-800 text-primary shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Search size={14} />
                  Text
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSearchMode('semantic');
                    setSemanticResults(null);
                  }}
                  className={cn(
                    'px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2',
                    searchMode === 'semantic'
                      ? 'bg-white dark:bg-stone-800 text-primary shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Sparkles size={14} />
                  Semantic
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    setSearchMode('graph');
                    setGraphLoading(true);
                    setSearchError(null);
                    try {
                      const graph = await wikiApi.graph(projectId);
                      setWikiGraph(graph);
                    } catch (error) {
                      console.error('Wiki graph failed:', error);
                      setSearchError('Failed to load knowledge graph.');
                    } finally {
                      setGraphLoading(false);
                    }
                  }}
                  className={cn(
                    'px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2',
                    searchMode === 'graph'
                      ? 'bg-white dark:bg-stone-800 text-primary shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <GitBranch size={14} />
                  Graph
                </button>
              </div>

              <div className="relative group">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground/40 group-focus-within:text-primary transition-colors" size={20} />
                <input
                  type="text"
                  placeholder={
                    searchMode === 'semantic'
                      ? 'Semantic search across wiki notes...'
                      : 'Query Research Repository...'
                  }
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 glass border-border/10 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:bg-white/80 transition-all duration-500 shadow-lg placeholder:text-muted-foreground/30 font-medium"
                />
              </div>

              {searchError && (
                <p className="text-sm text-muted-foreground text-center">{searchError}</p>
              )}
            </div>

            {searchMode === 'graph' ? (
              <div className="animate-in fade-in duration-700">
                {graphLoading ? (
                  <p className="text-center text-muted-foreground">Loading knowledge graph...</p>
                ) : wikiGraph && wikiGraph.nodes.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] px-1">
                      {wikiGraph.stats.note_count} notes · {wikiGraph.stats.edge_count} links · {wikiGraph.stats.run_count} runs
                    </p>
                    <KnowledgeGraph
                      data={{
                        nodes: wikiGraph.nodes.map((n) => ({
                          id: n.id,
                          title: n.title,
                          paper_type: n.note_type === 'paper' ? 'research' : 'review',
                          citation_count: 0,
                        })),
                        edges: wikiGraph.edges.map((e) => ({
                          id: e.id,
                          source: e.source,
                          target: e.target,
                          type: e.type === 'link' ? 'citation' : 'conflict',
                          label: e.label,
                        })),
                      }}
                      onNodeClick={async (nodeId) => {
                        try {
                          const note = await wikiApi.get(nodeId);
                          setSelectedNote(note);
                        } catch (error) {
                          console.error('Failed to open wiki note:', error);
                        }
                      }}
                    />
                  </div>
                ) : (
                  <EmptyState
                    icon={<GitBranch className="w-8 h-8 text-gray-400" />}
                    title="No graph data yet"
                    description="Add wiki notes across runs to build the cross-run knowledge graph."
                  />
                )}
              </div>
            ) : (searchQuery && (searchMode === 'text' ? searchQuery.trim().length >= 2 : searchQuery.trim().length >= 3)) ? (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] px-1">
                  {displayNotes.length} Correlation{displayNotes.length !== 1 ? 's' : ''} found for &quot;{searchQuery}&quot;
                </p>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {displayNotes.map((note) => (
                    <Card
                      key={note.id}
                      hover
                      className="p-8 cursor-pointer group transition-all duration-500 hover:scale-[1.02]"
                      onClick={() => setSelectedNote(note)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-4">
                            <Badge variant="info" className="bg-primary/5 uppercase text-[9px] font-bold tracking-widest">{note.note_type}</Badge>
                            <span className="text-[10px] font-bold text-muted-foreground/30 uppercase tracking-widest">{formatDate(note.created_at)}</span>
                          </div>
                          <h3 className="text-xl font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">{note.title}</h3>
                          <p className="text-muted-foreground text-sm font-medium line-clamp-2 leading-relaxed">{note.content}</p>
                          {searchMode === 'semantic' && semanticResults && (
                            <p className="text-[10px] font-black text-primary/60 mt-2 uppercase tracking-widest">
                              Match {Math.round((semanticResults.find((r) => r.note_id === note.id)?.score ?? 0) * 100)}%
                            </p>
                          )}
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteNote(note.id); }}
                          className="p-2 rounded-lg hover:bg-error/10 text-error shrink-0 ml-4 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0"
                          title="Purge Note"
                          disabled={deletingId === note.id}
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Tabs defaultValue={noteTypes[0] || 'all'}>
                <TabsList className="bg-white/40 p-1 rounded-2xl mb-8">
                  {noteTypes.map((type) => (
                    <TabsTrigger key={type} value={type} className="text-[10px] font-bold uppercase tracking-widest px-6">
                      {type.replace('_', ' ')}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {noteTypes.map((type) => (
                  <TabsContent key={type} value={type} className="animate-in fade-in duration-700">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {groupedNotes[type].map((note) => (
                        <Card
                          key={note.id}
                          hover
                          className="p-8 cursor-pointer group transition-all duration-500 hover:scale-[1.02]"
                          onClick={() => setSelectedNote(note)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-lg font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">{note.title}</h3>
                              <p className="text-sm text-muted-foreground font-medium line-clamp-3 mb-6 leading-relaxed">{note.content}</p>
                              <div className="flex items-center justify-between pt-4 border-t border-border/5">
                                 <span className="text-[10px] font-bold text-muted-foreground/30 uppercase tracking-widest">{formatDate(note.created_at)}</span>
                                 <div className="p-1.5 bg-primary/5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:translate-x-1">
                                    <ArrowRight size={14} className="text-primary/60" />
                                 </div>
                              </div>
                            </div>
                            <button
                              onClick={(e) => { e.stopPropagation(); handleDeleteNote(note.id); }}
                              className="p-1.5 rounded-lg hover:bg-error/10 text-error shrink-0 ml-2 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0"
                              title="Delete note"
                              disabled={deletingId === note.id}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
