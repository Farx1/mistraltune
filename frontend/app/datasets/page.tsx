"use client";

import { useEffect, useState } from "react";
import { apiClient, Dataset } from "@/lib/api";
import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate, formatBytes } from "@/lib/format";
import { Upload } from "lucide-react";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    try {
      setErr(null);
      setLoading(true);
      const res = await apiClient.listDatasets();
      setDatasets(res.datasets ?? []);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onUpload = async (file?: File | null) => {
    if (!file) return;
    try {
      setErr(null);
      setUploading(true);
      await apiClient.uploadDataset(file);
      await load();
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setUploading(false);
    }
  };

  return (
    <PageShell
      title="Datasets"
      subtitle="Upload and manage training files."
      right={
        <label className="inline-flex cursor-pointer items-center gap-2">
          <input type="file" className="hidden" accept=".jsonl,.json,.txt" onChange={(e) => onUpload(e.target.files?.[0])} />
          <Button className="gap-2" disabled={uploading}>
            <Upload className="h-4 w-4" />
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </label>
      }
    >
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Files</CardTitle>
          <div className="text-sm text-muted-foreground">{datasets.length} item(s)</div>
        </CardHeader>
        <CardContent>
          {err ? (
            <div className="mb-4 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {err}
            </div>
          ) : null}

          {loading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : datasets.length === 0 ? (
            <div className="rounded-2xl border bg-background/50 p-6 text-center text-muted-foreground">
              No datasets yet. Upload a JSONL file to start.
            </div>
          ) : (
            <div className="space-y-3">
              {datasets.map((d: any) => (
                <div key={d.id ?? d.filename} className="rounded-2xl border bg-background/60 p-4 hover:bg-accent/40 transition">
                  <div className="font-semibold truncate">{d.filename ?? d.name ?? "dataset"}</div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {d.created_at ? `Created: ${formatDate(d.created_at)}` : "Created: —"}
                    {" • "}
                    {d.size_bytes ? `Size: ${formatBytes(d.size_bytes)}` : "Size: —"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </PageShell>
  );
}
