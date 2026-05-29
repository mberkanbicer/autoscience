'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { questionsApi } from '@/lib/api';
import { ResearchQuestion } from '@/lib/types';

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
    <Layout>
      <Header title="Research Questions" />

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : questions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No questions found</div>
        ) : (
          <div className="space-y-4">
            {questions.map((question, index) => (
              <div
                key={question.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          question.status === 'selected'
                            ? 'bg-green-100 text-green-800'
                            : question.status === 'rejected'
                            ? 'bg-red-100 text-red-800'
                            : question.status === 'hypothesis_created'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {question.status}
                      </span>
                      {question.rank && (
                        <span className="text-sm text-gray-500">
                          Rank: {question.rank.toFixed(2)}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-800">{question.question}</p>
                    {question.rejection_reason && (
                      <p className="text-sm text-red-600 mt-2">
                        Rejection reason: {question.rejection_reason}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
