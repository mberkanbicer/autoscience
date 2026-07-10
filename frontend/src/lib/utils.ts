import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
    case 'active':
    case 'approved':
      return 'text-success bg-success/10';
    case 'running':
    case 'in_progress':
      return 'text-primary bg-primary/10';
    case 'paused':
    case 'pending':
      return 'text-warning bg-warning/10';
    case 'failed':
    case 'rejected':
    case 'denied':
      return 'text-error bg-error/10';
    case 'cancelled':
    case 'archived':
      return 'text-muted-foreground bg-muted';
    default:
      return 'text-muted-foreground bg-muted';
  }
}

export function getClassificationColor(classification: string): string {
  switch (classification) {
    case 'high_value':
      return 'text-success bg-success/10';
    case 'promising':
      return 'text-primary bg-primary/10';
    case 'incremental':
      return 'text-warning bg-warning/10';
    case 'weak':
      return 'text-tertiary bg-tertiary/10';
    case 'reject':
      return 'text-error bg-error/10';
    default:
      return 'text-muted-foreground bg-muted';
  }
}

export function formatDuration(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffMs = endDate.getTime() - startDate.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h`;
  if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m`;
  return `${diffMins}m`;
}
