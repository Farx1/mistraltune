"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiClient, Dataset } from "@/lib/api";
import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function NewJobPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [model, setModel] = useState("mistral-small");
  const [trainingId, setTrainingId] = useState("");
  const [validationId, setValidationId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setLoading(true);
        const res = await apiClient.listDatasets();
        const ds = res.datasets ?? [];
        setDatasets(ds);
        if (ds[0]?.id) setTrainingId(String(ds[0].id));
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const options = useMemo(
    () => datasets.map((d: any) => ({ id: String(d.id ?? ""), label: d.filename ?? d.name ?? String(d.id ?? "dataset") })),
    [datasets]
  );

  const submit = async () => {
    try {
      setSubmitting(true);
      setErr(null);

      const payload = {
        model,
        training_file: trainingId,
        validation_file: validationId || undefined,
      };

      const res = await apiClient.createJob(payload);
      const newId = res?.id ?? res?.job?.id;
      window.location.href = newId ? `/jobs/${newId}` : "/jobs";
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageShell
      title="New job"
      subtitle="Create a fine-tuning run using your uploaded datasets."
      right={
        <Button asChild variant="outline" className="border-primary/25 hover:border-primary/40">
          <Link href="/datasets">Upload datasets</Link>
        </Button>
      }
    >
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {err ? (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {err}
            </div>
          ) : null}

          {loading ? (
            <div className="text-sm text-muted-foreground">Loading datasets…</div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border bg-background/60 p-4">
                  <div className="text-xs text-muted-foreground">Base model</div>
                  <Input className="mt-2" value={model} onChange={(e) => setModel(e.target.value)} />
                  <div className="mt-2 text-xs text-muted-foreground">Example: <span className="font-mono">mistral-small</span></div>
                </div>

                <div className="rounded-2xl border bg-background/60 p-4">
                  <div className="text-xs text-muted-foreground">Training dataset</div>
                  <select
                    className="mt-2 h-10 w-full rounded-xl border bg-background/70 px-3 text-sm outline-none focus:border-foreground/30"
                    value={trainingId}
                    onChange={(e) => setTrainingId(e.target.value)}
                  >
                    {options.map((o) => (
                      <option key={o.id} value={o.id}>{o.label}</option>
                    ))}
                  </select>
                </div>

                <div className="rounded-2xl border bg-background/60 p-4 md:col-span-2">
                  <div className="text-xs text-muted-foreground">Validation dataset (optional)</div>
                  <select
                    className="mt-2 h-10 w-full rounded-xl border bg-background/70 px-3 text-sm outline-none focus:border-foreground/30"
                    value={validationId}
                    onChange={(e) => setValidationId(e.target.value)}
                  >
                    <option value="">— none —</option>
                    {options.map((o) => (
                      <option key={o.id} value={o.id}>{o.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button asChild variant="outline" className="border-primary/25 hover:border-primary/40">
                  <Link href="/jobs">Cancel</Link>
                </Button>
                <Button onClick={submit} disabled={submitting || !trainingId}>
                  {submitting ? "Creating…" : "Create job"}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </PageShell>
  );
}
