'use client';

import { useEffect } from 'react';
import { useToast } from '@/components/ui/toast';
import { onApiError } from '@/lib/errorEvents';

/**
 * Subscribes to global API error events and shows user-facing toasts.
 *
 * This component should be rendered once inside <ToastProvider> in the
 * app provider tree.  It has no visible UI of its own.
 */
export function GlobalErrorToast() {
  const { addToast } = useToast();

  useEffect(() => {
    const unsub = onApiError((message, status) => {
      // Determine a user-friendly title based on the status code
      const title =
        status === 404
          ? 'Resource not found'
          : status === 429
            ? 'Rate limited'
            : status >= 500
              ? 'Server error'
              : `Request failed (${status})`;

      addToast({
        type: 'error',
        title,
        message: message.slice(0, 300), // cap message length
        duration: 6000, // slightly longer for errors
      });
    });

    return unsub;
  }, [addToast]);

  return null;
}
