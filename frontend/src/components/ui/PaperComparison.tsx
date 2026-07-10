'use client';

import { useEffect, useState } from 'react';
import { papersApi } from '@/lib/api';
import type { Paper, PaperComparison as PaperComparisonData } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { EmptyState } from '@/components/ui/EmptyState';
import { Loader2, GitCompare, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PaperComparisonProps {
  projectId: string;
}

const COMPARE_ROWS = [
  { key: 'problem', label: 'Problem' },
  { key: 'method', label: 'Method' },
  { key: 'findings', label: 'Findings' },
  { key: 'limitations', label: 'Limitations' },
] as const;

function formatCellValue(value: unknown): string {
  if (value == null || value === '') return '—';
  if (Array.isArray(value)) {
    return value.length ? value.join('; ') : '—';
  }
  return String(value);
}

export function PaperComparison({ projectId }: PaperComparisonProps) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<PaperComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    papersApi
      .list(projectId)
      .then(setPapers)
      .catch(() => setError('Failed to load papers'))
      .finally(() => setLoading(false));
  }, [projectId]);

  const togglePaper = (id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
    setComparison(null);
    setError(null);
  };

  const runComparison = async () => {
    if (selectedIds.length < 2) {
      setError('Select at least 2 papers to compare');
      return;
    }
    setComparing(true);
    setError(null);
    try {
      const result = await papersApi.compare(selectedIds);
      setComparison(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (papers.length < 2) {
    return (
      <EmptyState
        icon={<GitCompare className="w-12 h-12 text-muted-foreground/20" />}
        title="Not enough papers"
        description="Add at least two papers with analysis to enable comparison."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6 border border-stone-200/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold">Select Papers</h3>
            <p className="text-sm text-muted-foreground">
              Choose 2–3 papers for side-by-side analysis
            </p>
          </div>
          <Badge variant="info">{selectedIds.length} / 3 selected</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          {papers.map((paper) => {
            const selected = selectedIds.includes(paper.id);
            return (
              <button
                key={paper.id}
                type="button"
                onClick={() => togglePaper(paper.id)}
                className={cn(
                  'text-left p-4 rounded-xl border transition-all duration-300',
                  selected
                    ? 'border-primary bg-primary/5 shadow-md'
                    : 'border-border/20 hover:border-primary/30 hover:bg-white/40'
                )}
              >
                <div className="flex items-start gap-2">
                  <div
                    className={cn(
                      'mt-0.5 h-5 w-5 rounded-md border flex items-center justify-center shrink-0',
                      selected ? 'bg-primary border-primary text-stone-900' : 'border-border/40'
                    )}
                  >
                    {selected && <Check size={12} />}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-sm line-clamp-2">{paper.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {paper.year ?? '—'} · {paper.authors?.slice(0, 2).join(', ')}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <Button onClick={runComparison} disabled={selectedIds.length < 2 || comparing}>
          {comparing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Comparing…
            </>
          ) : (
            <>
              <GitCompare className="h-4 w-4 mr-2" />
              Compare Selected
            </>
          )}
        </Button>

        {error && <p className="text-sm text-error mt-3">{error}</p>}
      </div>

      {comparison && comparison.papers.length > 0 && (
        <div className="glass rounded-[2.5rem] overflow-hidden border border-stone-200/10 shadow-2xl">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="py-4 px-6 text-[10px] font-black uppercase tracking-widest w-36">
                  Dimension
                </TableHead>
                {comparison.papers.map((paper) => (
                  <TableHead
                    key={paper.paper_id}
                    className="py-4 px-4 text-[10px] font-black uppercase tracking-widest"
                  >
                    <div className="max-w-xs">
                      <p className="line-clamp-2 normal-case font-bold text-sm">{paper.title}</p>
                      <span className="text-muted-foreground">{paper.year ?? '—'}</span>
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {COMPARE_ROWS.map((row) => (
                <TableRow key={row.key}>
                  <TableCell className="py-4 px-6 font-bold text-sm align-top">{row.label}</TableCell>
                  {comparison.papers.map((paper) => (
                    <TableCell key={`${paper.paper_id}-${row.key}`} className="py-4 px-4 align-top">
                      <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {formatCellValue(paper[row.key as keyof typeof paper])}
                      </p>
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {comparison.summary.shared_limitations.length > 0 && (
            <div className="p-6 border-t border-border/10 bg-stone-50/50 dark:bg-stone-900/30">
              <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">
                Shared Limitations
              </p>
              <div className="flex flex-wrap gap-2">
                {comparison.summary.shared_limitations.map((item) => (
                  <Badge key={item} variant="warning">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}