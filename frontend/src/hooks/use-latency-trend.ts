'use client';

import { useEffect, useRef, useCallback } from 'react';

const STORAGE_KEY = 'autoscience_latency_trend';
const MAX_POINTS = 20;

export interface LatencyPoint {
  t: number;  // timestamp (ms)
  v: number;  // latency value (ms)
}

export type LatencyTrend = Record<string, LatencyPoint[]>;

function loadTrend(): LatencyTrend {
  if (typeof window === 'undefined') return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as LatencyTrend;
  } catch {
    return {};
  }
}

function saveTrend(data: LatencyTrend): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // localStorage full or unavailable — silently ignore
  }
}

function prunePoints(points: LatencyPoint[]): LatencyPoint[] {
  // Keep only the most recent MAX_POINTS
  return points.slice(-MAX_POINTS);
}

/**
 * Returns a ref-stable callback that records a latency reading per connector
 * and persists the trend data to localStorage.
 *
 * Call `recordLatency` after each health-check poll with the per-connector
 * latency map. Data is automatically pruned to the most recent N points.
 */
export function useLatencyTrend() {
  // In-memory cache so we avoid parsing localStorage on every call
  const cacheRef = useRef<LatencyTrend>(loadTrend());

  const recordLatency = useCallback((perConnector: Record<string, number>) => {
    const now = Date.now();
    const trend = cacheRef.current;

    for (const [name, latencyMs] of Object.entries(perConnector)) {
      const points = trend[name] ?? [];
      points.push({ t: now, v: latencyMs });
      trend[name] = prunePoints(points);
    }

    cacheRef.current = trend;
    saveTrend(trend);
  }, []);

  const getTrend = useCallback((): LatencyTrend => {
    return cacheRef.current;
  }, []);

  // Sync from localStorage on mount (handles multi-tab)
  useEffect(() => {
    cacheRef.current = loadTrend();
  }, []);

  return { recordLatency, getTrend };
}
