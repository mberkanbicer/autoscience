'use client';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Box, Loader2 } from 'lucide-react';

export interface ExperimentData {
  available: boolean;
  run_id?: string;
  success?: boolean;
  status?: string;
  stdout?: string;
  stderr?: string;
  script?: string;
  error_message?: string;
  message?: string;
}

interface ExperimentTelemetryProps {
  experiment: ExperimentData | null;
  loading?: boolean;
  onExport?: () => void;
}

export function ExperimentTelemetry({ experiment, loading, onExport }: ExperimentTelemetryProps) {
  if (loading) {
    return (
      <Card className="p-10 bg-stone-950 border-white/5 rounded-[2.5rem] shadow-2xl flex items-center justify-center">
        <Loader2 className="animate-spin text-success" size={28} />
      </Card>
    );
  }

  if (!experiment?.available) {
    return (
      <Card className="p-10 bg-stone-950 border-white/5 rounded-[2.5rem] shadow-2xl text-center">
        <Box size={48} className="text-stone-600 mx-auto mb-4" />
        <p className="text-sm text-stone-400">
          {experiment?.message || 'No experiment results available for this run yet.'}
        </p>
      </Card>
    );
  }

  const succeeded = experiment.success ?? experiment.status === 'completed';

  return (
    <Card className="p-10 bg-stone-950 border-white/5 rounded-[2.5rem] shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-8 opacity-10">
        <Box size={80} className="text-success" />
      </div>
      <div className="relative z-10 space-y-6 font-mono">
        <div className="flex items-center gap-4 border-b border-white/10 pb-4">
          <Badge className={succeeded ? 'bg-success/20 text-success border-success/40' : 'bg-error/20 text-error border-error/40'}>
            {succeeded ? 'COMPUTE_SUCCESS' : 'COMPUTE_FAILED'}
          </Badge>
          <span className="text-[10px] text-stone-500 uppercase tracking-widest">
            Status: {experiment.status || (succeeded ? 'completed' : 'failed')}
          </span>
        </div>
        <pre className="text-xs text-stone-300 leading-relaxed overflow-x-auto whitespace-pre-wrap">
          {experiment.stdout?.trim() || experiment.stderr?.trim() || experiment.error_message || 'No stdout captured.'}
        </pre>
        {experiment.script && (
          <details className="text-[10px] text-stone-500">
            <summary className="cursor-pointer uppercase tracking-widest font-black text-stone-400">
              View experiment script
            </summary>
            <pre className="mt-3 text-xs text-stone-400 whitespace-pre-wrap">{experiment.script}</pre>
          </details>
        )}
        <div className="pt-4 border-t border-white/10 flex justify-between items-center">
          <span className="text-[9px] text-stone-600 font-bold uppercase tracking-widest">
            Environment: python sandbox
          </span>
          {onExport && experiment.stdout && (
            <Button
              variant="ghost"
              size="sm"
              className="text-[9px] font-black text-primary hover:bg-primary/5 uppercase"
              onClick={onExport}
            >
              Export Output
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}