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
import { reportsApi, exportReportUrl } from '@/lib/api';
import { ResearchReport } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { useArtifact } from '@/lib/ArtifactContext';
import { FileText, ArrowLeft, Download, Copy, Check, Trash2, Box, ArrowRight, DollarSign, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ReportsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { openArtifact } = useArtifact();
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
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row md:items-center gap-6 mb-8 bg-white/40 backdrop-blur-md p-6 rounded-2xl border border-border/10 shadow-sm">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelectedReport(null)}
                className="w-fit"
              >
                <ArrowLeft size={16} className="mr-2" />
                Back to Archive
              </Button>
              <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold text-foreground tracking-tight truncate">{selectedReport.title || 'Synthetic Report'}</h2>
                <div className="flex items-center gap-3 mt-1">
                   <Badge variant="info" className="bg-primary/5 uppercase text-[9px] font-bold tracking-widest">{selectedReport.report_type}</Badge>
                   <span className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">{formatDate(selectedReport.created_at)}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="ghost" size="sm" onClick={() => openArtifact({
                  id: selectedReport.id,
                  type: 'latex',
                  title: selectedReport.title || 'Report LaTeX',
                  content: selectedReport.content_markdown || ''
                })} className="rounded-xl hover:bg-primary/5">
                  <Box size={16} className="mr-2 text-primary" />
                  Artifact
                </Button>
                <Button variant="secondary" size="sm" onClick={copyToClipboard} className="rounded-xl">
                  {copied ? <Check size={16} className="mr-2 text-success" /> : <Copy size={16} className="mr-2 text-primary" />}
                  {copied ? 'Copied' : 'Copy MD'}
                </Button>
                <div className="flex gap-1 p-1 bg-muted/30 rounded-xl border border-border/5">
                  <a href={exportReportUrl(selectedReport.id, 'markdown')} download
                     className="p-2 rounded-lg text-primary hover:bg-white/60 transition-all" title="Download Markdown">
                    <Download size={14} />
                  </a>
                  <a href={exportReportUrl(selectedReport.id, 'html')} download
                     className="p-2 rounded-lg text-primary hover:bg-white/60 transition-all" title="Download HTML">
                    <div className="text-[10px] font-bold">HTML</div>
                  </a>
                  <a href={exportReportUrl(selectedReport.id, 'json')} download
                     className="p-2 rounded-lg text-primary hover:bg-white/60 transition-all" title="Download JSON">
                    <div className="text-[10px] font-bold">JSON</div>
                  </a>
                </div>
                <Button variant="danger" size="sm" onClick={() => handleDeleteReport(selectedReport.id)} className="rounded-xl">
                  <Trash2 size={16} className="mr-2" />
                  Purge
                </Button>
              </div>
            </div>
            <Card className="glass overflow-hidden border-border/5">
              <div className="p-12 prose prose-slate max-w-none prose-headings:tracking-tight prose-headings:font-bold prose-p:leading-relaxed prose-p:font-medium prose-p:text-foreground/80">
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
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {reports.map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-8 cursor-pointer group transition-all duration-500 hover:scale-[1.02]"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-3">
                           <Badge variant="info" className="bg-primary/5 uppercase text-[9px] font-bold tracking-widest">{report.report_type}</Badge>
                           <span className="text-[10px] font-bold text-muted-foreground/30 uppercase tracking-widest">{formatDate(report.created_at)}</span>
                        </div>
                        <h3 className="text-xl font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">
                          {report.title || 'Synthetic Research Report'}
                        </h3>
                        <p className="text-muted-foreground text-sm font-medium line-clamp-2 leading-relaxed mb-6">
                          {report.content_markdown}
                        </p>
                        <div className="pt-4 border-t border-border/5 flex items-center justify-between">
                           <span className="text-[10px] font-bold text-primary/60 uppercase tracking-[0.2em] group-hover:text-primary transition-colors">Analyze Full Report</span>
                           <ArrowRight size={14} className="text-primary/0 group-hover:text-primary/40 transition-all group-hover:translate-x-1" />
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-error/10 text-error shrink-0 ml-4 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        {deletingId === report.id ? (
                          <span className="block w-4 h-4 border-2 border-error/40 border-t-error rounded-full animate-spin" />
                        ) : (
                          <Trash2 size={18} />
                        )}
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="cycle">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {reports.filter(r => r.report_type === 'cycle').map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-8 cursor-pointer group transition-all duration-500 hover:scale-[1.02]"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">
                          {report.title || 'Synthetic Cycle Report'}
                        </h3>
                        <p className="text-muted-foreground text-sm font-medium line-clamp-2 leading-relaxed mb-6">
                          {report.content_markdown}
                        </p>
                        <div className="flex items-center justify-between pt-4 border-t border-border/5">
                           <span className="text-[10px] font-bold text-muted-foreground/30 uppercase tracking-widest">{formatDate(report.created_at)}</span>
                           <div className="p-1.5 bg-primary/5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:translate-x-1">
                              <ArrowRight size={14} className="text-primary/60" />
                           </div>
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-error/10 text-error shrink-0 ml-4 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="milestone">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {reports.filter(r => r.report_type === 'milestone').map((report) => (
                  <Card
                    key={report.id}
                    hover
                    className="p-8 cursor-pointer group transition-all duration-500 hover:scale-[1.02]"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-foreground tracking-tight group-hover:text-primary transition-colors mb-3">
                          {report.title || 'Synthetic Milestone Report'}
                        </h3>
                        <p className="text-muted-foreground text-sm font-medium line-clamp-2 leading-relaxed mb-6">
                          {report.content_markdown}
                        </p>
                        <div className="flex items-center justify-between pt-4 border-t border-border/5">
                           <span className="text-[10px] font-bold text-muted-foreground/30 uppercase tracking-widest">{formatDate(report.created_at)}</span>
                           <div className="p-1.5 bg-primary/5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:translate-x-1">
                              <ArrowRight size={14} className="text-primary/60" />
                           </div>
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                        className="p-2 rounded-lg hover:bg-error/10 text-error shrink-0 ml-4 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0"
                        title="Delete report"
                        disabled={deletingId === report.id}
                      >
                        <Trash2 size={18} />
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
