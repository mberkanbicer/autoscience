'use client';

import { useState } from 'react';
import { Card } from './Card';
import { Button } from './Button';
import { Badge } from './Badge';
import { Input, Textarea, Select } from './Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
import { Modal } from './Modal';
import { Plus, Trash2, GripVertical, FlaskConical, BarChart3, Database, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ValidationStep {
  id: string;
  name: string;
  description: string;
  type: 'data_prep' | 'statistical_test' | 'visualization' | 'comparison' | 'interpretation';
  status: 'pending' | 'running' | 'completed' | 'failed';
  expected_outcome: string;
}

export interface ValidationPlan {
  id?: string;
  hypothesis_id: string;
  hypothesis_statement: string;
  steps: ValidationStep[];
  metrics: string[];
  baselines: string[];
  datasets: string[];
  experimental_design: string;
  statistical_tests: string[];
  feasibility_score?: number;
  cost_estimate?: number;
}

interface ValidationPlanEditorProps {
  plan?: ValidationPlan;
  hypothesisId: string;
  hypothesisStatement: string;
  onSave?: (plan: ValidationPlan) => void;
  onGenerateScript?: (hypothesisId: string) => void;
  className?: string;
}

export function ValidationPlanEditor({
  plan,
  hypothesisId,
  hypothesisStatement,
  onSave,
  onGenerateScript,
  className,
}: ValidationPlanEditorProps) {
  const [steps, setSteps] = useState<ValidationStep[]>(plan?.steps || []);
  const [metrics, setMetrics] = useState<string[]>(plan?.metrics || ['accuracy', 'f1_score', 'latency']);
  const [baselines, setBaselines] = useState<string[]>(plan?.baselines || []);
  const [datasets, setDatasets] = useState<string[]>(plan?.datasets || []);
  const [design, setDesign] = useState(plan?.experimental_design || '');
  const [newMetric, setNewMetric] = useState('');
  const [newBaseline, setNewBaseline] = useState('');
  const [newDataset, setNewDataset] = useState('');
  const [showAddStep, setShowAddStep] = useState(false);

  const addStep = (step: ValidationStep) => {
    setSteps(prev => [...prev, step]);
    setShowAddStep(false);
  };

  const removeStep = (id: string) => {
    setSteps(prev => prev.filter(s => s.id !== id));
  };

  const addListItem = (list: string[], setter: (v: string[]) => void, value: string) => {
    if (value.trim()) {
      setter([...list, value.trim()]);
    }
  };

  const removeListItem = (list: string[], setter: (v: string[]) => void, index: number) => {
    setter(list.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    onSave?.({
      hypothesis_id: hypothesisId,
      hypothesis_statement: hypothesisStatement,
      steps,
      metrics,
      baselines,
      datasets,
      experimental_design: design,
      statistical_tests: metrics,
    });
  };

  const completedSteps = steps.filter(s => s.status === 'completed').length;
  const progress = steps.length > 0 ? Math.round((completedSteps / steps.length) * 100) : 0;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Hypothesis header */}
      <Card className="p-5 border-primary/20 bg-primary/[0.02]">
        <div className="flex items-start gap-3">
          <FlaskConical size={20} className="text-primary mt-0.5 shrink-0" />
          <div>
            <h3 className="font-bold text-sm mb-1">Hypothesis</h3>
            <p className="text-sm text-foreground/80 leading-relaxed">{hypothesisStatement}</p>
          </div>
        </div>
      </Card>

      <Tabs defaultValue="steps">
        <TabsList>
          <TabsTrigger value="steps">
            Steps {steps.length > 0 && `(${steps.length})`}
          </TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
        </TabsList>

        {/* Steps Tab */}
        <TabsContent value="steps">
          <div className="space-y-3">
            {/* Progress bar */}
            {steps.length > 0 && (
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-success rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-muted-foreground">{progress}%</span>
              </div>
            )}

            {/* Step list */}
            {steps.map((step, i) => (
              <Card key={step.id} className="p-4 border-border/10">
                <div className="flex items-start gap-3">
                  <div className="flex items-center gap-2 pt-1">
                    <GripVertical size={14} className="text-muted-foreground/30 cursor-grab" />
                    <span className="text-xs font-bold text-muted-foreground/50 w-5">{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-sm">{step.name}</span>
                      <Badge variant={
                        step.status === 'completed' ? 'success' :
                        step.status === 'failed' ? 'danger' :
                        step.status === 'running' ? 'info' : 'default'
                      } className="text-[9px]">
                        {step.status}
                      </Badge>
                      <Badge variant="default" className="text-[9px]">{step.type.replace('_', ' ')}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground/70">{step.description}</p>
                    {step.expected_outcome && (
                      <p className="text-xs text-muted-foreground/50 mt-1">
                        Expected: {step.expected_outcome}
                      </p>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeStep(step.id)} className="text-error">
                    <Trash2 size={14} />
                  </Button>
                </div>
              </Card>
            ))}

            <Button variant="secondary" onClick={() => setShowAddStep(true)} className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              Add Validation Step
            </Button>
          </div>
        </TabsContent>

        {/* Config Tab */}
        <TabsContent value="config">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Metrics */}
            <Card className="p-4 border-border/10">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 size={16} className="text-primary" />
                <h4 className="font-bold text-xs uppercase tracking-wider">Metrics</h4>
              </div>
              <div className="space-y-2">
                {metrics.map((m, i) => (
                  <div key={i} className="flex items-center justify-between bg-stone-50 dark:bg-stone-900 px-3 py-2 rounded-lg text-xs">
                    <span className="font-mono">{m}</span>
                    <button onClick={() => removeListItem(metrics, setMetrics, i)} className="text-error/50 hover:text-error">
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
                <div className="flex gap-2">
                  <Input
                    value={newMetric}
                    onChange={e => setNewMetric(e.target.value)}
                    placeholder="Add metric..."
                    className="text-xs py-2"
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        addListItem(metrics, setMetrics, newMetric);
                        setNewMetric('');
                      }
                    }}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { addListItem(metrics, setMetrics, newMetric); setNewMetric(''); }}
                  >
                    <Plus size={14} />
                  </Button>
                </div>
              </div>
            </Card>

            {/* Baselines */}
            <Card className="p-4 border-border/10">
              <div className="flex items-center gap-2 mb-3">
                <ArrowRight size={16} className="text-tertiary" />
                <h4 className="font-bold text-xs uppercase tracking-wider">Baselines</h4>
              </div>
              <div className="space-y-2">
                {baselines.map((b, i) => (
                  <div key={i} className="flex items-center justify-between bg-stone-50 dark:bg-stone-900 px-3 py-2 rounded-lg text-xs">
                    <span>{b}</span>
                    <button onClick={() => removeListItem(baselines, setBaselines, i)} className="text-error/50 hover:text-error">
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
                <div className="flex gap-2">
                  <Input
                    value={newBaseline}
                    onChange={e => setNewBaseline(e.target.value)}
                    placeholder="Add baseline..."
                    className="text-xs py-2"
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        addListItem(baselines, setBaselines, newBaseline);
                        setNewBaseline('');
                      }
                    }}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { addListItem(baselines, setBaselines, newBaseline); setNewBaseline(''); }}
                  >
                    <Plus size={14} />
                  </Button>
                </div>
              </div>
            </Card>

            {/* Datasets */}
            <Card className="p-4 border-border/10">
              <div className="flex items-center gap-2 mb-3">
                <Database size={16} className="text-success" />
                <h4 className="font-bold text-xs uppercase tracking-wider">Datasets</h4>
              </div>
              <div className="space-y-2">
                {datasets.map((d, i) => (
                  <div key={i} className="flex items-center justify-between bg-stone-50 dark:bg-stone-900 px-3 py-2 rounded-lg text-xs">
                    <span>{d}</span>
                    <button onClick={() => removeListItem(datasets, setDatasets, i)} className="text-error/50 hover:text-error">
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
                <div className="flex gap-2">
                  <Input
                    value={newDataset}
                    onChange={e => setNewDataset(e.target.value)}
                    placeholder="Add dataset..."
                    className="text-xs py-2"
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        addListItem(datasets, setDatasets, newDataset);
                        setNewDataset('');
                      }
                    }}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { addListItem(datasets, setDatasets, newDataset); setNewDataset(''); }}
                  >
                    <Plus size={14} />
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* Design Tab */}
        <TabsContent value="design">
          <Card className="p-5 border-border/10">
            <h4 className="font-bold text-xs uppercase tracking-wider mb-3">Experimental Design</h4>
            <Textarea
              value={design}
              onChange={e => setDesign(e.target.value)}
              placeholder="Describe the experimental design, including controlled variables, randomization, replication strategy, and statistical approach..."
              className="min-h-[200px] text-sm"
            />
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {plan?.feasibility_score && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <CheckCircle2 size={12} className={plan.feasibility_score >= 7 ? 'text-success' : 'text-warning'} />
              Feasibility: {plan.feasibility_score}/10
            </div>
          )}
          {plan?.cost_estimate && (
            <span className="text-xs text-muted-foreground/50">| Est. cost: ${plan.cost_estimate.toFixed(2)}</span>
          )}
        </div>
        <div className="flex gap-2">
          {onGenerateScript && (
            <Button variant="secondary" size="sm" onClick={() => onGenerateScript(hypothesisId)}>
              <FlaskConical className="h-3.5 w-3.5 mr-1" />
              Generate Script
            </Button>
          )}
          <Button size="sm" onClick={handleSave}>
            <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
            Save Plan
          </Button>
        </div>
      </div>

      {/* Add Step Modal */}
      <Modal isOpen={showAddStep} onClose={() => setShowAddStep(false)} title="Add Validation Step" size="sm">
        <AddStepForm onAdd={addStep} />
      </Modal>
    </div>
  );
}

function AddStepForm({ onAdd }: { onAdd: (step: ValidationStep) => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<ValidationStep['type']>('statistical_test');
  const [expected, setExpected] = useState('');

  const handleSubmit = () => {
    if (!name.trim()) return;
    onAdd({
      id: `step-${Date.now()}`,
      name: name.trim(),
      description: description.trim(),
      type,
      status: 'pending',
      expected_outcome: expected.trim(),
    });
  };

  return (
    <div className="space-y-4">
      <Input label="Step Name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g., Train-test split validation" />
      <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe what this step does..." />
      <Select
        label="Type"
        value={type}
        onChange={e => setType(e.target.value as ValidationStep['type'])}
        options={[
          { value: 'data_prep', label: 'Data Preparation' },
          { value: 'statistical_test', label: 'Statistical Test' },
          { value: 'visualization', label: 'Visualization' },
          { value: 'comparison', label: 'Comparison' },
          { value: 'interpretation', label: 'Interpretation' },
        ]}
      />
      <Input label="Expected Outcome" value={expected} onChange={e => setExpected(e.target.value)} placeholder="What should happen?" />
      <Button className="w-full" onClick={handleSubmit} disabled={!name.trim()}>
        Add Step
      </Button>
    </div>
  );
}
