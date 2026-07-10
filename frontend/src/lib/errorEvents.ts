// Global event emitter for API errors.
// This module is safe to import from non-React code (e.g. api.ts).
// React components subscribe via onApiError() and use useToast() to display them.

type ErrorListener = (message: string, status: number) => void;
type Unsubscribe = () => void;

let listeners: ErrorListener[] = [];

export function emitApiError(message: string, status: number): void {
  for (const fn of listeners) {
    try {
      fn(message, status);
    } catch {
      // Never let a listener crash the emitter
    }
  }
}

export function onApiError(fn: ErrorListener): Unsubscribe {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}
