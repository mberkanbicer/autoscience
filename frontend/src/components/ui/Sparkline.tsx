'use client';

import { useRef } from 'react';
import { cn } from '@/lib/utils';

let _instanceCounter = 0;
function nextId(): string {
  _instanceCounter += 1;
  return `sparkline-${_instanceCounter}`;
}

interface SparklinePoint {
  t: number;
  v: number;
}

interface SparklineProps {
  /** Time-ordered series of data points to render. */
  data: SparklinePoint[];
  /** If < 2 points the sparkline renders a flat line. */
  width?: number;
  /** Height of the SVG viewport. */
  height?: number;
  /** Color when latency is good (default green). */
  colorGood?: string;
  /** Color when latency is moderate (default amber). */
  colorMid?: string;
  /** Color when latency is high (default red). */
  colorBad?: string;
  /** Optional class name override. */
  className?: string;
  /** Badge showing latest value inside the sparkline. */
  showValue?: boolean;
}

/**
 * A tiny, dependency-free SVG sparkline that visualises a time-series
 * of latency values.  Colours shift from green → amber → red as values
 * increase, using 300 ms / 1000 ms thresholds.
 */
export function Sparkline({
  data,
  width = 60,
  height = 20,
  colorGood = '#22c55e',
  colorMid = '#eab308',
  colorBad = '#ef4444',
  className,
  showValue = false,
}: SparklineProps) {
  const uid = useRef(nextId());
  if (data.length === 0) {
    return (
      <svg
        width={width}
        height={height}
        className={cn('shrink-0', className)}
        viewBox={`0 0 ${width} ${height}`}
      >
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="currentColor"
          strokeWidth={1}
          opacity={0.15}
          className="text-muted-foreground"
        />
      </svg>
    );
  }

  // Determine the latest value for colour selection
  const lastValue = data[data.length - 1].v;
  const strokeColor = lastValue < 300 ? colorGood : lastValue < 1000 ? colorMid : colorBad;

  if (data.length === 1) {
    // Single point — draw a flat line at the value's Y position
    const vy = valueToY(data[0].v, data[0].v, data[0].v, height);
    return (
      <svg
        width={width}
        height={height}
        className={cn('shrink-0', className)}
        viewBox={`0 0 ${width} ${height}`}
      >
        <line
          x1={0}
          y1={vy}
          x2={width}
          y2={vy}
          stroke={strokeColor}
          strokeWidth={1.5}
          strokeLinecap="round"
        />
      </svg>
    );
  }

  const xs = pointsToPath(data, width, height);

  return (
    <svg
      width={width}
      height={height}
      className={cn('shrink-0 overflow-visible', className)}
      viewBox={`0 0 ${width} ${height}`}
    >
      {/* Gradient fill under the line — unique id per instance */}
      <defs>
        <linearGradient id={uid.current} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={strokeColor} stopOpacity={0.3} />
          <stop offset="100%" stopColor={strokeColor} stopOpacity={0.02} />
        </linearGradient>
      </defs>
      <path
        d={`${xs} L ${width} ${height} L 0 ${height} Z`}
        fill={`url(#${uid.current})`}
        opacity={0.6}
      />
      <path
        d={xs}
        fill="none"
        stroke={strokeColor}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Latest value badge inside the sparkline */}
      {showValue && (
        <text
          x={width - 4}
          y={10}
          textAnchor="end"
          fontSize={8}
          fontWeight={700}
          fill={strokeColor}
          className="tabular-nums"
        >
          {lastValue.toFixed(0)}
        </text>
      )}

      {/* Dot at the latest point */}
      {data.length >= 2 && (() => {
        const last = data[data.length - 1];
        const px = ((data.length - 1) / (data.length - 1)) * (width - 4) + 2;
        const py = valueToY(last.v, minOf(data), maxOf(data), height);
        return (
          <circle
            cx={px}
            cy={py}
            r={2}
            fill={strokeColor}
            stroke="white"
            strokeWidth={1}
          />
        );
      })()}
    </svg>
  );
}

// ── Pure helpers ──────────────────────────────────────────────────────────

function minOf(points: SparklinePoint[]): number {
  let m = points[0].v;
  for (let i = 1; i < points.length; i++) {
    if (points[i].v < m) m = points[i].v;
  }
  return m;
}

function maxOf(points: SparklinePoint[]): number {
  let m = points[0].v;
  for (let i = 1; i < points.length; i++) {
    if (points[i].v > m) m = points[i].v;
  }
  return m;
}

function valueToY(value: number, min: number, max: number, height: number): number {
  if (max === min) return height / 2;
  // Invert so high values are at the top (small y)
  const ratio = (value - min) / (max - min);
  return height - 4 - ratio * (height - 8);
}

function pointsToPath(data: SparklinePoint[], width: number, height: number): string {
  const len = data.length;
  if (len < 2) return '';

  const min = minOf(data);
  const max = maxOf(data);
  const stepX = (width - 4) / (len - 1);

  const parts: string[] = [];
  for (let i = 0; i < len; i++) {
    const x = i * stepX + 2;
    const y = valueToY(data[i].v, min, max, height);
    parts.push(`${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`);
  }
  return parts.join(' ');
}
