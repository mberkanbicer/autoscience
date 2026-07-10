'use client';

import { useState } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { Modal } from './Modal';
import { Download, Eye, ImageIcon, TableIcon, FileJson, FileText, FileType, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';

export interface Artifact {
  id: string;
  name: string;
  type: 'figure' | 'table' | 'json' | 'csv' | 'log' | 'other';
  content?: string;
  url?: string;
  created_at: string;
  size?: number;
  description?: string;
}

interface ArtifactGalleryProps {
  artifacts: Artifact[];
  projectId: string;
  runId?: string;
  className?: string;
  onDelete?: (artifactId: string) => void;
}

const TYPE_ICONS = {
  figure: <ImageIcon size={20} />,
  table: <TableIcon size={20} />,
  json: <FileJson size={20} />,
  csv: <FileType size={20} />,
  log: <FileText size={20} />,
  other: <FileText size={20} />,
};

const TYPE_COLORS = {
  figure: 'text-primary bg-primary/10 border-primary/20',
  table: 'text-tertiary bg-tertiary/10 border-tertiary/20',
  json: 'text-success bg-success/10 border-success/20',
  csv: 'text-warning bg-warning/10 border-warning/20',
  log: 'text-muted-foreground bg-muted/30 border-muted/40',
  other: 'text-muted-foreground bg-muted/30 border-muted/40',
};

export function ArtifactGallery({ artifacts, projectId, runId, className, onDelete }: ArtifactGalleryProps) {
  const [previewArtifact, setPreviewArtifact] = useState<Artifact | null>(null);

  if (artifacts.length === 0) {
    return (
      <Card className={cn('p-12 text-center', className)}>
        <div className="p-4 rounded-2xl bg-muted/30 w-fit mx-auto mb-4">
          <ImageIcon size={32} className="text-muted-foreground/30" />
        </div>
        <h3 className="font-bold text-muted-foreground mb-1">No Artifacts Yet</h3>
        <p className="text-sm text-muted-foreground/50 max-w-md mx-auto">
          Run an experiment to generate figures, tables, and data exports that will appear here.
        </p>
      </Card>
    );
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <>
      <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4', className)}>
        {artifacts.map((artifact) => (
          <Card key={artifact.id} hover className="group relative overflow-hidden border-border/10">
            {/* Type icon */}
            <div className={cn(
              'p-4 flex items-center justify-center border-b border-border/5',
              TYPE_COLORS[artifact.type]?.split(' ')[1] || 'bg-muted/20'
            )}>
              <div className={cn(
                'p-3 rounded-2xl border',
                TYPE_COLORS[artifact.type]
              )}>
                {TYPE_ICONS[artifact.type] || TYPE_ICONS.other}
              </div>
            </div>

            {/* Info */}
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="min-w-0 flex-1">
                  <h4 className="font-bold text-sm truncate">{artifact.name}</h4>
                  <p className="text-xs text-muted-foreground/50 mt-0.5">{formatDate(artifact.created_at)}</p>
                </div>
                <Badge variant="default" className="text-[9px] ml-2">
                  {artifact.type}
                </Badge>
              </div>

              {artifact.description && (
                <p className="text-xs text-muted-foreground/70 line-clamp-2 mb-3">{artifact.description}</p>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1 text-[9px]"
                  onClick={() => setPreviewArtifact(artifact)}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  Preview
                </Button>
                {artifact.url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(artifact.url, '_blank')}
                  >
                    <Download className="h-3 w-3" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(artifact.id)}
                    className="text-error hover:text-error"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Preview Modal */}
      <Modal
        isOpen={previewArtifact !== null}
        onClose={() => setPreviewArtifact(null)}
        title={previewArtifact?.name}
        size="lg"
      >
        {previewArtifact && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <Badge variant="default">{previewArtifact.type}</Badge>
              {previewArtifact.size && <span>{formatSize(previewArtifact.size)}</span>}
              <span>{formatDate(previewArtifact.created_at)}</span>
            </div>

            {previewArtifact.type === 'figure' && previewArtifact.url && (
              <div className="bg-stone-50 dark:bg-stone-900 rounded-xl p-4 flex items-center justify-center min-h-[200px]">
                <img
                  src={previewArtifact.url}
                  alt={previewArtifact.name}
                  className="max-w-full max-h-[500px] object-contain rounded-lg"
                />
              </div>
            )}

            {previewArtifact.content && (
              <pre className="text-xs font-mono bg-stone-50 dark:bg-stone-900 p-4 rounded-xl border border-border/5 overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre-wrap">
                {previewArtifact.content}
              </pre>
            )}

            {previewArtifact.url && (
              <Button
                variant="primary"
                className="w-full"
                onClick={() => window.open(previewArtifact.url, '_blank')}
              >
                <Download className="h-4 w-4 mr-2" />
                Download {previewArtifact.name}
              </Button>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}
