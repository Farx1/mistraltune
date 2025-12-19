"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient, Dataset } from "@/lib/api";
import { Loader2, Zap } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function NewJobPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    model: "open-mistral-7b",
    training_file_id: "",
    validation_file_id: "",
    learning_rate: "1e-4",
    epochs: "3",
    batch_size: "",
    suffix: "",
    job_type: "mistral_api",
  });

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await apiClient.listDatasets();
      setDatasets(response.datasets);
    } catch (error) {
      console.error("Error loading datasets:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await apiClient.createJob({
        model: formData.model,
        training_file_id: formData.training_file_id,
        validation_file_id: formData.validation_file_id || undefined,
        learning_rate: parseFloat(formData.learning_rate),
        epochs: parseInt(formData.epochs),
        batch_size: formData.batch_size ? parseInt(formData.batch_size) : undefined,
        suffix: formData.suffix || undefined,
        job_type: formData.job_type,
      });

      toast({
        title: "Succès",
        description: "Job créé avec succès",
      });

      router.push(`/jobs/${response.job_id}`);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.message || "Erreur lors de la création du job",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8 max-w-3xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Créer un nouveau job</h1>
          <p className="text-muted-foreground">
            Configurez et lancez un job de fine-tuning
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Configuration du job</CardTitle>
              <CardDescription>
                Remplissez les informations pour créer un nouveau job de fine-tuning
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="model">Modèle de base</Label>
                <Input
                  id="model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="open-mistral-7b"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="training_file">Fichier d'entraînement *</Label>
                <Select
                  value={formData.training_file_id}
                  onValueChange={(value) => setFormData({ ...formData, training_file_id: value })}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.file_id}>
                        {dataset.filename} ({dataset.num_samples} exemples)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="validation_file">Fichier de validation (optionnel)</Label>
                <Select
                  value={formData.validation_file_id}
                  onValueChange={(value) => setFormData({ ...formData, validation_file_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un dataset (optionnel)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Aucun</SelectItem>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.file_id}>
                        {dataset.filename} ({dataset.num_samples} exemples)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="learning_rate">Learning rate</Label>
                  <Input
                    id="learning_rate"
                    type="text"
                    value={formData.learning_rate}
                    onChange={(e) => setFormData({ ...formData, learning_rate: e.target.value })}
                    placeholder="1e-4"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="epochs">Epochs</Label>
                  <Input
                    id="epochs"
                    type="number"
                    value={formData.epochs}
                    onChange={(e) => setFormData({ ...formData, epochs: e.target.value })}
                    placeholder="3"
                    min="1"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="batch_size">Batch size (optionnel)</Label>
                  <Input
                    id="batch_size"
                    type="number"
                    value={formData.batch_size}
                    onChange={(e) => setFormData({ ...formData, batch_size: e.target.value })}
                    placeholder="Auto"
                    min="1"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="suffix">Suffixe (optionnel)</Label>
                  <Input
                    id="suffix"
                    value={formData.suffix}
                    onChange={(e) => setFormData({ ...formData, suffix: e.target.value })}
                    placeholder="domain-qa"
                  />
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                >
                  Annuler
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Création...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Créer le job
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </main>
    </div>
  );
}

