"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Layout } from "@/components/layout/Layout";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { ManuscriptEditor } from "@/components/ui/ManuscriptEditor";
import { DatasetBrowser } from "@/components/ui/DatasetBrowser";
import { ExperimentTelemetry, ExperimentData } from "@/components/common/ExperimentTelemetry";
import { AnalysisToolsPanel } from "@/components/common/AnalysisToolsPanel";
import { GenerateManuscriptButton } from "@/components/ui/GenerateManuscriptButton";
import { runsApi } from "@/lib/api";
import { FileText, Database, Beaker } from "lucide-react";

export default function ArticleStudioPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [latestRunId, setLatestRunId] = useState<string | undefined>();
  const [manuscriptRefreshKey, setManuscriptRefreshKey] = useState(0);
  const [experiment, setExperiment] = useState<ExperimentData | null>(null);
  const [loadingExperiment, setLoadingExperiment] = useState(false);

  useEffect(() => {
    runsApi
      .list(projectId, { state: "completed" })
      .then((runs) => {
        if (runs[0]) {
          setLatestRunId(runs[0].id);
        }
      })
      .catch(console.error);
  }, [projectId]);

  useEffect(() => {
    if (!latestRunId) {
      setExperiment(null);
      return;
    }

    setLoadingExperiment(true);
    runsApi
      .experiment(latestRunId)
      .then((data) => setExperiment(data as unknown as ExperimentData))
      .catch(console.error)
      .finally(() => setLoadingExperiment(false));
  }, [latestRunId]);

  const exportExperimentOutput = () => {
    if (!experiment?.stdout) return;
    const blob = new Blob([experiment.stdout], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `experiment_${latestRunId?.slice(0, 8) || "output"}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Article Studio"
        subtitle="Write, analyze, and publish your scientific findings"
        actions={
          <div className="flex gap-2 items-center">
            {latestRunId && (
              <Badge variant="info" className="uppercase text-[10px] font-black tracking-widest">
                Run {latestRunId.slice(0, 8)}
              </Badge>
            )}
            <Badge variant="info" className="uppercase text-[10px] font-black tracking-widest">
              IMRaD Format
            </Badge>
            <Badge variant="success" className="uppercase text-[10px] font-black tracking-widest">
              LaTeX Ready
            </Badge>
          </div>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="manuscript" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="manuscript" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />              Manuscript
            </TabsTrigger>
            <TabsTrigger value="datasets" className="flex items-center gap-2">
              <Database className="h-4 w-4" /> Datasets
            </TabsTrigger>
            <TabsTrigger value="experiments" className="flex items-center gap-2">
              <Beaker className="h-4 w-4" /> Experiments
            </TabsTrigger>
          </TabsList>

          <TabsContent value="manuscript" className="mt-6 space-y-4">
            {latestRunId ? (
              <>
                <div className="flex justify-end">
                  <GenerateManuscriptButton
                    runId={latestRunId}
                    projectId={projectId}
                    onGenerated={() => setManuscriptRefreshKey((key) => key + 1)}
                  />
                </div>
                <ManuscriptEditor
                  key={manuscriptRefreshKey}
                  projectId={projectId}
                  runId={latestRunId}
                />
              </>
            ) : (
              <Card className="glass p-8 text-center">
                <p className="text-stone-600">
                  Complete a research run to generate a manuscript with real experiment results and citations.
                </p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="datasets" className="mt-6">
            <DatasetBrowser projectId={projectId} />
          </TabsContent>

          <TabsContent value="experiments" className="mt-6 space-y-4">
            {latestRunId ? (
              <>
                <ExperimentTelemetry
                  experiment={experiment}
                  loading={loadingExperiment}
                  onExport={exportExperimentOutput}
                />
                <AnalysisToolsPanel projectId={projectId} runId={latestRunId} />
              </>
            ) : (
              <Card className="glass p-8 text-center">
                <Beaker className="h-12 w-12 text-amber-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold mb-2">No Completed Runs</h3>
                <p className="text-stone-600">
                  Run a validation cycle to populate experiment telemetry here.
                </p>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}