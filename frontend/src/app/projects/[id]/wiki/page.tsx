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
import { KnowledgeNote } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { BookOpen, ArrowLeft, Search } from 'lucide-react';

export default function WikiPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [notes, setNotes] = useState<KnowledgeNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState<KnowledgeNote | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadNotes();
  }, [projectId]);

  const loadNotes = async () => {
    try {
      const data = await wikiApi.list(projectId);
      setNotes(data);
    } catch (error) {
      console.error('Failed to load wiki notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupedNotes = notes.reduce((acc, note) => {
    const type = note.note_type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(note);
    return acc;
  }, {} as Record<string, KnowledgeNote[]>);

  const filteredNotes = notes.filter(
    (note) =>
      note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content.toLowerCase().includes(searchQuery.toLowerCase())
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
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="info">{selectedNote.note_type}</Badge>
                </div>
                <h2 className="text-xl font-bold text-gray-900">{selectedNote.title}</h2>
                <p className="text-sm text-gray-500">{formatDate(selectedNote.created_at)}</p>
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
            {/* Search */}
            <div className="relative mb-6">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search wiki..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {searchQuery ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-500">
                  {filteredNotes.length} result{filteredNotes.length !== 1 ? 's' : ''} for &quot;{searchQuery}&quot;
                </p>
                {filteredNotes.map((note) => (
                  <Card
                    key={note.id}
                    hover
                    className="p-6 cursor-pointer"
                    onClick={() => setSelectedNote(note)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="info" size="sm">{note.note_type}</Badge>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{note.title}</h3>
                        <p className="text-gray-600 text-sm line-clamp-2">{note.content}</p>
                      </div>
                      <span className="text-sm text-gray-400">{formatDate(note.created_at)}</span>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Tabs defaultValue={noteTypes[0] || 'all'}>
                <TabsList>
                  {noteTypes.map((type) => (
                    <TabsTrigger key={type} value={type}>
                      {type.replace('_', ' ')} ({groupedNotes[type].length})
                    </TabsTrigger>
                  ))}
                </TabsList>

                {noteTypes.map((type) => (
                  <TabsContent key={type} value={type}>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {groupedNotes[type].map((note) => (
                        <Card
                          key={note.id}
                          hover
                          className="p-6 cursor-pointer"
                          onClick={() => setSelectedNote(note)}
                        >
                          <h3 className="font-semibold text-gray-900 mb-2">{note.title}</h3>
                          <p className="text-sm text-gray-600 line-clamp-3 mb-3">{note.content}</p>
                          <span className="text-xs text-gray-400">{formatDate(note.created_at)}</span>
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
