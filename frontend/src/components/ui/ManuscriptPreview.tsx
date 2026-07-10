'use client';

import { useMemo } from 'react';
import { latexToPreviewHtml } from '@/lib/latexPreview';
import { cn } from '@/lib/utils';

interface ManuscriptPreviewProps {
  latex: string;
  className?: string;
}

export function ManuscriptPreview({ latex, className }: ManuscriptPreviewProps) {
  const html = useMemo(() => latexToPreviewHtml(latex), [latex]);

  if (!html) {
    return (
      <p className="text-stone-500 italic text-sm">
        No preview content yet. Add sections and paragraphs in the LaTeX editor.
      </p>
    );
  }

  return (
    <div
      className={cn(
        'prose prose-stone max-w-none manuscript-preview',
        '[&_h2]:text-xl [&_h2]:font-bold [&_h2]:mt-6 [&_h2]:mb-3',
        '[&_h3]:text-lg [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-2',
        '[&_p]:text-stone-700 [&_p]:leading-relaxed [&_p]:mb-4',
        className
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}