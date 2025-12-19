"use client";

import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { apiClient, Job } from "@/lib/api";
import { 
  Zap, 
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Filter
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filterJobs();
  }, [jobs, searchQuery, statusFilter]);

  const loadJobs = async () => {
    try {
      const response = await apiClient.listJobs();
      setJobs(response.jobs);
    } catch (error) {
      console.error("Error loading jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterJobs = () => {
    let filtered = jobs;

    if (statusFilter !== "all") {
      filtered = filtered.filter((job) => job.status === statusFilter);
    }

    if (searchQuery) {
      filtered = filtered.filter(
        (job) =>
          job.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          job.model.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredJobs(filtered);
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

  const statusCounts = {
    all: jobs.length,
    succeeded: jobs.filter((j) => j.status === "succeeded").length,
    running: jobs.filter((j) => j.status === "running" || j.status === "queued" || j.status === "validating_files").length,
    failed: jobs.filter((j) => j.status === "failed").length,
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Jobs de Fine-tuning</h1>
            <p className="text-muted-foreground">
              Gérez et suivez vos jobs de fine-tuning
            </p>
          </div>
          <Link href="/jobs/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nouveau job
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Rechercher par ID ou modèle..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex gap-2">
                {["all", "succeeded", "running", "failed"].map((status) => (
                  <Button
                    key={status}
                    variant={statusFilter === status ? "default" : "outline"}
                    onClick={() => setStatusFilter(status)}
                    className="capitalize"
                  >
                    {status === "all" ? "Tous" : status}
                    {statusCounts[status as keyof typeof statusCounts] > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {statusCounts[status as keyof typeof statusCounts]}
                      </Badge>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Jobs List */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : filteredJobs.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <Zap className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Aucun job trouvé</h3>
              <p className="text-muted-foreground mb-4">
                {jobs.length === 0
                  ? "Créez votre premier job de fine-tuning"
                  : "Aucun job ne correspond à vos filtres"}
              </p>
              {jobs.length === 0 && (
                <Link href="/jobs/new">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Créer un job
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredJobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-semibold text-lg">{job.model}</span>
                          {getStatusBadge(job.status)}
                          <Badge variant="outline">{job.job_type}</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground space-y-1">
                          <div>ID: {job.id}</div>
                          <div>
                            Créé le {new Date(job.created_at * 1000).toLocaleString()}
                          </div>
                          {job.fine_tuned_model && (
                            <div className="text-primary font-medium">
                              Modèle fine-tuné: {job.fine_tuned_model}
                            </div>
                          )}
                          {job.error && (
                            <div className="text-destructive">
                              Erreur: {job.error}
                            </div>
                          )}
                        </div>
                        {job.config && (
                          <div className="mt-3 flex gap-4 text-sm">
                            <span>LR: {job.config.learning_rate}</span>
                            <span>Epochs: {job.config.epochs}</span>
                            {job.config.batch_size && (
                              <span>Batch: {job.config.batch_size}</span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Link href={`/jobs/${job.id}`}>
                          <Button variant="outline" size="sm">
                            Détails
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

