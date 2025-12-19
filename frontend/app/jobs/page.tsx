"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiClient, Job } from "@/lib/api";
import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDate } from "@/lib/format";
import { ArrowUpRight, Plus, Search } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setLoading(true);
        const res = await apiClient.listJobs();
        setJobs(res.jobs ?? []);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    const arr = s
      ? jobs.filter((j) => `${j.id} ${j.model} ${j.status} ${j.fine_tuned_model ?? ""}`.toLowerCase().includes(s))
      : jobs;
    return arr.slice().sort((a, b) => (b.created_at ?? 0) - (a.created_at ?? 0));
  }, [jobs, q]);

  return (
    <PageShell
      title="Jobs"
      subtitle="Browse all fine-tuning runs."
      right={
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search…" className="pl-9 w-[260px]" />
          </div>
          <Button asChild className="gap-2">
            <Link href="/jobs/new">
              <Plus className="h-4 w-4" /> New job
            </Link>
          </Button>
        </div>
      }
    >
      <Card className="overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Runs</CardTitle>
          <div className="text-sm text-muted-foreground">{filtered.length} item(s)</div>
        </CardHeader>
        <CardContent>
          {err ? (
            <div className="mb-4 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {err}
            </div>
          ) : null}

          {loading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="rounded-2xl border bg-background/50 p-6 text-center text-muted-foreground">
              No jobs found.
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((j) => (
                <div key={j.id} className="rounded-2xl border bg-background/60 p-4 hover:bg-accent/40 transition">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="font-semibold truncate">{j.model}</div>
                        <StatusBadge status={j.status} />
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        ID: <span className="font-mono">{j.id.slice(0, 10)}…</span> • Created: {formatDate(j.created_at)}
                      </div>
                      {j.fine_tuned_model ? (
                        <div className="mt-1 text-sm text-muted-foreground">
                          Fine-tuned: <span className="font-mono">{j.fine_tuned_model}</span>
                        </div>
                      ) : null}
                    </div>
                    <Button asChild variant="ghost" className="gap-2">
                      <Link href={`/jobs/${j.id}`}>
                        Details <ArrowUpRight className="h-4 w-4 opacity-70" />
                      </Link>
                    </Button>
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
