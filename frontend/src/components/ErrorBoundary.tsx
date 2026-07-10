'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center glass rounded-2xl border-error/10 p-12 text-center animate-in fade-in zoom-in-95 duration-700">
          <div className="w-20 h-20 bg-error/10 rounded-full flex items-center justify-center mb-8 shadow-inner animate-pulse">
            <AlertTriangle className="h-10 w-10 text-error" />
          </div>
          <h3 className="text-xl font-bold text-foreground mb-3 uppercase tracking-tight">Cognitive System Fault</h3>
          <p className="max-w-md text-muted-foreground font-medium mb-8 leading-relaxed">
            The laboratory instance has encountered an unhandled intellectual exception:
            <span className="block mt-2 font-mono text-xs bg-error/5 p-3 rounded-lg border border-error/10 text-error/70">
               {this.state.error?.message || 'NULL_REFERENCE_EXCEPTION'}
            </span>
          </p>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-3 rounded-xl bg-error text-white px-8 py-3 font-bold uppercase text-[10px] tracking-[0.2em] shadow-lg shadow-error/20 hover:scale-105 active:scale-95 transition-all duration-300"
          >
            <RefreshCw size={14} className="animate-spin-slow" />
            Reinitialize Environment
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}