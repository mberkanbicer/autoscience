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
import { MessageSquare, Hash, TrendingUp, Trash2, XCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function QuestionsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [questions, setQuestions] = useState<ResearchQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this question?')) return;
    setDeletingId(id);
    try {
      await questionsApi.reject(id, 'Deleted by user');
      setQuestions(questions.filter(q => q.id !== id));
    } catch (error) {
      console.error('Failed to delete question:', error);
    } finally {
      setDeletingId(null);
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
          <div className="grid gap-6">
            {questions.map((question, index) => (
              <Card key={question.id} className="p-8 group transition-all duration-500 hover:scale-[1.01]">
                <div className="flex items-start gap-8">
                  <div className="w-14 h-14 bg-tertiary/10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner group-hover:bg-tertiary/20 transition-all duration-500">
                    <span className="text-tertiary font-extrabold text-2xl">{index + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1">
                    <p className="text-lg font-bold text-foreground/80 tracking-tight leading-relaxed mb-6">{question.question}</p>
                    <div className="flex items-center gap-4 flex-wrap">
                      <StatusBadge status={question.status} />
                      {question.rank && (
                        <Badge variant="purple" className="bg-tertiary/5 uppercase text-[9px] font-bold tracking-[0.2em] px-3 py-1">
                          <TrendingUp size={12} className="mr-2" />
                          Rank #{question.rank}
                        </Badge>
                      )}
                      <span className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">
                        Recorded {formatDate(question.created_at)}
                      </span>
                      <button
                        onClick={() => handleDelete(question.id)}
                        disabled={deletingId === question.id}
                        className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300 hover:scale-110 disabled:opacity-30 ml-auto"
                        title="Invalidate Question"
                      >
                        {deletingId === question.id ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={20} />}
                      </button>
                    </div>
                    {question.rejection_reason && (
                      <div className="mt-6 p-5 bg-error/5 rounded-2xl border border-error/10 flex items-start gap-4">
                         <div className="p-1.5 bg-error/10 rounded-lg">
                            <XCircle size={16} className="text-error" />
                         </div>
                         <div>
                            <span className="text-[10px] font-bold text-error uppercase tracking-widest">Scientific Disqualification</span>
                            <p className="text-xs font-medium text-error/80 mt-1.5 leading-relaxed">{question.rejection_reason}</p>
                         </div>
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
