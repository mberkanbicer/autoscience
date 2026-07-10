'use client';

import { useState } from 'react';
import { Button } from './Button';
import { Card } from './Card';
import { Textarea } from './Input';
import { Play, Save, RotateCcw, Terminal, Download, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SandboxEditorProps {
  hypothesisId: string;
  projectId: string;
  initialCode?: string;
  onRun?: (code: string) => Promise<SandboxOutput>;
  onSave?: (code: string) => void;
}

export interface SandboxOutput {
  success: boolean;
  stdout: string;
  stderr: string;
  duration_ms: number;
  error_message?: string;
}

export function SandboxEditor({ hypothesisId, projectId, initialCode, onRun, onSave }: SandboxEditorProps) {
  const [code, setCode] = useState(initialCode || 'import json\nimport numpy as np\n\n# Experiment code here\nprint("Ready")\n');
  const [output, setOutput] = useState<SandboxOutput | null>(null);
  const [running, setRunning] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    setOutput(null);
    try {
      if (onRun) {
        const result = await onRun(code);
        setOutput(result);
      } else {
        // Default: send to sandbox API
        const response = await fetch('/api/v1/sandbox/plotly', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_id: projectId, code, title: 'Sandbox Run' }),
        });
        if (response.ok) {
          const data = await response.json();
          setOutput({
            success: true,
            stdout: JSON.stringify(data, null, 2),
            stderr: '',
            duration_ms: 0,
          });
        } else {
          setOutput({
            success: false,
            stdout: '',
            stderr: 'API request failed',
            duration_ms: 0,
            error_message: `HTTP ${response.status}`,
          });
        }
      }
    } catch (err) {
      setOutput({
        success: false,
        stdout: '',
        stderr: String(err),
        duration_ms: 0,
        error_message: String(err),
      });
    } finally {
      setRunning(false);
    }
  };

  const handleSave = () => {
    onSave?.(code);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setCode(initialCode || 'import json\nimport numpy as np\n\n# Experiment code here\nprint("Ready")\n');
    setOutput(null);
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-primary" />
          <span className="text-xs font-black uppercase tracking-widest text-muted-foreground">Python Experiment Sandbox</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleReset}>
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset
          </Button>
          <Button variant="secondary" size="sm" onClick={handleSave}>
            <Save className="h-3.5 w-3.5 mr-1" />
            {saved ? 'Saved!' : 'Save'}
          </Button>
          <Button size="sm" onClick={handleRun} disabled={running}>
            {running ? (
              <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5 mr-1" />
            )}
            Run
          </Button>
        </div>
      </div>

      {/* Code editor */}
      <div className="relative">
        <div className="absolute top-0 left-0 w-12 h-full bg-stone-50 dark:bg-stone-900 border-r border-border/10 flex flex-col items-center pt-4 text-[10px] font-mono text-muted-foreground/30 select-none">
          {code.split('\n').map((_, i) => (
            <span key={i} className="leading-6">{i + 1}</span>
          ))}
        </div>
        <Textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="min-h-[300px] font-mono text-sm resize-y pl-14 bg-stone-50/50 dark:bg-stone-900/50 border border-border/10 rounded-xl"
          spellCheck={false}
        />
      </div>

      {/* Output */}
      {output && (
        <Card className={cn(
          'overflow-hidden border',
          output.success ? 'border-success/30' : 'border-error/30'
        )}>
          <div className={cn(
            'flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider',
            output.success ? 'bg-success/5 text-success' : 'bg-error/5 text-error'
          )}>
            {output.success ? (
              <CheckCircle2 size={14} />
            ) : (
              <AlertCircle size={14} />
            )}
            {output.success ? 'Execution successful' : 'Execution failed'}
            {output.duration_ms > 0 && (
              <span className="ml-auto text-muted-foreground/50 font-mono text-[10px]">
                {output.duration_ms}ms
              </span>
            )}
          </div>
          <div className="p-4">
            {output.stdout && (
              <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap bg-stone-50 dark:bg-stone-900 p-3 rounded-lg border border-border/5 mb-2">
                {output.stdout}
              </pre>
            )}
            {output.stderr && (
              <pre className="text-xs font-mono text-error whitespace-pre-wrap bg-error/5 p-3 rounded-lg border border-error/10">
                {output.stderr}
              </pre>
            )}
            {output.error_message && !output.stderr && (
              <p className="text-xs text-error font-medium">{output.error_message}</p>
            )}
            {!output.stdout && !output.stderr && !output.error_message && (
              <p className="text-xs text-muted-foreground/50 font-mono">[No output]</p>
            )}
          </div>
          {output.stdout && (
            <div className="px-4 py-2 border-t border-border/5">
              <Button variant="ghost" size="sm" onClick={() => {
                const blob = new Blob([output.stdout], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `experiment_output.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }}>
                <Download className="h-3 w-3 mr-1" />
                Download Output
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
