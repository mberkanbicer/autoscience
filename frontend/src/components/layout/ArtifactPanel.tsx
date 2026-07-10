'use client';

import React from 'react';
import { useArtifact } from '@/lib/ArtifactContext';
import { LaTeXArtifact } from '@/components/common/LaTeXArtifact';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

export function ArtifactPanel() {
  const { activeArtifact, isOpen, closeArtifact, updateArtifactContent } = useArtifact();

  if (!isOpen || !activeArtifact) return null;

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm lg:hidden"
        aria-label="Close artifact panel"
        onClick={closeArtifact}
      />
      <div
        className={cn(
          'fixed z-40 glass shadow-2xl border-border/10 flex flex-col',
          'inset-0 lg:inset-y-0 lg:right-0 lg:left-auto',
          'w-full lg:w-[min(600px,100vw)]',
          'border-t lg:border-t-0 lg:border-l',
          'animate-in slide-in-from-bottom-full lg:slide-in-from-right-full duration-500 ease-in-out',
        )}
      >
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 border-b border-border/10 bg-white/40 backdrop-blur-md shrink-0">
          <div className="min-w-0 pr-4">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] block mb-1">
              Active Artifact
            </span>
            <h3 className="text-base sm:text-lg font-bold text-foreground tracking-tight truncate">
              {activeArtifact.title}
            </h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={closeArtifact}
            className="rounded-full hover:rotate-90 transition-all duration-300 shrink-0"
          >
            <X size={20} />
          </Button>
        </div>

        <div className="flex-1 min-h-0 overflow-hidden p-4 sm:p-6 bg-muted/20">
          {activeArtifact.type === 'latex' && (
            <LaTeXArtifact
              initialContent={activeArtifact.content}
              onSave={(content) => {
                updateArtifactContent(content);
              }}
            />
          )}

          {activeArtifact.type !== 'latex' && (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm text-center px-4">
              Preview for {activeArtifact.type} not implemented yet.
            </div>
          )}
        </div>
      </div>
    </>
  );
}