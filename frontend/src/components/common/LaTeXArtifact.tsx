'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Copy, Check, Download, Maximize2, Minimize2, Play, Eraser } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LaTeXArtifactProps {
  initialContent?: string;
  onSave?: (content: string) => void;
}

export function LaTeXArtifact({ initialContent = '', onSave }: LaTeXArtifactProps) {
  const [content, setContent] = useState(initialContent);
  const [copied, setCopied] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const previewRef = useRef<HTMLDivElement>(null);
  const [isKaTexLoaded, setIsKaTexLoaded] = useState(false);

  // Load KaTeX dynamically from CDN
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.hasOwnProperty('renderMathInElement')) {
      setIsKaTexLoaded(true);
      return;
    }

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css';
    link.integrity = 'sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvEasxt3uSVGy';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js';
    script.integrity = 'sha384-7zkInuTyB7LRCOpa9Wn99Gis4Opx+zE1K6H4qH406A17726hYl4NByw066hXTP6g';
    script.crossOrigin = 'anonymous';
    script.defer = true;
    script.onload = () => {
      const autoRenderScript = document.createElement('script');
      autoRenderScript.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js';
      autoRenderScript.integrity = 'sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk';
      autoRenderScript.crossOrigin = 'anonymous';
      autoRenderScript.defer = true;
      autoRenderScript.onload = () => setIsKaTexLoaded(true);
      document.head.appendChild(autoRenderScript);
    };
    document.head.appendChild(script);
  }, []);

  const renderLaTeX = () => {
    if (isKaTexLoaded && previewRef.current && (window as any).renderMathInElement) {
      (window as any).renderMathInElement(previewRef.current, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true }
        ],
        throwOnError: false
      });
    }
  };

  useEffect(() => {
    renderLaTeX();
  }, [content, isKaTexLoaded]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'artifact.tex';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={cn(
      'flex flex-col h-full bg-white/60 backdrop-blur-md border-white/40 transition-all duration-700 overflow-hidden shadow-xl',
      isMaximized ? 'fixed inset-8 z-50 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.2)]' : ''
    )}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border/10 bg-white/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-error/40 border border-error/20" />
            <div className="w-3 h-3 rounded-full bg-warning/40 border border-warning/20" />
            <div className="w-3 h-3 rounded-full bg-success/40 border border-success/20" />
          </div>
          <span className="ml-2 text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">Scientific Manuscript</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleCopy} className="rounded-lg hover:bg-primary/5 hover:text-primary transition-all duration-300" title="Copy Source">
            {copied ? <Check size={16} className="text-success" /> : <Copy size={16} />}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDownload} className="rounded-lg hover:bg-primary/5 hover:text-primary transition-all duration-300" title="Export .tex">
            <Download size={16} />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setIsMaximized(!isMaximized)} className="rounded-lg hover:bg-primary/5 hover:text-primary transition-all duration-300" title={isMaximized ? "Minimize" : "Full Screen"}>
            {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="editor" className="flex flex-col flex-1 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-2 border-b border-border/10 bg-white/20">
          <TabsList className="bg-muted/40 p-1">
            <TabsTrigger value="editor" className="text-[10px] uppercase font-bold px-4 py-1.5">Editor</TabsTrigger>
            <TabsTrigger value="preview" className="text-[10px] uppercase font-bold px-4 py-1.5" onMouseEnter={renderLaTeX}>Render</TabsTrigger>
            <TabsTrigger value="split" className="text-[10px] uppercase font-bold px-4 py-1.5" onMouseEnter={renderLaTeX}>Split</TabsTrigger>
          </TabsList>
          {onSave && (
            <Button variant="primary" size="sm" onClick={() => onSave(content)} className="h-8 px-4 text-[10px] uppercase font-bold tracking-widest shadow-lg shadow-primary/20">
              Commit Changes
            </Button>
          )}
        </div>

        <TabsContent value="editor" className="flex-1 p-0 m-0 overflow-hidden animate-in fade-in duration-500">
          <textarea
            className="w-full h-full p-8 font-mono text-sm resize-none focus:outline-none bg-transparent text-foreground/80 selection:bg-primary/20"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            spellCheck={false}
            placeholder="% Research notation entry...
\section{Research Summary}
Describe your findings here..."
          />
        </TabsContent>

        <TabsContent value="preview" className="flex-1 p-0 m-0 overflow-hidden animate-in fade-in duration-500">
          <div 
            ref={previewRef}
            className="w-full h-full p-10 overflow-y-auto bg-white/50 prose prose-slate max-w-none prose-headings:tracking-tight prose-headings:font-bold prose-math:text-primary"
          >
            {content.split('\n').map((line, i) => (
              <p key={i} className="mb-2 whitespace-pre-wrap">{line}</p>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="split" className="flex-1 p-0 m-0 overflow-hidden animate-in fade-in duration-500">
          <div className="flex h-full divide-x divide-border/10">
            <div className="flex-1">
              <textarea
                className="w-full h-full p-6 font-mono text-xs resize-none focus:outline-none bg-transparent text-foreground/70"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                spellCheck={false}
              />
            </div>
            <div className="flex-1 overflow-y-auto bg-white/30 p-8">
              <div ref={previewRef} className="prose prose-sm prose-slate max-w-none prose-math:text-primary">
                {content.split('\n').map((line, i) => (
                  <p key={i} className="mb-2 whitespace-pre-wrap">{line}</p>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
