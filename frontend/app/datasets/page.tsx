"use client";

import { useEffect, useState, useRef } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient, Dataset } from "@/lib/api";
import { 
  Database, 
  Upload,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await apiClient.listDatasets();
      setDatasets(response.datasets);
    } catch (error) {
      console.error("Error loading datasets:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les datasets",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.jsonl')) {
      toast({
        title: "Erreur",
        description: "Le fichier doit être au format .jsonl",
        variant: "destructive",
      });
      return;
    }

    setUploading(true);
    try {
      const dataset = await apiClient.uploadDataset(file);
      toast({
        title: "Succès",
        description: `Dataset "${dataset.filename}" uploadé avec succès`,
      });
      await loadDatasets();
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.message || "Erreur lors de l'upload",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Datasets</h1>
            <p className="text-muted-foreground">
              Gérez vos fichiers JSONL pour le fine-tuning
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".jsonl"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Upload en cours...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Uploader un dataset
                </>
              )}
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : datasets.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Aucun dataset</h3>
              <p className="text-muted-foreground mb-4">
                Uploader votre premier fichier JSONL pour commencer
              </p>
              <Button onClick={() => fileInputRef.current?.click()}>
                <Upload className="h-4 w-4 mr-2" />
                Uploader un dataset
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {datasets.map((dataset, index) => (
              <motion.div
                key={dataset.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <FileText className="h-8 w-8 text-primary mb-2" />
                      <Badge variant="secondary">{dataset.num_samples} exemples</Badge>
                    </div>
                    <CardTitle className="text-lg">{dataset.filename}</CardTitle>
                    <CardDescription>
                      ID: {dataset.id.slice(0, 12)}...
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Uploadé le:</span>
                        <span>
                          {new Date(dataset.uploaded_at * 1000).toLocaleDateString()}
                        </span>
                      </div>
                      {dataset.metadata && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Taille:</span>
                          <span>
                            {(dataset.metadata.size / 1024).toFixed(2)} KB
                          </span>
                        </div>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      className="w-full mt-4"
                      onClick={() => {
                        navigator.clipboard.writeText(dataset.file_id);
                        toast({
                          title: "Copié",
                          description: "File ID copié dans le presse-papier",
                        });
                      }}
                    >
                      Copier File ID
                    </Button>
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

