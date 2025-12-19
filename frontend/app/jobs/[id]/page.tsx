"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiClient, Job } from "@/lib/api";
import { 
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Zap,
  Copy
} from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadJob();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [jobId]);

  const loadJob = async () => {
    try {
      const jobData = await apiClient.getJobStatus(jobId);
      setJob(jobData as any);
    } catch (error) {
      console.error("Error loading job:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les détails du job",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const ws = new WebSocket(`${wsUrl}/api/jobs/${jobId}/ws`);
    
    ws.onopen = () => {
      setWsConnected(true);
      wsRef.current = ws;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "status_update") {
        setJob((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            status: data.status,
            fine_tuned_model: data.fine_tuned_model || prev.fine_tuned_model,
            error: data.error || prev.error,
          };
        });

        // Si le job est terminé, arrêter le WebSocket
        if (["succeeded", "failed", "cancelled"].includes(data.status)) {
          ws.close();
          setWsConnected(false);
        }
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      setWsConnected(false);
      // Reconnect after 5 seconds if job is still running
      if (job && !["succeeded", "failed", "cancelled"].includes(job.status)) {
        setTimeout(connectWebSocket, 5000);
      }
    };
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
        {status === "running" && <Icon className="h-3 w-3 animate-spin" />}
        {status !== "running" && <Icon className="h-3 w-3" />}
        {status}
      </Badge>
    );
  };

  const getProgress = (status: string): number => {
    const statusProgress: Record<string, number> = {
      validating_files: 10,
      queued: 20,
      running: 60,
      succeeded: 100,
      failed: 0,
      cancelled: 0,
    };
    return statusProgress[status] || 0;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copié",
      description: "Copié dans le presse-papier",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container py-8">
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </main>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container py-8">
          <Card>
            <CardContent className="py-16 text-center">
              <XCircle className="h-12 w-12 mx-auto mb-4 text-destructive" />
              <h3 className="text-lg font-semibold mb-2">Job non trouvé</h3>
              <Button onClick={() => router.push("/jobs")} className="mt-4">
                Retour aux jobs
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8 max-w-4xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">{job.model}</h1>
              <div className="flex items-center gap-2">
                {getStatusBadge(job.status)}
                <Badge variant="outline">{job.job_type}</Badge>
                {wsConnected && (
                  <Badge variant="secondary" className="gap-1">
                    <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    Live
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Progress */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Progression</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Statut: {job.status}</span>
                <span>{getProgress(job.status)}%</span>
              </div>
              <Progress value={getProgress(job.status)} />
            </div>
          </CardContent>
        </Card>

        {/* Job Info */}
        <div className="grid gap-6 md:grid-cols-2 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Informations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <div className="text-sm text-muted-foreground">Job ID</div>
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono">{job.id}</code>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => copyToClipboard(job.id)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Créé le</div>
                <div className="text-sm">
                  {new Date(job.created_at * 1000).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Dernière mise à jour</div>
                <div className="text-sm">
                  {new Date(job.updated_at * 1000).toLocaleString()}
                </div>
              </div>
              {job.config && (
                <div>
                  <div className="text-sm text-muted-foreground">Configuration</div>
                  <div className="text-sm space-y-1">
                    <div>Learning rate: {job.config.learning_rate}</div>
                    <div>Epochs: {job.config.epochs}</div>
                    {job.config.batch_size && (
                      <div>Batch size: {job.config.batch_size}</div>
                    )}
                    {job.config.suffix && (
                      <div>Suffixe: {job.config.suffix}</div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Résultat</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {job.fine_tuned_model ? (
                <div>
                  <div className="text-sm text-muted-foreground mb-2">Modèle fine-tuné</div>
                  <div className="flex items-center gap-2">
                    <code className="text-sm font-mono flex-1 break-all">
                      {job.fine_tuned_model}
                    </code>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => copyToClipboard(job.fine_tuned_model!)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => router.push(`/playground?model=${encodeURIComponent(job.fine_tuned_model!)}`)}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Tester le modèle
                  </Button>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Le modèle fine-tuné sera disponible une fois le job terminé
                </div>
              )}
              {job.error && (
                <div>
                  <div className="text-sm text-destructive font-medium mb-1">Erreur</div>
                  <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                    {job.error}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => loadJob()}
              >
                Actualiser
              </Button>
              {job.fine_tuned_model && (
                <Button
                  onClick={() => router.push(`/comparison?base=${encodeURIComponent(job.model)}&ft=${encodeURIComponent(job.fine_tuned_model!)}`)}
                >
                  Comparer avec le modèle de base
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

