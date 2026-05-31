'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { reportsApi } from '@/lib/api';
import { ResearchReport } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { FileText, ArrowLeft, Download, Copy, Check, Trash2 } from 'lucide-react';

export default function ReportsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);
  const [copied, setCopied] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

  const handleDeleteReport = async (reportId: string) => {
    if (!window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) return;
    try {
      setDeletingId(reportId);
      await reportsApi.delete(reportId);
      setReports(prev => prev.filter(r => r.id !== reportId));
      if (selectedReport?.id === reportId) setSelectedReport(null);
    } catch (error) {
      console.error('Failed to delete report:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const copyToClipboard = () => {
    if (selectedReport?.content_markdown) {
      navigator.clipboard.writeText(selectedReport.content_markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Reports"
        subtitle={`${reports.length} reports generated`}
      />

      <div className="p-6">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : selectedReport ? (
          <div>
            <div className="flex items-center gap-4 mb-6">
              <Button
                variant="ghost"
                onClick={() => setSelectedReport(null)}
              >
                <ArrowLeft size={18} className="mr-2" />
                Back to reports
              </Button>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900">{selectedReport.title || 'Untitled Report'}</h2>
                <p className="text-sm text-gray-500">{formatDate(selectedReport.created_at)} • {selectedReport.report_type}</p>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={copyToClipboard}>
                  {copied ? <Check size={16} className="mr-2" /> : <Copy size={16} className="mr-2" />}
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
                <Button variant="secondary" size="sm">
                  <Download size={16} className="mr-2" />
                  Export
                </Button>
                <Button variant="danger" size="sm" onClick={() => handleDeleteReport(selectedReport.id)}>
                  <Trash2 size={16} className="mr-2" />
                  Delete
                </Button>
              </div>
            </div>
            <Card className="p-8">
              <div className="prose prose-gray max-w-none">
                <ReactMarkdown>{selectedReport.content_markdown || ''}</ReactMarkdown>
              </div>
            </Card>
          </div>
        ) : reports.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-8 h-8 text-gray-400" />}
            title="No reports yet"
            description="Reports are generated automatically at the end of research runs."
          />
        ) : (
          <Tabs defaultValue="all">
            <TabsList>
              <TabsTrigger value="all">All ({reports.length})</TabsTrigger>
              <TabsTrigger value="cycle">
                Cycle Reports ({reports.filter(r => r.report_type === 'cycle').length})
              </TabsTrigger>
              <TabsTrigger value="milestone">
                Milestones ({reports.filter(r => r.report_type === 'milestone').length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              <div className="space-y-4">
                {reports.map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-6 cursor-pointer"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {report.title || 'Untitled Report'}
                        </h3>
                        <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                          {report.content_markdown}
                        </p>
                        <div className="flex items-center gap-3">
                          <Badge variant="info">{report.report_type}</Badge>
                          <span className="text-sm text-gray-500">{formatDate(report.created_at)}</span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-red-50 text-red-600 shrink-0 ml-4"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        {deletingId === report.id ? (
                          <span className="block w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="cycle">
              <div className="space-y-4">
                {reports.filter(r => r.report_type === 'cycle').map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-6 cursor-pointer"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {report.title || 'Untitled Report'}
                        </h3>
                        <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                          {report.content_markdown}
                        </p>
                        <span className="text-sm text-gray-500">{formatDate(report.created_at)}</span>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-red-50 text-red-600 shrink-0 ml-4"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="milestone">
              <div className="space-y-4">
                {reports.filter(r => r.report_type === 'milestone').map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-6 cursor-pointer"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {report.title || 'Untitled Report'}
                        </h3>
                        <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                          {report.content_markdown}
                        </p>
                        <span className="text-sm text-gray-500">{formatDate(report.created_at)}</span>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-red-50 text-red-600 shrink-0 ml-4"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </Layout>
  );
}
