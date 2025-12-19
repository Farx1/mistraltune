"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiClient, Job } from "@/lib/api";
import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDate } from "@/lib/format";
import { ArrowLeft, Ban } from "lucide-react";

export default function JobDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [canceling, setCanceling] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setLoading(true);
        const j = await apiClient.getJob(id);
        setJob(j);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const cancel = async () => {
    try {
      setCanceling(true);
      await apiClient.cancelJob(id);
      const j = await apiClient.getJob(id);
      setJob(j);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setCanceling(false);
    }
  };

  return (
    <PageShell
      title="Job details"
      subtitle={`ID: ${id}`}
      right={
        <div className="flex gap-2">
          <Button asChild variant="outline" className="gap-2 border-primary/25 hover:border-primary/40">
            <Link href="/jobs">
              <ArrowLeft className="h-4 w-4" /> Back
            </Link>
          </Button>
          <Button onClick={cancel} disabled={canceling || !job || ["succeeded", "failed", "cancelled"].includes(job.status)} className="gap-2">
            <Ban className="h-4 w-4" />
            {canceling ? "Canceling…" : "Cancel job"}
          </Button>
        </div>
      }
    >
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>
          {err ? (
            <div className="mb-4 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {err}
            </div>
          ) : null}

          {loading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : !job ? (
            <div className="rounded-2xl border bg-background/50 p-6 text-center text-muted-foreground">
              Not found.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border bg-background/60 p-4">
                <div className="text-xs text-muted-foreground">Base model</div>
                <div className="mt-1 font-semibold">{job.model}</div>
              </div>

              <div className="rounded-2xl border bg-background/60 p-4">
                <div className="text-xs text-muted-foreground">Status</div>
                <div className="mt-2">
                  <StatusBadge status={job.status} />
                </div>
              </div>

              <div className="rounded-2xl border bg-background/60 p-4">
                <div className="text-xs text-muted-foreground">Created</div>
                <div className="mt-1 font-semibold">{formatDate(job.created_at)}</div>
              </div>

              <div className="rounded-2xl border bg-background/60 p-4">
                <div className="text-xs text-muted-foreground">Fine-tuned model</div>
                <div className="mt-1 font-semibold">{job.fine_tuned_model ?? "—"}</div>
              </div>

              <div className="md:col-span-2 rounded-2xl border bg-background/60 p-4">
                <div className="text-xs text-muted-foreground">Raw payload</div>
                <pre className="mt-3 max-h-[420px] overflow-auto rounded-2xl bg-card p-4 text-xs">
                  {JSON.stringify(job, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </PageShell>
  );
}
