'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Bell } from 'lucide-react';
import { collaborationApi } from '@/lib/api';
import { useToast } from '@/components/ui/toast';
import type { ReviewNotification } from '@/lib/types';
import { cn } from '@/lib/utils';

const READ_KEY = 'autoscience_read_notifications';

function getReadIds(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    return new Set(JSON.parse(localStorage.getItem(READ_KEY) || '[]'));
  } catch {
    return new Set();
  }
}

function markRead(ids: string[]) {
  const existing = getReadIds();
  ids.forEach((id) => existing.add(id));
  localStorage.setItem(READ_KEY, JSON.stringify(Array.from(existing)));
}

interface NotificationBellProps {
  projectId: string;
  compact?: boolean;
}

export function NotificationBell({ projectId, compact }: NotificationBellProps) {
  const [notifications, setNotifications] = useState<ReviewNotification[]>([]);
  const [open, setOpen] = useState(false);
  const seenRef = useRef<Set<string>>(new Set());
  const { addToast } = useToast();

  const load = useCallback(async () => {
    try {
      const data = await collaborationApi.notifications(projectId);
      const read = getReadIds();
      const unread = data.filter((n) => !read.has(n.id));
      setNotifications(unread);

      for (const n of unread) {
        if (!seenRef.current.has(n.id)) {
          seenRef.current.add(n.id);
          addToast({
            type: 'info',
            title: 'Review assigned',
            message: n.title,
            duration: 6000,
          });
        }
      }
    } catch {
      /* not signed in or no access */
    }
  }, [projectId, addToast]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, [load]);

  const unreadCount = notifications.length;

  if (compact && unreadCount === 0) return null;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'relative p-2 rounded-xl hover:bg-muted transition-colors',
          unreadCount > 0 && 'text-primary',
        )}
        aria-label={`${unreadCount} unread notifications`}
      >
        <Bell size={compact ? 18 : 20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-primary text-stone-900 text-[10px] font-black flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      {open && unreadCount > 0 && (
        <div className="absolute right-0 mt-2 w-72 glass rounded-2xl border border-border/10 shadow-2xl p-3 z-50">
          <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">
            Review Assignments
          </p>
          <ul className="space-y-2 max-h-48 overflow-y-auto">
            {notifications.map((n) => (
              <li key={n.id}>
                <Link
                  href={`/projects/${projectId}/team`}
                  className="block p-2 rounded-lg hover:bg-primary/5 text-sm"
                  onClick={() => {
                    markRead([n.id]);
                    setNotifications((prev) => prev.filter((x) => x.id !== n.id));
                    setOpen(false);
                  }}
                >
                  {n.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}