'use client';

import { ErrorBoundary } from './ErrorBoundary';
import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

export const ErrorBoundaryWrapper = ({ children }: Props) => <ErrorBoundary>{children}</ErrorBoundary>;