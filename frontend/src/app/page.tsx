'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import {
  FlaskConical,
  ArrowRight,
  Lightbulb,
  FileSearch,
  Brain,
  BarChart3,
  Zap,
  BookOpen,
  Network,
  Cpu,
  ShieldAlert,
  GitMerge,
  History,
  Workflow,
  Search,
  CheckCircle,
} from 'lucide-react';

export default function HomePage() {
  const [showBlueprint, setShowBlueprint] = useState(false);

  return (
    <Layout>
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-stone-900 via-secondary to-stone-800 text-stone-100 border-b border-white/5">
        {/* Animated background element */}
        <div className="absolute top-0 right-0 w-full h-full opacity-30 pointer-events-none">
           <div className="absolute top-[-20%] right-[-10%] w-[70%] h-[130%] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
        </div>

        <div className="max-w-7xl mx-auto px-10 py-32 relative z-10">
          <div className="max-w-3xl animate-in fade-in slide-in-from-left-12 duration-1000 ease-out">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/20 backdrop-blur-xl border border-primary/30 text-[10px] font-black uppercase tracking-[0.4em] text-primary mb-8 shadow-2xl shadow-primary/20">
              Autonomous Laboratory_v1.2
            </span>
            <h1 className="text-7xl font-black mb-10 tracking-tighter leading-[1.05]">
              Synthetic <br />
              <span className="bg-gradient-to-r from-primary via-amber-400 to-tertiary bg-clip-text text-transparent italic">Cognition</span>
            </h1>
            <p className="text-xl text-stone-300 mb-14 leading-relaxed font-bold uppercase tracking-widest opacity-80 max-w-xl border-l-4 border-primary/30 pl-8">
              A persistent research environment modeled after neural synthesis. 
              Map the frontier, resolve tensions, and forge hypotheses with 
              unparalleled precision.
            </p>
            <div className="flex items-center gap-6">
              <Link href="/projects">
                <Button size="lg" className="px-12 py-8 rounded-[2.5rem] shadow-2xl shadow-primary/30 hover:scale-105 active:scale-95 transition-all duration-700 group">
                  Initialize Lab Unit
                  <ArrowRight className="ml-4 group-hover:translate-x-2 transition-transform duration-500" size={24} />
                </Button>
              </Link>
              <Button 
                size="lg" 
                variant="ghost" 
                className="px-10 text-stone-300 hover:bg-white/5 rounded-[2.5rem] font-black uppercase tracking-widest text-xs"
                onClick={() => setShowBlueprint(true)}
              >
                System Blueprint
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Blueprint Modal */}
      <Modal
        isOpen={showBlueprint}
        onClose={() => setShowBlueprint(false)}
        title="Cognitive System Blueprint"
        size="lg"
      >
        <div className="space-y-12 py-6">
           {/* Loop Visualization */}
           <div className="space-y-6">
              <div className="flex items-center gap-3">
                 <div className="p-2 bg-primary/10 rounded-lg">
                    <Workflow size={18} className="text-primary" />
                 </div>
                 <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em]">The Central Cognitive Loop</h3>
              </div>
              
              <div className="bg-stone-50 dark:bg-stone-900 p-8 rounded-3xl border border-border/5 relative overflow-hidden group">
                 <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                 <div className="relative z-10 flex flex-wrap justify-center items-center gap-4">
                    {[
                      { label: 'Observe', icon: Search },
                      { label: 'Cluster', icon: Network },
                      { label: 'Question', icon: Brain },
                      { label: 'Formulate', icon: FlaskConical },
                      { label: 'Validate', icon: CheckCircle },
                      { label: 'Learn', icon: Zap }
                    ].map((step, i) => (
                      <React.Fragment key={step.label}>
                        <div className="flex flex-col items-center gap-3 group/step">
                           <div className="w-16 h-16 bg-white dark:bg-stone-800 rounded-2xl shadow-xl flex items-center justify-center border border-border/5 group-hover/step:scale-110 group-hover/step:rotate-6 transition-all duration-500">
                              <step.icon size={24} className="text-primary" />
                           </div>
                           <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/60">{step.label}</span>
                        </div>
                        {i < 5 && (
                          <div className="w-8 h-px bg-stone-200 dark:bg-stone-800 hidden md:block" />
                        )}
                      </React.Fragment>
                    ))}
                 </div>
              </div>
           </div>

           {/* Architecture Columns */}
           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-black text-stone-900 dark:text-stone-100 uppercase tracking-[0.3em]">
                    <History size={14} />
                    <span>Persistence Layer</span>
                 </div>
                 <ul className="space-y-3">
                    {[
                      'Database-First State Persistence',
                      'Full Decision Audit Trail',
                      'Scientific Evidence Ledger',
                      'Hypothesis Versioning Engine'
                    ].map(item => (
                      <li key={item} className="flex items-center gap-3 text-sm text-muted-foreground font-medium bg-stone-50 dark:bg-stone-900/40 p-4 rounded-xl border border-border/5">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary/40" />
                        {item}
                      </li>
                    ))}
                 </ul>
              </div>

              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-black text-stone-900 dark:text-stone-100 uppercase tracking-[0.3em]">
                    <ShieldAlert size={14} />
                    <span>Safety Guardrails</span>
                 </div>
                 <ul className="space-y-3">
                    {[
                      'Mandatory Sandbox Execution',
                      'Real-time Token Budgeting',
                      'Human-in-the-Loop Approval Gates',
                      'Protocol Consistency Checks'
                    ].map(item => (
                      <li key={item} className="flex items-center gap-3 text-sm text-muted-foreground font-medium bg-stone-50 dark:bg-stone-900/40 p-4 rounded-xl border border-border/5">
                        <div className="w-1.5 h-1.5 rounded-full bg-error/40" />
                        {item}
                      </li>
                    ))}
                 </ul>
              </div>
           </div>

           <div className="p-8 bg-primary/5 rounded-3xl border border-primary/10">
              <p className="text-center text-sm font-bold text-stone-600 dark:text-stone-400 italic">
                 {"The system behaves like a persistent researcher’s brain: monitoring literature, detecting tensions, and learning reusable skills from every cycle."}
              </p>
           </div>
        </div>
      </Modal>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-8 py-24">
        <div className="text-center mb-16 space-y-3">
          <h2 className="text-3xl font-extrabold text-foreground tracking-tight text-stone-800">
            Integrated Cognitive Engines
          </h2>
          <p className="text-muted-foreground font-black uppercase tracking-[0.2em] text-xs">Architectural Pillars of Autoscience</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-primary group-hover:text-stone-900 transition-all duration-700 group-hover:rotate-6">
              <Lightbulb className="text-primary" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Idea Generation</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
              Autonomous frontier scanning identifies literature gaps and cross-domain connections to spawn novel research seeds.
            </p>
          </Card>

          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-success/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-success group-hover:text-white transition-all duration-700 group-hover:rotate-6">
              <FileSearch className="text-success" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Literature Extraction</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
              Deep semantic parsing of academic sources extracts structured claims, methodology, and scientific tensions.
            </p>
          </Card>

          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-tertiary/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-tertiary group-hover:text-white transition-all duration-700 group-hover:rotate-6">
              <Brain className="text-tertiary" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Hypothesis Synthesis</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
              Converts research questions into testable, versioned hypotheses with associated dataset and validation plans.
            </p>
          </Card>

          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-warning/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-warning group-hover:text-white transition-all duration-700 group-hover:rotate-6">
              <BarChart3 className="text-warning" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Objective Scoring</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
              Honest evaluation of research utility via a 12-dimensional utility function, preventing hallucination drift.
            </p>
          </Card>

          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-error/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-error group-hover:text-white transition-all duration-700 group-hover:rotate-6">
              <Zap className="text-error" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Skill Acquisition</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
               System memoizes successful research protocols into reusable &ldquo;Skills&rdquo; that optimize subsequent cognitive cycles.
            </p>
          </Card>

          <Card hover className="p-8 group">
            <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 shadow-inner group-hover:bg-primary group-hover:text-stone-900 transition-all duration-700 group-hover:rotate-6">
              <BookOpen className="text-primary" size={28} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3 tracking-tight">Evidence Ledger</h3>
            <p className="text-muted-foreground leading-relaxed text-sm font-medium">
              Persistent knowledge graph of project state, decision history, and artifact lineage for total research transparency.
            </p>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative py-32 overflow-hidden border-t border-border/10 bg-stone-50">
        <div className="absolute top-0 right-0 w-[50%] h-full bg-primary/5 blur-[140px] rounded-full translate-x-1/3" />
        <div className="max-w-5xl mx-auto px-10 relative z-10 text-center">
          <div className="w-32 h-32 bg-white shadow-2xl rounded-[3rem] flex items-center justify-center mx-auto mb-12 border border-border/5 group hover:rotate-[360deg] transition-all duration-[2500ms] ease-in-out">
            <FlaskConical className="text-primary" size={64} />
          </div>
          <h2 className="text-5xl font-black mb-8 tracking-tighter text-foreground text-stone-900 leading-tight">Accelerate Your Research Output</h2>
          <p className="text-xl text-muted-foreground mb-14 leading-relaxed font-black uppercase tracking-[0.1em] opacity-60">
            Join the frontier of autonomous scientific discovery. Configure your cognitive parameters 
            and let the laboratory run while you sleep.
          </p>
          <Link href="/projects">
            <Button size="lg" className="px-14 py-8 rounded-[2.5rem] shadow-2xl shadow-primary/30 hover:scale-105 active:scale-95 transition-all duration-500">
              Initialize Synthesis Engine
              <ArrowRight className="ml-4" size={24} />
            </Button>
          </Link>
        </div>
      </div>
    </Layout>
  );
}
