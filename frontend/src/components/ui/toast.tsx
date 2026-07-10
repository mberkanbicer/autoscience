'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextProps {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextProps | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

export function ToastProvider({ children }: { children?: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-full">
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const toastIcons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const toastStyles = {
  success: 'border-success/20 text-success',
  error: 'border-error/20 text-error',
  info: 'border-primary/20 text-primary',
  warning: 'border-warning/20 text-warning',
};

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const Icon = toastIcons[toast.type];

  useEffect(() => {
    if (toast.duration !== 0) {
      const timer = setTimeout(onClose, toast.duration ?? 4000);
      return () => clearTimeout(timer);
    }
  }, [toast.duration, onClose]);

  return (
    <div className={cn(
      'glass rounded-xl p-4 shadow-xl border animate-in slide-in-from-right-full duration-500',
      toastStyles[toast.type]
    )}>
      <div className="flex items-start gap-4">
        <div className={cn(
          'p-2 rounded-lg shadow-inner',
          toast.type === 'success' ? 'bg-success/10' :
          toast.type === 'error' ? 'bg-error/10' :
          toast.type === 'warning' ? 'bg-warning/10' : 'bg-primary/10'
        )}>
          <Icon className="h-5 w-5 flex-shrink-0" />
        </div>
        <div className="flex-1 pt-0.5">
          {toast.title && <p className="font-bold text-sm tracking-tight text-foreground">{toast.title}</p>}
          <p className={cn('text-xs font-medium leading-relaxed opacity-90', toast.title ? 'mt-1 text-muted-foreground' : 'text-foreground')}>
            {toast.message}
          </p>
        </div>
        <button 
          onClick={onClose} 
          className="rounded-lg p-1.5 hover:bg-muted/50 transition-all duration-300 hover:rotate-90 text-muted-foreground/40 hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}