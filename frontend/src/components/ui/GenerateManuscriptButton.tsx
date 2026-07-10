'use client';

import { useState } from 'react';
import { Manuscript } from '@/lib/types';
import { manuscriptsApi } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Loader2, FileText, Sparkles } from 'lucide-react';

interface GenerateManuscriptButtonProps {
  runId: string;
  projectId: string;
  onGenerated: (manuscript: Manuscript) => void;
}

export function GenerateManuscriptButton({ runId, projectId, onGenerated }: GenerateManuscriptButtonProps) {
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const manuscript = await manuscriptsApi.generate(runId);
      onGenerated(manuscript);
    } catch (err) {
      console.error('Failed to generate manuscript:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Button
      variant="primary"
      size="lg"
      onClick={handleGenerate}
      disabled={generating}
      className="rounded-xl px-8 py-6 text-[10px] font-black uppercase tracking-widest shadow-2xl shadow-primary/20 hover:shadow-primary/30 transition-all"
    >
      {generating ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin mr-3" />
          Generating...
        </>
      ) : (
        <>
          <Sparkles className="h-5 w-5 mr-3" />
          Generate Manuscript
        </>
      )}
    </Button>
  );
}