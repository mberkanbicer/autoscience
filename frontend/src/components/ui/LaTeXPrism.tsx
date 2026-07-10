'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Edit3, MessageSquare, Send, Sparkles, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface LaTeXPrismProps {
  content: string;
  onUpdate: (newContent: string) => Promise<void>;
}

export function LaTeXPrism({ content, onUpdate }: LaTeXPrismProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftContent, setDraftContent] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const [selection, setSelection] = useState({ text: '', start: 0, end: 0 });
  const [prompt, setPrompt] = useState('');

  const handleSelection = () => {
    const textarea = document.getElementById('latex-editor') as HTMLTextAreaElement;
    if (!textarea) return;
    
    const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    if (selectedText) {
      setSelection({
        text: selectedText,
        start: textarea.selectionStart,
        end: textarea.selectionEnd
      });
    }
  };

  const applyAIReview = async () => {
     // This would call an LLM to refine the selected section
     setIsSaving(true);
     try {
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate AI processing
        const refinedText = `% AI REFINED: ${selection.text}\n% Rationale: Increased statistical rigor\n${selection.text}`;
        const newContent = draftContent.substring(0, selection.start) + refinedText + draftContent.substring(selection.end);
        setDraftContent(newContent);
        setPrompt('');
        setSelection({ text: '', start: 0, end: 0 });
     } finally {
        setIsSaving(false);
     }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdate(draftContent);
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-[10px] font-black text-primary uppercase tracking-[0.3em]">
           <Sparkles size={14} />
           <span>Prism Logic Refinement</span>
        </div>
        <div className="flex gap-2">
           {!isEditing ? (
             <Button size="sm" onClick={() => setIsEditing(true)} className="rounded-xl text-[9px] font-black uppercase tracking-widest px-4 py-2">
                <Edit3 size={12} className="mr-2" /> Open Editor
             </Button>
           ) : (
             <div className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={() => setIsEditing(false)} className="rounded-xl text-[9px] font-black uppercase tracking-widest">
                   Cancel
                </Button>
                <Button size="sm" onClick={handleSave} disabled={isSaving} className="rounded-xl text-[9px] font-black uppercase tracking-widest px-6 py-2 shadow-lg shadow-primary/20">
                   {isSaving ? <Loader2 size={12} className="animate-spin mr-2" /> : <Check size={12} className="mr-2" />}
                   Sync Changes
                </Button>
             </div>
           )}
        </div>
      </div>

      <div className={cn(
        "relative rounded-[2rem] border transition-all duration-700",
        isEditing ? "border-primary/30 shadow-2xl" : "border-white/5 shadow-inner"
      )}>
        <textarea
          id="latex-editor"
          readOnly={!isEditing}
          value={draftContent}
          onChange={(e) => setDraftContent(e.target.value)}
          onMouseUp={handleSelection}
          className={cn(
            "w-full h-[600px] bg-stone-950 p-10 font-mono text-xs leading-relaxed text-stone-300 rounded-[2rem] focus:outline-none resize-none custom-scrollbar",
            !isEditing && "cursor-default"
          )}
        />
        
        {/* Floating AI Toolbar */}
        {isEditing && selection.text && (
          <div className="absolute top-10 right-10 w-80 glass-dark p-6 rounded-3xl shadow-2xl border border-primary/20 animate-in slide-in-from-right-4 duration-500 z-20">
             <div className="flex items-center gap-2 text-[8px] font-black text-primary uppercase tracking-widest mb-4">
                <MessageSquare size={12} />
                <span>Contextual Instruction</span>
             </div>
             <textarea 
               placeholder="e.g., 'Make this section more formal' or 'Add citations to support this claim'..."
               value={prompt}
               onChange={(e) => setPrompt(e.target.value)}
               className="w-full bg-stone-800 border border-white/5 rounded-xl p-3 text-[10px] text-stone-100 placeholder:text-stone-600 focus:border-primary/40 focus:outline-none mb-4 h-24 resize-none"
             />
             <Button 
               size="sm" 
               className="w-full rounded-xl text-[9px] font-black uppercase tracking-widest py-4 bg-primary text-stone-900 hover:scale-105 transition-all"
               onClick={applyAIReview}
               disabled={isSaving}
             >
                {isSaving ? <Loader2 size={12} className="animate-spin mr-2" /> : <Sparkles size={12} className="mr-2" />}
                Refine Selection
             </Button>
             <p className="mt-3 text-[8px] text-muted-foreground/40 text-center font-bold uppercase tracking-tighter italic">
                PRISM_LOGIC_V1.2_ACTIVE
             </p>
          </div>
        )}
      </div>
    </div>
  );
}
