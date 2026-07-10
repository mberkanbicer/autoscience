'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { sandboxApi } from '@/lib/api';
import type { PlotlySandboxResult, PowerAnalysisResult } from '@/lib/types';
import { BarChart3, Calculator, Download, Loader2 } from 'lucide-react';

const DEFAULT_PLOTLY = `import plotly.graph_objects as go
fig = go.Figure(data=go.Bar(x=["A", "B", "C"], y=[4, 7, 3]))
fig.update_layout(title="Sample Results", template="plotly_white")
`;

interface AnalysisToolsPanelProps {
  projectId: string;
  runId?: string;
}

export function AnalysisToolsPanel({ projectId, runId }: AnalysisToolsPanelProps) {
  const [effectSize, setEffectSize] = useState('0.5');
  const [powerResult, setPowerResult] = useState<PowerAnalysisResult | null>(null);
  const [powerLoading, setPowerLoading] = useState(false);
  const [plotlyCode, setPlotlyCode] = useState(DEFAULT_PLOTLY);
  const [plotlyResult, setPlotlyResult] = useState<PlotlySandboxResult | null>(null);
  const [plotlyLoading, setPlotlyLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runPowerAnalysis = async () => {
    setPowerLoading(true);
    setError(null);
    try {
      const result = await sandboxApi.powerAnalysis({
        project_id: projectId,
        test_type: 'two_sample_ttest',
        effect_size: parseFloat(effectSize),
      });
      setPowerResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Power analysis failed');
    } finally {
      setPowerLoading(false);
    }
  };

  const runPlotly = async () => {
    setPlotlyLoading(true);
    setError(null);
    try {
      const result = await sandboxApi.plotly({
        project_id: projectId,
        code: plotlyCode,
        title: 'Sandbox Figure',
      });
      setPlotlyResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Plotly sandbox failed');
    } finally {
      setPlotlyLoading(false);
    }
  };

  return (
    <Card className="glass p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Calculator size={18} className="text-primary" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
          Analysis Tools
        </h3>
      </div>

      {error && <p className="text-sm text-error">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Power Analysis
          </p>
          <Input
            label="Effect size (Cohen's d)"
            value={effectSize}
            onChange={(e) => setEffectSize(e.target.value)}
          />
          <Button onClick={runPowerAnalysis} disabled={powerLoading} size="sm">
            {powerLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Compute Sample Size
          </Button>
          {powerResult && (
            <p className="text-sm text-muted-foreground">{powerResult.recommendation}</p>
          )}
        </div>

        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <BarChart3 size={14} /> Plotly Sandbox
          </p>
          <Textarea
            label="Python code (must define fig)"
            value={plotlyCode}
            onChange={(e) => setPlotlyCode(e.target.value)}
            rows={6}
            className="font-mono text-xs"
          />
          <Button onClick={runPlotly} disabled={plotlyLoading} size="sm" variant="secondary">
            {plotlyLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Render Figure
          </Button>
          {plotlyResult?.html && (
            <div
              className="rounded-xl border border-border/10 overflow-hidden bg-white"
              dangerouslySetInnerHTML={{ __html: plotlyResult.html }}
            />
          )}
        </div>
      </div>

      {runId && (
        <div className="pt-4 border-t border-border/10 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Export sandbox run as Jupyter notebook</span>
          <a href={sandboxApi.notebookUrl(runId)} download>
            <Button variant="ghost" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download .ipynb
            </Button>
          </a>
        </div>
      )}
    </Card>
  );
}