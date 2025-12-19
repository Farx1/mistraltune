"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiClient, Dataset, Job } from "@/lib/api";
import { PageShell } from "@/components/shared/page-shell";
import { BentoGrid, BentoCard } from "@/components/aceternity/bento";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDate } from "@/lib/format";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight, Database, Plus, RefreshCcw, Search } from "lucide-react";

export default function DashboardPage() {
  const reduceMotion = useReducedMotion() ?? false;

  const [jobs, setJobs] = useState<Job[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [softLoading, setSoftLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async (hard: boolean) => {
    try {
      setError(null);
      hard ? setLoading(true) : setSoftLoading(true);
      const [j, d] = await Promise.all([apiClient.listJobs(), apiClient.listDatasets()]);
      setJobs(j.jobs ?? []);
      setDatasets(d.datasets ?? []);
    } catch (e: any) {
      setError(String(e?.message ?? e));
    } finally {
      setLoading(false);
      setSoftLoading(false);
    }
  };

  useEffect(() => {
    load(true);
    const t = setInterval(() => {
      if (document.hidden) return;
      load(false);
    }, 10000);
    return () => clearInterval(t);
  }, []);

  const stats = useMemo(() => {
    const total = jobs.length;
    const active = jobs.filter((x) => ["queued", "running", "validating_files"].includes(x.status)).length;
    const ok = jobs.filter((x) => x.status === "succeeded").length;
    const fail = jobs.filter((x) => x.status === "failed").length;
    const successRate = total ? Math.round((ok / total) * 100) : 0;

    const filtered =
      q.trim().length === 0
        ? jobs
        : jobs.filter((j) => `${j.id} ${j.model} ${j.status} ${j.fine_tuned_model ?? ""}`.toLowerCase().includes(q.toLowerCase()));

    const recent = filtered
      .slice()
      .sort((a, b) => (b.created_at ?? 0) - (a.created_at ?? 0))
      .slice(0, 6);

    return { total, active, ok, fail, successRate, recent, filteredCount: filtered.length };
  }, [jobs, q]);

  return (
    <PageShell
      title="Studio Dashboard"
      subtitle="A clean, Mistral-themed control center for jobs, datasets and quick actions."
      right={
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search jobs…" className="pl-9 w-[280px]" />
          </div>

          <Button variant="outline" className="gap-2 border-primary/25 hover:border-primary/40" onClick={() => load(false)} disabled={loading || softLoading}>
            <RefreshCcw className={softLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            Refresh
          </Button>

          <Button asChild className="gap-2">
            <Link href="/jobs/new">
              <Plus className="h-4 w-4" /> New job
            </Link>
          </Button>
        </div>
      }
    >
      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <BentoGrid className="mt-4">
        <BentoCard className="lg:col-span-3" title="Total jobs" description="All created runs">
          <div className="text-3xl font-bold">{loading ? "—" : stats.total}</div>
        </BentoCard>

        <BentoCard className="lg:col-span-3" title="Active" description="queued / running / validating">
          <div className="text-3xl font-bold">{loading ? "—" : stats.active}</div>
        </BentoCard>

        <BentoCard className="lg:col-span-3" title="Succeeded" description="completed successfully">
          <div className="text-3xl font-bold">{loading ? "—" : stats.ok}</div>
        </BentoCard>

        <BentoCard className="lg:col-span-3" title="Datasets" description="available files">
          <div className="text-3xl font-bold">{loading ? "—" : datasets.length}</div>
        </BentoCard>

        <BentoCard className="lg:col-span-5" title="Health" description="quick stability signal">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Success rate</span>
            <span className="font-semibold">{loading ? "—" : `${stats.successRate}%`}</span>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary" style={{ width: `${stats.successRate}%` }} />
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <div className="rounded-2xl border bg-background/50 p-3">
              <div className="text-xs text-muted-foreground">Failed</div>
              <div className="mt-1 text-lg font-semibold">{loading ? "—" : stats.fail}</div>
            </div>
            <div className="rounded-2xl border bg-background/50 p-3">
              <div className="text-xs text-muted-foreground">Filtered</div>
              <div className="mt-1 text-lg font-semibold">{loading ? "—" : stats.filteredCount}</div>
            </div>
          </div>
        </BentoCard>

        <BentoCard className="lg:col-span-7" title="Quick actions" description="fast navigation">
          <div className="grid gap-3 sm:grid-cols-2">
            <Link href="/jobs/new" className="rounded-2xl border bg-background/60 p-4 hover:bg-accent/40 transition">
              <div className="font-semibold">Create a new job</div>
              <div className="text-sm text-muted-foreground mt-1">Configure model + dataset and launch.</div>
            </Link>
            <Link href="/datasets" className="rounded-2xl border bg-background/60 p-4 hover:bg-accent/40 transition">
              <div className="font-semibold">Manage datasets</div>
              <div className="text-sm text-muted-foreground mt-1">Upload JSONL and reuse across runs.</div>
            </Link>
          </div>
        </BentoCard>
      </BentoGrid>

      <div className="mt-6 grid gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-8 overflow-hidden">
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Recent jobs</CardTitle>
              <div className="text-sm text-muted-foreground">Status-focused list (top 6)</div>
            </div>
            <Button asChild variant="outline" className="border-primary/25 hover:border-primary/40">
              <Link href="/jobs">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : stats.recent.length === 0 ? (
              <div className="rounded-2xl border bg-background/50 p-6 text-center text-muted-foreground">
                No jobs yet.
              </div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence initial={false}>
                  {stats.recent.map((j) => (
                    <motion.div
                      key={j.id}
                      initial={reduceMotion ? undefined : { opacity: 0, y: 10 }}
                      animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                      exit={reduceMotion ? undefined : { opacity: 0, y: 10 }}
                      transition={{ duration: 0.2 }}
                      className="rounded-2xl border bg-background/60 p-4 hover:bg-accent/40 transition"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <div className="font-semibold truncate">{j.model}</div>
                            <StatusBadge status={j.status} />
                          </div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            ID: <span className="font-mono">{j.id.slice(0, 10)}…</span> • Created: {formatDate(j.created_at)}
                          </div>
                        </div>
                        <Button asChild variant="ghost" className="gap-2">
                          <Link href={`/jobs/${j.id}`}>
                            Details <ArrowUpRight className="h-4 w-4 opacity-70" />
                          </Link>
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-4 overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4" /> Datasets
            </CardTitle>
            <div className="text-sm text-muted-foreground">Quick preview</div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : datasets.length === 0 ? (
              <div className="rounded-2xl border bg-background/50 p-6 text-center text-muted-foreground">
                No datasets yet.
              </div>
            ) : (
              <div className="space-y-3">
                {datasets.slice(0, 5).map((d: any) => (
                  <div key={d.id ?? d.filename} className="rounded-2xl border bg-background/60 p-4">
                    <div className="font-semibold truncate">{d.filename ?? d.name ?? "dataset"}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {d.created_at ? `Created: ${formatDate(d.created_at)}` : "—"}
                    </div>
                  </div>
                ))}
                <Button asChild variant="outline" className="w-full border-primary/25 hover:border-primary/40">
                  <Link href="/datasets">Open datasets</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
