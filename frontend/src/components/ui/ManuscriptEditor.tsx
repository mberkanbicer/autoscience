"use client";

import { useState, useEffect } from "react";
import { Manuscript } from "@/lib/types";
import { manuscriptsApi } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Textarea } from "@/components/ui/Input";
import { ManuscriptPreview } from "@/components/ui/ManuscriptPreview";
import { Loader2, Save, FileText, BookOpen, Code, Download, FileDown } from "lucide-react";
import { clsx } from "clsx";
import { exportManuscriptPdf, exportManuscriptDocx } from "@/lib/manuscriptPdf";

interface ManuscriptEditorProps {
  projectId: string;
  runId?: string;
}

export function ManuscriptEditor({ projectId, runId }: ManuscriptEditorProps) {
  const [manuscript, setManuscript] = useState<Manuscript | null>(null);
  const [latexContent, setLatexContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"latex" | "preview" | "references">("latex");

  useEffect(() => {
    loadManuscript();
  }, [projectId, runId]);

  const loadManuscript = async () => {
    setLoading(true);
    try {
      const manuscripts = await manuscriptsApi.list(projectId, runId);
      if (manuscripts.length > 0) {
        const ms = manuscripts[0];
        setManuscript(ms);
        setLatexContent(ms.content_latex || "");
      } else if (!runId) {
        const newMs = await manuscriptsApi.create({
          project_id: projectId,
          run_id: runId,
          title: "Untitled Manuscript",
        });
        setManuscript(newMs);
      } else {
        setManuscript(null);
        setLatexContent("");
      }
    } catch (error) {
      console.error("Failed to load manuscript:", error);
    } finally {
      setLoading(false);
    }
  };

  const saveManuscript = async () => {
    if (!manuscript) return;
    setSaving(true);
    try {
      await manuscriptsApi.update(manuscript.id, { content_latex: latexContent });
    } catch (error) {
      console.error("Failed to save manuscript:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = (format: "tex" | "bib" | "zip") => {
    if (!manuscript) return;
    window.open(manuscriptsApi.download(manuscript.id, format), "_blank");
  };

  const handleExportPdf = () => {
    if (!manuscript) return;
    exportManuscriptPdf(manuscript, latexContent);
  };

  const handleExportDocx = () => {
    if (!manuscript) return;
    exportManuscriptDocx(manuscript, latexContent);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
      </div>
    );
  }

  if (!manuscript) {
    return <div className="text-center py-8">No manuscript available</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-stone-200">
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-amber-600" />
          <h2 className="text-lg font-semibold">{manuscript.title}</h2>
          <Badge variant={manuscript.status === "draft" ? "default" : "success"}>
            {manuscript.status}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleExport("tex")}>
            <Download className="h-4 w-4 mr-2" />
            Export .tex
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport("bib")}>
            <Download className="h-4 w-4 mr-2" />
            Export .bib
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport("zip")}>
            <Download className="h-4 w-4 mr-2" />
            Export Bundle
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExportDocx}>
            <FileDown className="h-4 w-4 mr-2" />
            Export DOCX
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExportPdf}>
            <FileDown className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
          <Button size="sm" onClick={saveManuscript} disabled={saving}>
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save
          </Button>
        </div>
      </div>

      <div className="flex border-b border-stone-200">
        {(["latex", "preview", "references"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
              activeTab === tab
                ? "border-amber-600 text-amber-700"
                : "border-transparent text-stone-600 hover:text-stone-800"
            )}
          >
            {tab === "latex" && <Code className="h-4 w-4 inline mr-1" />}
            {tab === "preview" && <BookOpen className="h-4 w-4 inline mr-1" />}
            {tab === "references" && <FileText className="h-4 w-4 inline mr-1" />}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {activeTab === "latex" && (
          <Textarea
            value={latexContent}
            onChange={(e) => setLatexContent(e.target.value)}
            placeholder={
              '\\documentclass{article}\n\\begin{document}\n\n\\section{Introduction}\n\n% Write your manuscript here\n\n\\end{document}'
            }
            className="min-h-full font-mono text-sm resize-none"
            rows={30}
          />
        )}

        {activeTab === "preview" && (
          <div className="glass p-6 rounded-lg">
            <ManuscriptPreview latex={latexContent} />
          </div>
        )}

        {activeTab === "references" && (
          <div className="space-y-4">
            {manuscript.bibtex ? (
              <pre className="text-xs bg-stone-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                {manuscript.bibtex}
              </pre>
            ) : (
              <p className="text-stone-500">No references yet. Generate from research papers.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}