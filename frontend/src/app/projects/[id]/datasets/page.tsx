"use client";

import { useParams } from "next/navigation";
import { Layout } from "@/components/layout/Layout";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { DatasetBrowser } from "@/components/ui/DatasetBrowser";
import { datasetsApi } from "@/lib/api";
import { Database, Download, RefreshCw, Upload, Loader2, AlertCircle, CheckCircle2, FileText, Table } from "lucide-react";
import { useState, useRef } from "react";

export default function DatasetsPage() {
  const params = useParams();
  const projectId = params.id as string;

  const handleExport = (format: "json" | "csv") => {
    window.open(datasetsApi.exportUrl(projectId, format), "_blank");
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('project_id', projectId);
      formData.append('file', file);
      const result = await datasetsApi.upload(formData);
      setUploadResult(result);
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Dataset Discovery"
        subtitle="Search, upload, and import datasets for validation experiments"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => setUploadOpen(true)}>
              <Upload className="h-4 w-4 mr-2" />
              Upload CSV/JSON
            </Button>
            <Badge variant="info" className="uppercase text-[10px] font-black tracking-widest">
              <Database className="h-3 w-3 mr-1" />
              Validation Data
            </Badge>
          </div>
        }
      />

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search & Discovery */}
          <div className="lg:col-span-2">
            <Card className="glass">
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Search Datasets</h3>
                <DatasetBrowser projectId={projectId} />
              </div>
            </Card>
          </div>

          {/* Quick Stats & Upload */}
          <div className="space-y-4">
            <Card className="glass">
              <div className="p-6">
                <h3 className="text-sm font-medium text-stone-600 mb-3">Sources</h3>
                <div className="space-y-2">
                  <Badge variant="default" className="w-full justify-start">
                    <Database className="h-3 w-3 mr-1" /> HuggingFace Datasets
                  </Badge>
                  <Badge variant="default" className="w-full justify-start">
                    <Database className="h-3 w-3 mr-1" /> Zenodo
                  </Badge>
                  <Badge variant="default" className="w-full justify-start opacity-50">
                    <Database className="h-3 w-3 mr-1" /> Kaggle (API key required)
                  </Badge>
                </div>
              </div>
            </Card>

            <Card className="glass">
              <div className="p-6">
                <h3 className="text-sm font-medium text-stone-600 mb-3">Export Options</h3>
                <div className="space-y-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => handleExport("csv")}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export as CSV
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => handleExport("json")}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export as JSON
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={handleRefresh}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh Metadata
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={uploadOpen}
        onClose={() => { setUploadOpen(false); setUploadResult(null); setUploadError(null); }}
        title="Upload Dataset"
        size="lg"
      >
        <div className="space-y-6">
          <div
            className="border-2 border-dashed border-border/30 rounded-2xl p-12 text-center cursor-pointer hover:border-primary/40 transition-colors group"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json,.jsonl"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(file);
              }}
            />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-sm font-medium text-muted-foreground">Uploading and validating...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="h-10 w-10 text-muted-foreground/40 group-hover:text-primary/60 transition-colors" />
                <p className="text-sm font-medium text-muted-foreground">
                  Drop a <strong>.csv</strong>, <strong>.json</strong>, or <strong>.jsonl</strong> file here
                </p>
                <p className="text-xs text-muted-foreground/50">or click to browse</p>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="flex items-start gap-3 p-4 bg-error/5 border border-error/20 rounded-xl">
              <AlertCircle size={18} className="text-error shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-error">Upload Error</p>
                <p className="text-xs text-muted-foreground mt-1">{uploadError}</p>
              </div>
            </div>
          )}

          {uploadResult && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-success/5 border border-success/20 rounded-xl">
                <CheckCircle2 size={18} className="text-success shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-success">Upload Successful</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Dataset &ldquo;{uploadResult.name}&rdquo; imported with {uploadResult.row_count} rows and {uploadResult.column_count} columns.
                  </p>
                </div>
              </div>

              {uploadResult.warnings?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-bold text-warning uppercase tracking-wider">Warnings</p>
                  {uploadResult.warnings.map((w: string, i: number) => (
                    <p key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                      <AlertCircle size={12} className="text-warning shrink-0 mt-0.5" />
                      {w}
                    </p>
                  ))}
                </div>
              )}

              {uploadResult.preview_rows?.length > 0 && (
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider mb-2 text-muted-foreground">
                    Preview ({uploadResult.preview_rows.length} rows)
                  </p>
                  <div className="overflow-x-auto rounded-xl border border-border/10">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-stone-50 dark:bg-stone-900">
                          {Object.keys(uploadResult.preview_rows[0]).map((col) => (
                            <th key={col} className="text-left px-3 py-2 font-bold text-muted-foreground uppercase tracking-wider">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {uploadResult.preview_rows.map((row: any, i: number) => (
                          <tr key={i} className="border-t border-border/5 hover:bg-stone-50/50 dark:hover:bg-stone-900/50">
                            {Object.values(row).map((val: any, j: number) => (
                              <td key={j} className="px-3 py-2 text-muted-foreground truncate max-w-[200px]">
                                {String(val).substring(0, 80)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <Button className="w-full" onClick={() => { setUploadOpen(false); setUploadResult(null); handleRefresh(); }}>
                Done
              </Button>
            </div>
          )}
        </div>
      </Modal>
    </Layout>
  );
}