"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { datasetsApi } from "@/lib/api";
import { Loader2, Search, Database, ExternalLink, Plus, Eye } from "lucide-react";

interface Dataset {
  id: string;
  name: string;
  description: string;
  source_url: string;
  format: string;
  row_count?: number;
  column_count?: number;
  size_bytes?: number;
  tags?: string[];
  connector?: string;
  schema_json?: Record<string, unknown>;
  doi?: string;
}

interface DatasetBrowserProps {
  projectId: string;
}

function formatBytes(bytes?: number): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export function DatasetBrowser({ projectId }: DatasetBrowserProps) {
  const [query, setQuery] = useState("");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewDataset, setPreviewDataset] = useState<Dataset | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  const searchDatasets = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const results = await datasetsApi.search(query.trim());
      setDatasets(results as unknown as Dataset[]);
    } catch (error) {
      console.error("Dataset search failed:", error);
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  };

  const openPreview = async (dataset: Dataset) => {
    if (!dataset.connector) return;

    setPreviewOpen(true);
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewDataset(dataset);

    try {
      const detail = (await datasetsApi.previewExternal(
        dataset.connector,
        dataset.id,
      )) as unknown as Dataset;
      setPreviewDataset({ ...dataset, ...detail, connector: dataset.connector });
    } catch {
      setPreviewError("Could not load full dataset details. Showing search result.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const addDataset = async (dataset: Dataset) => {
    setAddingId(dataset.id);
    try {
      await datasetsApi.create({
        project_id: projectId,
        name: dataset.name,
        description: dataset.description,
        source_url: dataset.source_url,
        format: dataset.format,
        row_count: dataset.row_count,
        column_count: dataset.column_count,
        size_bytes: dataset.size_bytes,
        schema_json: dataset.schema_json,
      });
    } catch (error) {
      console.error("Failed to add dataset:", error);
    } finally {
      setAddingId(null);
    }
  };

  const schemaEntries = previewDataset?.schema_json
    ? Object.entries(previewDataset.schema_json)
    : [];

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search datasets (e.g., 'climate temperature', 'image classification')"
          className="flex-1"
          onKeyDown={(e) => e.key === "Enter" && searchDatasets()}
        />
        <Button onClick={searchDatasets} disabled={loading || !query.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
          Search
        </Button>
      </div>

      {datasets.length > 0 && (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {datasets.map((dataset) => (
            <Card key={`${dataset.connector}-${dataset.id}`} className="p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Database className="h-4 w-4 text-amber-600 shrink-0" />
                    <h3 className="font-semibold text-foreground truncate">{dataset.name}</h3>
                    {dataset.connector && (
                      <Badge variant="info" size="sm">
                        {dataset.connector}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-stone-600 line-clamp-2 mb-2">
                    {dataset.description || "No description available"}
                  </p>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-stone-500">
                    <span>Format: {dataset.format || "unknown"}</span>
                    {dataset.row_count ? (
                      <span>Rows: {dataset.row_count.toLocaleString()}</span>
                    ) : null}
                    {dataset.tags && dataset.tags.length > 0 && (
                      <span>Tags: {dataset.tags.slice(0, 3).join(", ")}</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1 ml-2 shrink-0">
                  {dataset.connector && (
                    <Button size="sm" variant="ghost" onClick={() => openPreview(dataset)}>
                      <Eye className="h-3 w-3 mr-1" />
                      Preview
                    </Button>
                  )}
                  {dataset.source_url && (
                    <a
                      href={dataset.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-stone-400 hover:text-amber-600 transition-colors"
                      aria-label="Open source"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => addDataset(dataset)}
                    disabled={addingId === dataset.id}
                  >
                    {addingId === dataset.id ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <Plus className="h-3 w-3 mr-1" />
                    )}
                    Add
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {datasets.length === 0 && query && !loading && (
        <p className="text-center text-stone-500 py-8">No datasets found. Try a different search.</p>
      )}

      <Modal
        isOpen={previewOpen}
        onClose={() => {
          setPreviewOpen(false);
          setPreviewDataset(null);
          setPreviewError(null);
        }}
        title={previewDataset?.name || "Dataset Preview"}
        size="lg"
      >
        {previewLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
          </div>
        ) : previewDataset ? (
          <div className="space-y-4">
            {previewError && (
              <p className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">{previewError}</p>
            )}

            <div className="flex flex-wrap gap-2">
              {previewDataset.connector && (
                <Badge variant="info">{previewDataset.connector}</Badge>
              )}
              {previewDataset.format && <Badge variant="default">{previewDataset.format}</Badge>}
              {previewDataset.tags?.map((tag) => (
                <Badge key={tag} variant="purple" size="sm">
                  {tag}
                </Badge>
              ))}
            </div>

            <p className="text-sm text-stone-600 whitespace-pre-wrap">
              {previewDataset.description || "No description available."}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div className="glass rounded-lg p-3">
                <p className="text-xs text-stone-500 uppercase tracking-wide">Rows</p>
                <p className="font-semibold">{previewDataset.row_count?.toLocaleString() ?? "—"}</p>
              </div>
              <div className="glass rounded-lg p-3">
                <p className="text-xs text-stone-500 uppercase tracking-wide">Columns</p>
                <p className="font-semibold">{previewDataset.column_count ?? "—"}</p>
              </div>
              <div className="glass rounded-lg p-3">
                <p className="text-xs text-stone-500 uppercase tracking-wide">Size</p>
                <p className="font-semibold">{formatBytes(previewDataset.size_bytes)}</p>
              </div>
              <div className="glass rounded-lg p-3">
                <p className="text-xs text-stone-500 uppercase tracking-wide">ID</p>
                <p className="font-semibold truncate text-xs" title={previewDataset.id}>
                  {previewDataset.id}
                </p>
              </div>
            </div>

            {previewDataset.doi && (
              <p className="text-xs text-stone-500">
                DOI: <span className="font-mono">{previewDataset.doi}</span>
              </p>
            )}

            {schemaEntries.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Schema</h4>
                <div className="max-h-48 overflow-y-auto rounded-lg border border-stone-200">
                  <table className="w-full text-xs">
                    <thead className="bg-stone-50 sticky top-0">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium">Field</th>
                        <th className="text-left px-3 py-2 font-medium">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {schemaEntries.map(([field, meta]) => (
                        <tr key={field} className="border-t border-stone-100">
                          <td className="px-3 py-2 font-mono">{field}</td>
                          <td className="px-3 py-2 text-stone-600">
                            {typeof meta === "object" && meta !== null && "dtype" in meta
                              ? String((meta as { dtype?: string }).dtype)
                              : typeof meta === "string"
                                ? meta
                                : JSON.stringify(meta)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {previewDataset.source_url && (
              <a
                href={previewDataset.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-amber-700 hover:text-amber-800"
              >
                <ExternalLink className="h-4 w-4" />
                Open on source site
              </a>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}