'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { questionsApi } from '@/lib/api';
import { ResearchQuestion } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { MessageSquare, Hash, TrendingUp } from 'lucide-react';

export default function QuestionsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [questions, setQuestions] = useState<ResearchQuestion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuestions();
  }, [projectId]);

  const loadQuestions = async () => {
    try {
      const data = await questionsApi.list(projectId);
      setQuestions(data);
    } catch (error) {
      console.error('Failed to load questions:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Research Questions"
        subtitle={`${questions.length} questions identified`}
      />

      <div className="p-6">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : questions.length === 0 ? (
          <EmptyState
            icon={<MessageSquare className="w-8 h-8 text-gray-400" />}
            title="No questions yet"
            description="Research questions are generated from literature conflicts and gaps."
          />
        ) : (
          <div className="space-y-4">
            {questions.map((question, index) => (
              <Card key={question.id} className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-purple-600 font-bold">{index + 1}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium mb-2">{question.question}</p>
                    <div className="flex items-center gap-3 flex-wrap">
                      <StatusBadge status={question.status} />
                      {question.rank && (
                        <Badge variant="purple">
                          <TrendingUp size={12} className="mr-1" />
                          Rank #{question.rank}
                        </Badge>
                      )}
                      <span className="text-xs text-gray-400">
                        {formatDate(question.created_at)}
                      </span>
                    </div>
                    {question.rejection_reason && (
                      <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
                        <p className="text-sm text-red-700">
                          <span className="font-medium">Rejection reason:</span> {question.rejection_reason}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
