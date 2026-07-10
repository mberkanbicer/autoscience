'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { activityApi } from '@/lib/api';

const PROJECT_PATH = /^\/projects\/([^/]+)/;

/** Track user activity for idle-research triggers on any project route. */
export function useActivityHeartbeat() {
  const pathname = usePathname();
  const projectId = pathname.match(PROJECT_PATH)?.[1];

  useEffect(() => {
    if (!projectId) return;

    const trackActivity = () => {
      activityApi.track(projectId).catch(() => {});
    };

    trackActivity();

    const handleFocus = () => trackActivity();
    window.addEventListener('focus', handleFocus);

    const interval = setInterval(trackActivity, 30_000);

    return () => {
      window.removeEventListener('focus', handleFocus);
      clearInterval(interval);
    };
  }, [projectId]);
}