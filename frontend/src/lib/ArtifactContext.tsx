'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

export type ArtifactType = 'latex' | 'code' | 'chart' | 'document';

interface Artifact {
  id: string;
  type: ArtifactType;
  title: string;
  content: string;
}

interface ArtifactContextType {
  activeArtifact: Artifact | null;
  isOpen: boolean;
  openArtifact: (artifact: Artifact) => void;
  closeArtifact: () => void;
  updateArtifactContent: (content: string) => void;
}

const ArtifactContext = createContext<ArtifactContextType | undefined>(undefined);

export function ArtifactProvider({ children }: { children: ReactNode }) {
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const openArtifact = (artifact: Artifact) => {
    setActiveArtifact(artifact);
    setIsOpen(true);
  };

  const closeArtifact = () => {
    setIsOpen(false);
  };

  const updateArtifactContent = (content: string) => {
    if (activeArtifact) {
      setActiveArtifact({ ...activeArtifact, content });
    }
  };

  return (
    <ArtifactContext.Provider value={{ activeArtifact, isOpen, openArtifact, closeArtifact, updateArtifactContent }}>
      {children}
    </ArtifactContext.Provider>
  );
}

export function useArtifact() {
  const context = useContext(ArtifactContext);
  if (context === undefined) {
    throw new Error('useArtifact must be used within an ArtifactProvider');
  }
  return context;
}
