'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { papersApi } from '@/lib/api';
import { Paper } from '@/lib/types';
import { FileText, ExternalLink, Trash2 } from 'lucide-react';

export default function PapersPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadPapers();
  }, [projectId]);

  const loadPapers = async () => {
    try {
      const data = await papersApi.list(projectId);
      setPapers(data);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this paper?')) return;
    setDeletingId(id);
    try {
      await papersApi.delete(id);
      setPapers(papers.filter(p => p.id !== id));
    } catch (error) {
      console.error('Failed to delete paper:', error);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Papers"
        subtitle={`${papers.length} papers analyzed`}
      />

      <div className="p-6">
        {loading ? (
          <SkeletonTable />
        ) : papers.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-8 h-8 text-gray-400" />}
            title="No papers yet"
            description="Papers will be discovered and analyzed during research runs."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Authors</TableHead>
                <TableHead>Year</TableHead>
                <TableHead>Citations</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {papers.map((paper) => (
                <TableRow key={paper.id}>
                  <TableCell>
                    <div className="max-w-lg">
                      <p className="font-medium text-gray-900">{paper.title}</p>
                      {paper.venue && (
                        <p className="text-xs text-gray-500 mt-1">{paper.venue}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs truncate text-gray-600">
                      {Array.isArray(paper.authors) ? paper.authors.slice(0, 2).join(', ') : paper.authors}
                      {Array.isArray(paper.authors) && paper.authors.length > 2 && '...'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-gray-600">{paper.year || '—'}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium text-gray-900">{paper.citation_count || 0}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="info">{paper.paper_type || 'unknown'}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {paper.doi && (
                        <a
                          href={`https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <ExternalLink size={16} />
                        </a>
                      )}
                      <button
                        onClick={() => handleDelete(paper.id)}
                        disabled={deletingId === paper.id}
                        className="text-red-500 hover:text-red-700 disabled:opacity-50"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </Layout>
  );
}
