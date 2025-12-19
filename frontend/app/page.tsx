"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient, Job, Dataset } from "@/lib/api";
import { 
  Zap, 
  Database, 
  TrendingUp, 
  Clock,
  CheckCircle2,
  XCircle,
  Loader2
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalJobs: 0,
    activeJobs: 0,
    completedJobs: 0,
    totalDatasets: 0,
  });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [jobsRes, datasetsRes] = await Promise.all([
        apiClient.listJobs(),
        apiClient.listDatasets(),
      ]);

      setJobs(jobsRes.jobs);
      setDatasets(datasetsRes.datasets);

      const activeJobs = jobsRes.jobs.filter(
        (j) => j.status === "validating_files" || j.status === "queued" || j.status === "running"
      ).length;
      const completedJobs = jobsRes.jobs.filter(
        (j) => j.status === "succeeded"
      ).length;

      setStats({
        totalJobs: jobsRes.jobs.length,
        activeJobs,
        completedJobs,
        totalDatasets: datasetsRes.datasets.length,
      });
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; icon: any }> = {
      succeeded: { variant: "default", icon: CheckCircle2 },
      failed: { variant: "destructive", icon: XCircle },
      running: { variant: "secondary", icon: Loader2 },
      queued: { variant: "outline", icon: Clock },
      validating_files: { variant: "outline", icon: Loader2 },
    };

    const config = variants[status] || { variant: "outline" as const, icon: Clock };
    const Icon = config.icon || Clock;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    );
  };

  const recentJobs = jobs.slice(0, 5);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Vue d'ensemble de vos jobs de fine-tuning et datasets
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalJobs}</div>
                <p className="text-xs text-muted-foreground">
                  Tous les jobs créés
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Jobs Actifs</CardTitle>
                <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.activeJobs}</div>
                <p className="text-xs text-muted-foreground">
                  En cours d'exécution
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Jobs Terminés</CardTitle>
                <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.completedJobs}</div>
                <p className="text-xs text-muted-foreground">
                  Avec succès
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Datasets</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalDatasets}</div>
                <p className="text-xs text-muted-foreground">
                  Fichiers uploadés
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Recent Jobs */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Jobs Récents</CardTitle>
                <CardDescription>
                  Derniers jobs de fine-tuning créés
                </CardDescription>
              </div>
              <Link href="/jobs">
                <Button variant="outline">Voir tout</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : recentJobs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Aucun job pour le moment. Créez votre premier job de fine-tuning!
              </div>
            ) : (
              <div className="space-y-4">
                {recentJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{job.model}</span>
                        {getStatusBadge(job.status)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ID: {job.id.slice(0, 8)}... | Créé le{" "}
                        {new Date(job.created_at * 1000).toLocaleDateString()}
                      </div>
                      {job.fine_tuned_model && (
                        <div className="text-sm text-muted-foreground mt-1">
                          Modèle: {job.fine_tuned_model}
                        </div>
                      )}
                    </div>
                    <Link href={`/jobs/${job.id}`}>
                      <Button variant="ghost" size="sm">
                        Voir détails
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Créer un nouveau job</CardTitle>
              <CardDescription>
                Lancez un fine-tuning avec l'API Mistral
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/jobs/new">
                <Button className="w-full">Créer un job</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Uploader un dataset</CardTitle>
              <CardDescription>
                Ajoutez un nouveau fichier JSONL pour l'entraînement
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/datasets">
                <Button variant="outline" className="w-full">
                  Gérer les datasets
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
