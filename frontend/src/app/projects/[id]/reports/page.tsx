'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { reportsApi } from '@/lib/api';
import { ResearchReport } from '@/lib/types';
import { formatDate, truncate } from '@/lib/utils';

export default function ReportsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);

  useEffect(() => {
    loadReports();
  }, [projectId]);

  const loadReports = async () => {
    try {
      const data = await reportsApi.list(projectId);
      setReports(data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Header title="Reports" />

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No reports found</div>
        ) : selectedReport ? (
          <div>
            <button
              onClick={() => setSelectedReport(null)}
              className="mb-4 text-blue-600 hover:text-blue-800"
            >
              ← Back to reports
            </button>
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-2xl font-bold mb-4">{selectedReport.title}</h2>
              <div className="text-sm text-gray-500 mb-4">
                {formatDate(selectedReport.created_at)} | {selectedReport.report_type}
              </div>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm">
                  {selectedReport.content_markdown}
                </pre>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition cursor-pointer"
                onClick={() => setSelectedReport(report)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">
                      {report.title || 'Untitled Report'}
                    </h3>
                    <p className="text-gray-600 text-sm mb-2">
                      {truncate(report.content_markdown || '', 200)}
                    </p>
                    <div className="text-sm text-gray-500">
                      {formatDate(report.created_at)} | {report.report_type}
                    </div>
                  </div>
                  <span className="text-blue-600">View →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
