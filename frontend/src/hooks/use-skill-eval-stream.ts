'use client';

import { useEffect, useRef } from 'react';
import { useToast } from '@/components/ui/toast';

interface SkillEvalEvent {
  type: string;
  data: {
    evaluated_count?: number;
    deprecated_count?: number;
    retired_count?: number;
    error_count?: number;
    dry_run?: boolean;
    summary?: string;
    run_number?: number;
  };
}

/**
 * Connects to the SSE endpoint for skill evaluation events.
 * Shows toast notifications when the scheduled evaluation completes
 * with deprecations, retirements, or errors.
 */
export function useSkillEvalStream() {
  const { addToast } = useToast();
  const seenEventIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectAttempt = 0;

    function connect() {
      // Close any existing connection
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }

      eventSource = new EventSource('/api/v1/skills/performance/eval-stream');

      eventSource.onopen = () => {
        reconnectAttempt = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const payload: SkillEvalEvent = JSON.parse(event.data);

          // Skip connected/keepalive messages
          if (payload.type === 'connected') return;

          // Deduplicate events by run_number
          const eventId = `eval-${payload.data.run_number}`;
          if (seenEventIdsRef.current.has(eventId)) return;
          seenEventIdsRef.current.add(eventId);

          const { evaluated_count, deprecated_count, retired_count, error_count, dry_run, summary } = payload.data;

          if (payload.type === 'skill_eval_completed') {
            if (deprecated_count && deprecated_count > 0) {
              addToast({
                type: 'warning',
                title: dry_run ? '⚠️ Skills flagged (dry run)' : '🔄 Skills deprecated',
                message: `${deprecated_count} skill${deprecated_count > 1 ? 's' : ''} deprecated, ${retired_count || 0} retired. ${summary || ''}`,
                duration: 8000,
              });
            } else if (retired_count && retired_count > 0) {
              addToast({
                type: 'info',
                title: '🔄 Skills retired',
                message: `${retired_count} skill${retired_count > 1 ? 's' : ''} retired. ${summary || ''}`,
                duration: 6000,
              });
            } else {
              addToast({
                type: 'success',
                title: '✅ Skill evaluation complete',
                message: `${evaluated_count || 0} skills evaluated — all performing adequately.`,
                duration: 5000,
              });
            }
          }

          if (payload.type === 'skill_eval_error') {
            addToast({
              type: 'error',
              title: '❌ Skill evaluation failed',
              message: error_count ? `${error_count} error${error_count > 1 ? 's' : ''} occurred. Check scheduler status for details.` : 'Evaluation cycle encountered an error.',
              duration: 10000,
            });
          }
        } catch {
          // Ignore malformed events
        }
      };

      eventSource.onerror = () => {
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }

        // Exponential backoff reconnect (max 30s)
        const delay = Math.min(1000 * 2 ** reconnectAttempt, 30000);
        reconnectAttempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      };
    }

    // Limit the seen events set to prevent memory leak
    const cleanupInterval = setInterval(() => {
      if (seenEventIdsRef.current.size > 100) {
        seenEventIdsRef.current = new Set(
          Array.from(seenEventIdsRef.current).slice(-50)
        );
      }
    }, 60000);

    connect();

    return () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      clearInterval(cleanupInterval);
    };
  }, [addToast]);
}
