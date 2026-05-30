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
      return 'text-green-600 bg-green-100';
    case 'running':
    case 'in_progress':
      return 'text-blue-600 bg-blue-100';
    case 'paused':
    case 'pending':
      return 'text-yellow-600 bg-yellow-100';
    case 'failed':
    case 'rejected':
    case 'denied':
      return 'text-red-600 bg-red-100';
    case 'cancelled':
    case 'archived':
      return 'text-gray-600 bg-gray-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
}

export function getClassificationColor(classification: string): string {
  switch (classification) {
    case 'high_value':
      return 'text-green-700 bg-green-100';
    case 'promising':
      return 'text-blue-700 bg-blue-100';
    case 'incremental':
      return 'text-yellow-700 bg-yellow-100';
    case 'weak':
      return 'text-orange-700 bg-orange-100';
    case 'reject':
      return 'text-red-700 bg-red-100';
    default:
      return 'text-gray-700 bg-gray-100';
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
