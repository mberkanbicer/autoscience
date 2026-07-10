'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Brain, 
  Settings2, 
  Cpu, 
  Zap, 
  ArrowRight, 
  ArrowLeft, 
  FlaskConical, 
  Search, 
  ShieldAlert, 
  Wrench,
  Loader2,
  CheckCircle,
  Lightbulb
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';

interface DiscoveryWizardProps {
  projectId: string;
  onStart: (config: any) => Promise<void>;
  onClose: () => void;
}

type WizardStep = 'intent' | 'params' | 'foundry' | 'review';

export function DiscoveryWizard({ projectId, onStart, onClose }: DiscoveryWizardProps) {
  const [step, setStep] = useState<WizardStep>('intent');
  const [isSubmitting, setIsSaving] = useState(false);
  
  // Wizard State
  const [config, setConfig] = useState({
    topic: '',
    flexibility: 0.6,
    max_sources: 50,
    max_cost_usd: 1.0,
    enable_skeptic: true,
    enable_developer: true,
    enable_skill_creation: true,
  });

  const nextStep = () => {
    if (step === 'intent') setStep('params');
    else if (step === 'params') setStep('foundry');
    else if (step === 'foundry') setStep('review');
  };

  const prevStep = () => {
    if (step === 'params') setStep('intent');
    else if (step === 'foundry') setStep('params');
    else if (step === 'review') setStep('foundry');
  };

  const handleStart = async () => {
    setIsSaving(true);
    try {
      await onStart(config);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-10 py-4">
      {/* Progress Indicator */}
      <div className="flex items-center justify-between px-10">
        {[
          { id: 'intent', icon: Lightbulb, label: 'Intent' },
          { id: 'params', icon: Settings2, label: 'Scope' },
          { id: 'foundry', icon: Cpu, label: 'Foundry' },
          { id: 'review', icon: Zap, label: 'Ignition' },
        ].map((s, i) => {
          const isActive = step === s.id;
          const isDone = ['intent', 'params', 'foundry', 'review'].indexOf(step) > i;
          return (
            <React.Fragment key={s.id}>
              <div className="flex flex-col items-center gap-3">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-lg",
                  isActive ? "bg-primary text-stone-900 scale-110 ring-4 ring-primary/20" : 
                  isDone ? "bg-primary/20 text-primary" : "bg-stone-100 dark:bg-stone-800 text-stone-400"
                )}>
                  <s.icon size={20} />
                </div>
                <span className={cn(
                  "text-[9px] font-black uppercase tracking-[0.2em]",
                  isActive ? "text-primary" : "text-muted-foreground/40"
                )}>{s.label}</span>
              </div>
              {i < 3 && (
                <div className={cn(
                  "h-px flex-1 mx-4 transition-colors duration-500",
                  isDone ? "bg-primary/40" : "bg-stone-200 dark:bg-stone-800"
                )} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="min-h-[400px] animate-in fade-in slide-in-from-bottom-4 duration-700">
        {step === 'intent' && (
          <div className="space-y-8 p-6">
            <div className="space-y-4 text-center max-w-xl mx-auto">
               <h3 className="text-3xl font-black text-foreground tracking-tighter uppercase">Formulate Research Intent</h3>
               <p className="text-muted-foreground font-medium">Define the core scientific question or seed idea that the laboratory should investigate.</p>
            </div>
            <textarea
              autoFocus
              value={config.topic}
              onChange={(e) => setConfig({ ...config, topic: e.target.value })}
              placeholder="e.g., 'Analyze the impact of metasurface array geometry on localized heating for hyperthermia treatment...'"
              className="w-full h-48 bg-stone-50 dark:bg-stone-900/50 border border-stone-200 dark:border-stone-100/10 rounded-[2rem] p-10 text-lg font-bold text-foreground placeholder:text-stone-300 focus:ring-4 focus:ring-primary/10 focus:border-primary/30 transition-all outline-none custom-scrollbar shadow-inner"
            />
            <div className="flex justify-center">
               <Badge className="bg-primary/5 text-primary border-primary/10 px-4 py-2 uppercase text-[10px] font-black tracking-widest animate-pulse">
                  Neural synthesis active
               </Badge>
            </div>
          </div>
        )}

        {step === 'params' && (
          <div className="space-y-10 p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-2">Exploration Flexibility</label>
                  <div className="bg-stone-50 dark:bg-stone-900/50 p-8 rounded-3xl border border-border/5 space-y-6">
                    <input 
                      type="range" min="0" max="1" step="0.1" 
                      value={config.flexibility}
                      onChange={(e) => setConfig({ ...config, flexibility: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-stone-200 dark:bg-stone-800 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">
                      <span>Strict Protocol</span>
                      <span className="text-primary text-sm font-black">{config.flexibility * 100}%</span>
                      <span>High Entropy</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-2">Literature Depth</label>
                  <div className="grid grid-cols-3 gap-4">
                    {[20, 50, 100].map(val => (
                      <button 
                        key={val}
                        onClick={() => setConfig({ ...config, max_sources: val })}
                        className={cn(
                          "py-4 rounded-2xl border text-[10px] font-black uppercase tracking-widest transition-all duration-300",
                          config.max_sources === val ? "bg-primary text-stone-900 border-primary" : "bg-stone-50 dark:bg-stone-900 border-border/5 text-muted-foreground"
                        )}
                      >
                        {val} Sources
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <div className="space-y-2 text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-2">Resource Budget (USD)</div>
                <div className="bg-stone-50 dark:bg-stone-900/50 p-10 rounded-[2.5rem] border border-border/5 flex flex-col items-center justify-center gap-6">
                   <div className="text-5xl font-black text-foreground tracking-tighter">
                      ${config.max_cost_usd.toFixed(2)}
                   </div>
                   <div className="flex gap-4">
                      {[0.5, 1.0, 5.0].map(val => (
                        <button 
                          key={val}
                          onClick={() => setConfig({ ...config, max_cost_usd: val })}
                          className={cn(
                            "w-12 h-12 rounded-xl border flex items-center justify-center text-[10px] font-black transition-all",
                            config.max_cost_usd === val ? "bg-primary text-stone-900 border-primary" : "bg-white dark:bg-stone-800 border-border/5"
                          )}
                        >
                           ${val}
                        </button>
                      ))}
                   </div>
                   <p className="text-[9px] text-muted-foreground/40 font-bold uppercase text-center max-w-[200px]">
                      The system will automatically pause if the compute cost exceeds this threshold.
                   </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'foundry' && (
          <div className="space-y-8 p-6">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { 
                    id: 'enable_developer', 
                    label: 'Autonomous Developer', 
                    icon: Wrench, 
                    desc: 'Enables Python sandbox for empirical validation and experiment execution.',
                    color: 'text-primary'
                  },
                  { 
                    id: 'enable_skeptic', 
                    label: 'Adversarial Skeptic', 
                    icon: ShieldAlert, 
                    desc: 'Challenges findings and probes for prior art to ensure novelty.',
                    color: 'text-error'
                  },
                  { 
                    id: 'enable_skill_creation', 
                    label: 'Skill Curator', 
                    icon: Zap, 
                    desc: 'Extracts and memoizes successful research protocols as reusable system skills.',
                    color: 'text-warning'
                  },
                ].map(agent => (
                  <Card 
                    key={agent.id}
                    className={cn(
                      "p-8 cursor-pointer transition-all duration-500 rounded-[2rem]",
                      (config as any)[agent.id] ? "ring-2 ring-primary bg-primary/[0.02]" : "opacity-60 border-border/5 grayscale"
                    )}
                    onClick={() => setConfig({ ...config, [agent.id]: !(config as any)[agent.id] })}
                  >
                    <div className="flex gap-6 items-start">
                       <div className={cn("p-4 rounded-2xl bg-stone-100 dark:bg-stone-800", (config as any)[agent.id] && "bg-primary/20")}>
                          <agent.icon size={24} className={(config as any)[agent.id] ? agent.color : "text-stone-400"} />
                       </div>
                       <div className="flex-1">
                          <div className="flex justify-between items-center mb-2">
                             <h4 className="font-black text-foreground tracking-tight uppercase text-xs">{agent.label}</h4>
                             <div className={cn(
                               "w-4 h-4 rounded-full border-2 transition-all",
                               (config as any)[agent.id] ? "bg-primary border-primary" : "border-stone-300"
                             )} />
                          </div>
                          <p className="text-xs text-muted-foreground font-medium leading-relaxed">{agent.desc}</p>
                       </div>
                    </div>
                  </Card>
                ))}
             </div>
          </div>
        )}

        {step === 'review' && (
          <div className="space-y-10 p-6 flex flex-col items-center">
             <div className="w-24 h-24 bg-primary/20 rounded-[2.5rem] flex items-center justify-center animate-pulse shadow-2xl shadow-primary/30 mb-6">
                <FlaskConical size={48} className="text-primary" />
             </div>
             <div className="text-center space-y-4 max-w-lg">
                <h3 className="text-4xl font-black text-foreground tracking-tighter uppercase leading-none">Ready for Synthesis</h3>
                <p className="text-muted-foreground font-medium">All cognitive parameters have been mapped. The laboratory is ready to initialize the discovery engine.</p>
             </div>

             <div className="w-full grid grid-cols-3 gap-4">
                {[
                  { label: 'Sources', val: config.max_sources },
                  { label: 'Mode', val: config.flexibility > 0.5 ? 'Broad' : 'Focused' },
                  { label: 'Budget', val: `$${config.max_cost_usd}` }
                ].map(item => (
                  <div key={item.label} className="bg-stone-50 dark:bg-stone-900/50 p-6 rounded-3xl border border-border/5 text-center">
                    <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">{item.label}</p>
                    <p className="text-lg font-black text-foreground">{item.val}</p>
                  </div>
                ))}
             </div>
          </div>
        )}
      </div>

      {/* Navigation Bar */}
      <div className="p-8 border-t border-border/5 bg-stone-50/50 dark:bg-stone-900/50 rounded-b-[2rem] flex items-center justify-between">
        <Button 
          variant="ghost" 
          onClick={step === 'intent' ? onClose : prevStep}
          className="rounded-2xl px-10 py-6 text-[10px] font-black uppercase tracking-widest"
        >
          {step === 'intent' ? 'Abort' : (
            <>
              <ArrowLeft size={14} className="mr-2" /> Back
            </>
          )}
        </Button>
        
        <Button 
          variant="primary"
          disabled={(step === 'intent' && !config.topic) || isSubmitting}
          onClick={step === 'review' ? handleStart : nextStep}
          className="rounded-2xl px-12 py-6 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 group"
        >
          {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : (
            <>
              {step === 'review' ? 'Ignition' : 'Next Step'}
              <ArrowRight size={14} className="ml-2 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
