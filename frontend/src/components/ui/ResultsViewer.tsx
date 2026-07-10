'use client';

import { useState } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { Button } from './Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
import { CheckCircle2, XCircle, Clock, Download, Copy, FileText, Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ExperimentResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  error_message?: string;
  artifacts?: Record<string, any>;
}

interface ResultsViewerProps {
  result: ExperimentResult;
  hypothesisLabel?: string;
  className?: string;
}

export function ResultsViewer({ result, hypothesisLabel, className }: ResultsViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(result.stdout);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const duration = result.duration_ms > 1000
    ? `${(result.duration_ms / 1000).toFixed(1)}s`
    : `${result.duration_ms}ms`;

  return (
    <Card className={cn('overflow-hidden', className)}>
      {/* Header */}
      <div className={cn(
        'flex items-center justify-between px-5 py-4 border-b',
        result.success ? 'border-success/20 bg-success/[0.02]' : 'border-error/20 bg-error/[0.02]'
      )}>
        <div className="flex items-center gap-3">
          {result.success ? (
            <div className="p-2 rounded-lg bg-success/10">
              <CheckCircle2 size={20} className="text-success" />
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-error/10">
              <XCircle size={20} className="text-error" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm">Experiment Result</span>
              <Badge variant={result.success ? 'success' : 'danger'}>
                {result.success ? 'PASSED' : 'FAILED'}
              </Badge>
            </div>
            {hypothesisLabel && (
              <p className="text-xs text-muted-foreground mt-0.5">{hypothesisLabel}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {duration}
          </span>
          <span className="font-mono">Exit: {result.exit_code}</span>
        </div>
      </div>

      {/* Body */}
      <Tabs defaultValue="stdout">
        <div className="px-5 pt-3">
          <TabsList className="bg-transparent border border-border/10 p-0.5">
            <TabsTrigger value="stdout">
              <Terminal size={12} className="mr-1.5" />
              stdout
            </TabsTrigger>
            {result.stderr && (
              <TabsTrigger value="stderr" className="text-error">
                stderr
              </TabsTrigger>
            )}
            {result.artifacts && Object.keys(result.artifacts).length > 0 && (
              <TabsTrigger value="artifacts">
                <FileText size={12} className="mr-1.5" />
                Artifacts
              </TabsTrigger>
            )}
          </TabsList>
        </div>

        <TabsContent value="stdout">
          <div className="px-5 pb-5">
            <div className="flex justify-end gap-2 mb-2">
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                <Copy className="h-3 w-3 mr-1" />
                {copied ? 'Copied!' : 'Copy'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => {
                const blob = new Blob([result.stdout], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'experiment_stdout.txt';
                a.click();
                URL.revokeObjectURL(url);
              }}>
                <Download className="h-3 w-3 mr-1" />
                Download
              </Button>
            </div>
            <pre className="text-xs font-mono bg-stone-50 dark:bg-stone-900 p-4 rounded-xl border border-border/5 overflow-x-auto whitespace-pre-wrap max-h-[400px] overflow-y-auto">
              {result.stdout || <span className="text-muted-foreground/30 italic">No output</span>}
            </pre>
          </div>
        </TabsContent>

        {result.stderr && (
          <TabsContent value="stderr">
            <div className="px-5 pb-5">
              <pre className="text-xs font-mono text-error bg-error/5 p-4 rounded-xl border border-error/10 overflow-x-auto whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                {result.stderr}
              </pre>
            </div>
          </TabsContent>
        )}

        {result.artifacts && Object.keys(result.artifacts).length > 0 && (
          <TabsContent value="artifacts">
            <div className="px-5 pb-5 grid gap-3">
              {Object.entries(result.artifacts).map(([key, value]) => (
                <div key={key} className="bg-stone-50 dark:bg-stone-900 p-4 rounded-xl border border-border/5">
                  <div className="text-xs font-bold text-muted-foreground mb-2 uppercase tracking-wider">{key}</div>
                  <pre className="text-xs font-mono whitespace-pre-wrap">
                    {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </TabsContent>
        )}
      </Tabs>
    </Card>
  );
}
