'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  FolderKanban, 
  Settings2, 
  FlaskConical, 
  Zap, 
  ArrowRight, 
  ArrowLeft, 
  Loader2,
  CheckCircle,
  Lightbulb,
  FileSearch,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Input, Textarea } from '@/components/ui/Input';

interface ProjectCreationWizardProps {
  onStart: (data: any) => void;
  onClose: () => void;
  isSubmitting?: boolean;
}

type WizardStep = 'identity' | 'context' | 'policy' | 'review';

export function ProjectCreationWizard({ onStart, onClose, isSubmitting }: ProjectCreationWizardProps) {
  const [step, setStep] = useState<WizardStep>('identity');
  
  // Wizard State
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    description: '',
    default_flexibility: 0.6,
    idle_research_enabled: true,
    idle_trigger_minutes: 120,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateStep = () => {
    const newErrors: Record<string, string> = {};
    if (step === 'identity') {
      if (!formData.name) newErrors.name = 'Project name is required';
      if (!formData.domain) newErrors.domain = 'Research domain is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep()) {
      if (step === 'identity') setStep('context');
      else if (step === 'context') setStep('policy');
      else if (step === 'policy') setStep('review');
    }
  };

  const prevStep = () => {
    if (step === 'context') setStep('identity');
    else if (step === 'policy') setStep('context');
    else if (step === 'review') setStep('policy');
  };

  return (
    <div className="space-y-10 py-4">
      {/* Progress Indicator */}
      <div className="flex items-center justify-between px-10">
        {[
          { id: 'identity', icon: FolderKanban, label: 'Identity' },
          { id: 'context', icon: FileSearch, label: 'Context' },
          { id: 'policy', icon: Settings2, label: 'Policy' },
          { id: 'review', icon: Zap, label: 'Initialize' },
        ].map((s, i) => {
          const isActive = step === s.id;
          const isDone = ['identity', 'context', 'policy', 'review'].indexOf(step) > i;
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
        {step === 'identity' && (
          <div className="space-y-8 p-6 max-w-xl mx-auto">
            <div className="space-y-4 text-center">
               <h3 className="text-3xl font-black text-foreground tracking-tighter uppercase leading-none">New Lab Unit</h3>
               <p className="text-muted-foreground font-medium">Define the core identity of this research instance.</p>
            </div>
            <div className="space-y-6 bg-stone-50 dark:bg-stone-900/50 p-10 rounded-[2.5rem] border border-border/5 shadow-inner">
               <Input 
                 label="Laboratory Name" 
                 placeholder="e.g., Quantum Synthesis Foundry" 
                 value={formData.name}
                 onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                 error={errors.name}
               />
               <Input 
                 label="Scientific Domain" 
                 placeholder="e.g., Applied Physics, Neural Cognition" 
                 value={formData.domain}
                 onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                 error={errors.domain}
               />
            </div>
          </div>
        )}

        {step === 'context' && (
          <div className="space-y-8 p-6 max-w-2xl mx-auto">
            <div className="space-y-4 text-center">
               <h3 className="text-3xl font-black text-foreground tracking-tighter uppercase leading-none">Scientific Abstract</h3>
               <p className="text-muted-foreground font-medium">Provide a high-level overview of the research goals and core methodology.</p>
            </div>
            <Textarea
              autoFocus
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="The primary focus of this project is to investigate the relationship between..."
              className="w-full h-56 bg-stone-50 dark:bg-stone-900/50 border border-stone-200 dark:border-stone-100/10 rounded-[2rem] p-10 text-lg font-bold text-foreground placeholder:text-stone-300 focus:ring-4 focus:ring-primary/10 focus:border-primary/30 transition-all outline-none custom-scrollbar shadow-inner"
            />
          </div>
        )}

        {step === 'policy' && (
          <div className="space-y-10 p-6 max-w-2xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-2">Default Flexibility</label>
                  <div className="bg-stone-50 dark:bg-stone-900/50 p-8 rounded-3xl border border-border/5 space-y-6">
                    <input 
                      type="range" min="0" max="1" step="0.1" 
                      value={formData.default_flexibility}
                      onChange={(e) => setFormData({ ...formData, default_flexibility: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-stone-200 dark:bg-stone-800 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">
                      <span>Strict</span>
                      <span className="text-primary text-sm font-black">{formData.default_flexibility * 100}%</span>
                      <span>Creative</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <div className="space-y-4">
                  <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-2">Idle Research Mode</label>
                  <Card 
                    className={cn(
                      "p-8 cursor-pointer transition-all duration-500 rounded-[2rem]",
                      formData.idle_research_enabled ? "ring-2 ring-primary bg-primary/[0.02]" : "opacity-60 border-border/5 grayscale"
                    )}
                    onClick={() => setFormData({ ...formData, idle_research_enabled: !formData.idle_research_enabled })}
                  >
                    <div className="flex gap-4 items-center">
                       <div className={cn("p-3 rounded-xl bg-stone-100 dark:bg-stone-800", formData.idle_research_enabled && "bg-primary/20")}>
                          <Activity size={18} className={formData.idle_research_enabled ? "text-primary" : "text-stone-400"} />
                       </div>
                       <div className="flex-1">
                          <h4 className="font-black text-foreground tracking-tight uppercase text-[10px]">Background Cognition</h4>
                       </div>
                       <div className={cn(
                         "w-4 h-4 rounded-full border-2 transition-all",
                         formData.idle_research_enabled ? "bg-primary border-primary" : "border-stone-300"
                       )} />
                    </div>
                  </Card>
                  <p className="text-[9px] text-muted-foreground/40 font-bold uppercase text-center px-4 leading-relaxed">
                     When enabled, the laboratory will perform low-intensity literature scanning while idle.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'review' && (
          <div className="space-y-10 p-6 flex flex-col items-center">
             <div className="w-24 h-24 bg-primary/20 rounded-[2.5rem] flex items-center justify-center animate-pulse shadow-2xl shadow-primary/30 mb-6">
                <FlaskConical size={48} className="text-primary" />
             </div>
             <div className="text-center space-y-4 max-w-lg">
                <h3 className="text-4xl font-black text-foreground tracking-tighter uppercase leading-none">Initialize Laboratory</h3>
                <p className="text-muted-foreground font-medium">Review the configuration before booting the autonomous instance.</p>
             </div>

             <div className="w-full grid grid-cols-2 gap-4 max-w-md">
                <div className="bg-stone-50 dark:bg-stone-900/50 p-6 rounded-3xl border border-border/5">
                   <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Unit Name</p>
                   <p className="text-sm font-black text-foreground truncate">{formData.name}</p>
                </div>
                <div className="bg-stone-50 dark:bg-stone-900/50 p-6 rounded-3xl border border-border/5">
                   <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Domain</p>
                   <p className="text-sm font-black text-foreground truncate">{formData.domain}</p>
                </div>
                <div className="bg-stone-50 dark:bg-stone-900/50 p-6 rounded-3xl border border-border/5">
                   <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Background Cognition</p>
                   <p className="text-sm font-black text-foreground">{formData.idle_research_enabled ? 'Active' : 'Disabled'}</p>
                </div>
                <div className="bg-stone-50 dark:bg-stone-900/50 p-6 rounded-3xl border border-border/5">
                   <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-widest mb-1">Flexibility</p>
                   <p className="text-sm font-black text-foreground">{formData.default_flexibility * 100}%</p>
                </div>
             </div>
          </div>
        )}
      </div>

      {/* Navigation Bar */}
      <div className="p-8 border-t border-border/5 bg-stone-50/50 dark:bg-stone-900/50 rounded-b-[2rem] flex items-center justify-between">
        <Button 
          variant="ghost" 
          onClick={step === 'identity' ? onClose : prevStep}
          className="rounded-2xl px-10 py-6 text-[10px] font-black uppercase tracking-widest"
        >
          {step === 'identity' ? 'Abort' : (
            <>
              <ArrowLeft size={14} className="mr-2" /> Back
            </>
          )}
        </Button>
        
        <Button 
          variant="primary"
          disabled={isSubmitting}
          onClick={step === 'review' ? () => onStart(formData) : nextStep}
          className="rounded-2xl px-12 py-6 text-[10px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 group"
        >
          {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : (
            <>
              {step === 'review' ? 'Boot Instance' : 'Next Step'}
              <ArrowRight size={14} className="ml-2 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
