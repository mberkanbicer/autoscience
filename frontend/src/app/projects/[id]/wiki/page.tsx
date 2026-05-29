'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { wikiApi } from '@/lib/api';
import { KnowledgeNote } from '@/lib/types';
import { formatDate } from '@/lib/utils';

export default function WikiPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [notes, setNotes] = useState<KnowledgeNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNote, setSelectedNote] = useState<KnowledgeNote | null>(null);

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

  return (
    <Layout>
      <Header title="Research Wiki" />

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : notes.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No wiki notes found</div>
        ) : selectedNote ? (
          <div>
            <button
              onClick={() => setSelectedNote(null)}
              className="mb-4 text-blue-600 hover:text-blue-800"
            >
              ← Back to wiki
            </button>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                  {selectedNote.note_type}
                </span>
                <span className="text-sm text-gray-500">
                  {formatDate(selectedNote.created_at)}
                </span>
              </div>
              <h2 className="text-2xl font-bold mb-4">{selectedNote.title}</h2>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm">
                  {selectedNote.content}
                </pre>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedNotes).map(([type, typeNotes]) => (
              <div key={type}>
                <h2 className="text-xl font-semibold mb-4 capitalize">
                  {type.replace('_', ' ')}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {typeNotes.map((note) => (
                    <div
                      key={note.id}
                      className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
                      onClick={() => setSelectedNote(note)}
                    >
                      <h3 className="font-medium mb-2">{note.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {note.content}
                      </p>
                      <div className="text-xs text-gray-500 mt-2">
                        {formatDate(note.created_at)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
