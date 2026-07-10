'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from './Badge';
import { AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';

interface DecisionGateProps {
  actionType: 'spend' | 'external_publish' | 'major_pivot' | 'validation' | string;
  costUsd?: number;
  status?: 'pending' | 'approved' | 'rejected';
  description?: string;
  children?: ReactNode;
  className?: string;
}

const getActionConfig = (actionType: string) => {
  switch (actionType) {
    case 'spend':
      return { icon: AlertTriangle, label: 'Cost Threshold', color: 'warning' };
    case 'external_publish':
      return { icon: AlertTriangle, label: 'External Publish', color: 'warning' };
    case 'major_pivot':
      return { icon: AlertTriangle, label: 'Research Pivot', color: 'warning' };
    case 'validation':
      return { icon: CheckCircle, label: 'Validation Required', color: 'primary' };
    default:
      return { icon: AlertTriangle, label: actionType.replace(/_/g, ' '), color: 'warning' };
  }
};

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'approved':
      return { icon: CheckCircle, color: 'success', label: 'Approved' };
    case 'rejected':
      return { icon: XCircle, color: 'error', label: 'Rejected' };
    case 'pending':
    default:
      return { icon: Clock, color: 'warning', label: 'Pending Review' };
  }
};

export function DecisionGate({ actionType, costUsd, status = 'pending', description, children, className }: DecisionGateProps) {
  const actionConfig = getActionConfig(actionType);
  const statusConfig = getStatusConfig(status);
  
  const ActionIcon = actionConfig.icon;
  const StatusIcon = statusConfig.icon;

  // Warning Amber Glow per DESIGN.md section 4.2
  const glowClass = status === 'pending' && (actionType === 'spend' || actionType === 'external_publish' || actionType === 'major_pivot')
    ? 'shadow-[0_0_40px_hsla(var(--warning),0.4)] animate-cognitive-pulse'
    : '';

  return (
    <div className={cn(
      'glass rounded-[2rem] p-8 border-l-4 transition-all duration-500 relative overflow-hidden',
      status === 'pending' ? 'border-warning' : status === 'approved' ? 'border-success' : 'border-error',
      glowClass,
      className
    )}>
      {/* Warning Glow Background */}
      {status === 'pending' && (
        <div className="absolute inset-0 bg-gradient-to-r from-warning/5 to-tertiary/5 opacity-30" />
      )}
      
      <div className="relative z-10 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-xl',
              `bg-${actionConfig.color}/10`
            )}>
              <ActionIcon size={20} className={cn(`text-${actionConfig.color}`)} />
            </div>
            <div>
              <h3 className="text-sm font-black text-foreground uppercase tracking-widest">
                {actionConfig.label}
              </h3>
              {costUsd !== undefined && (
                <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                  Budget: ${costUsd.toFixed(2)}
                </p>
              )}
            </div>
          </div>
          <Badge 
            variant={statusConfig.color as any} 
            className="text-[9px] font-black uppercase tracking-widest px-3 py-1"
          >
            <StatusIcon size={12} className="mr-1" />
            {statusConfig.label}
          </Badge>
        </div>
        
        {description && (
          <p className="text-xs text-muted-foreground/80 font-medium leading-relaxed pl-11">
            {description}
          </p>
        )}
        
        {children && (
          <div className="pl-11 pt-2">
            {children}
          </div>
        )}
      </div>
    </div>
  );
}
