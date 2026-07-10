'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { PaperComparison } from '@/components/ui/PaperComparison';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, GitCompare } from 'lucide-react';

export default function PaperComparePage() {
  const params = useParams();
  const projectId = params.id as string;

  return (
    <Layout projectId={projectId}>
      <Header
        title="Paper Comparison"
        subtitle="Side-by-side analysis of problem, method, findings, and limitations"
        actions={
          <Link href={`/projects/${projectId}/papers`}>
            <Button variant="secondary" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Papers
            </Button>
          </Link>
        }
      />

      <div className="p-6">
        <div className="flex items-center gap-2 mb-6 text-muted-foreground">
          <GitCompare size={16} />
          <p className="text-sm">
            Compare extracted analysis dimensions across selected papers in your corpus.
          </p>
        </div>
        <PaperComparison projectId={projectId} />
      </div>
    </Layout>
  );
}