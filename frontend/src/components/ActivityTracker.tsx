'use client';

import { useActivityHeartbeat } from '@/hooks/use-activity-heartbeat';

/** Invisible component that records project activity for idle-research triggers. */
export function ActivityTracker() {
  useActivityHeartbeat();
  return null;
}