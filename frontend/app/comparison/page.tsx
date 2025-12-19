"use client";

import { useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient, InferenceResult } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2, TrendingUp, FileText } from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

export default function ComparisonPage() {
  const [baseModel, setBaseModel] = useState("open-mistral-7b");
  const [fineTunedModel, setFineTunedModel] = useState("");
  const [prompts, setPrompts] = useState("");
  const [results, setResults] = useState<InferenceResult[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleCompare = async () => {
    if (!prompts.trim() || !fineTunedModel.trim()) {
      toast({
        title: "Erreur",
        description: "Veuillez remplir tous les champs",
        variant: "destructive",
      });
      return;
    }

    const promptList = prompts.split("\n").filter((p) => p.trim());
    if (promptList.length === 0) {
      toast({
        title: "Erreur",
        description: "Veuillez entrer au moins un prompt",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setResults([]);

    try {
      const response = await apiClient.compareModels({
        base_model: baseModel,
        fine_tuned_model: fineTunedModel,
        prompts: promptList,
      });
      setResults(response.results);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.message || "Erreur lors de la comparaison",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const chartData = results.map((r, i) => ({
    name: `Prompt ${i + 1}`,
    "Base Model": r.base_length,
    "Fine-tuned": r.ft_length,
    "Base Tokens": r.base_tokens,
    "FT Tokens": r.ft_tokens,
  }));

  const avgBaseLength = results.length > 0
    ? results.reduce((sum, r) => sum + r.base_length, 0) / results.length
    : 0;
  const avgFtLength = results.length > 0
    ? results.reduce((sum, r) => sum + r.ft_length, 0) / results.length
    : 0;
  const avgBaseTokens = results.length > 0
    ? results.reduce((sum, r) => sum + r.base_tokens, 0) / results.length
    : 0;
  const avgFtTokens = results.length > 0
    ? results.reduce((sum, r) => sum + r.ft_tokens, 0) / results.length
    : 0;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Comparaison de Modèles</h1>
          <p className="text-muted-foreground">
            Comparez les performances de deux modèles sur plusieurs prompts
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Configurez les modèles et les prompts à comparer
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="base-model">Modèle de base</Label>
                <Input
                  id="base-model"
                  value={baseModel}
                  onChange={(e) => setBaseModel(e.target.value)}
                  placeholder="open-mistral-7b"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ft-model">Modèle fine-tuné</Label>
                <Input
                  id="ft-model"
                  value={fineTunedModel}
                  onChange={(e) => setFineTunedModel(e.target.value)}
                  placeholder="ft:open-mistral-7b:XXX"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prompts">Prompts (un par ligne)</Label>
                <Textarea
                  id="prompts"
                  value={prompts}
                  onChange={(e) => setPrompts(e.target.value)}
                  placeholder="Qu'est-ce que le PTO ?&#10;Define KPI in one sentence.&#10;..."
                  rows={8}
                />
              </div>
              <Button
                onClick={handleCompare}
                disabled={loading || !prompts.trim() || !fineTunedModel.trim()}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Comparaison en cours...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Comparer
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Statistiques */}
          {results.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Statistiques</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Longueur moyenne</div>
                    <div className="text-2xl font-bold">{avgBaseLength.toFixed(0)}</div>
                    <div className="text-xs text-muted-foreground">Base</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Longueur moyenne</div>
                    <div className="text-2xl font-bold text-primary">{avgFtLength.toFixed(0)}</div>
                    <div className="text-xs text-muted-foreground">Fine-tuné</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Tokens moyens</div>
                    <div className="text-2xl font-bold">{avgBaseTokens.toFixed(0)}</div>
                    <div className="text-xs text-muted-foreground">Base</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Tokens moyens</div>
                    <div className="text-2xl font-bold text-primary">{avgFtTokens.toFixed(0)}</div>
                    <div className="text-xs text-muted-foreground">Fine-tuné</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Graphiques */}
        {results.length > 0 && (
          <div className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Comparaison des Longueurs</CardTitle>
                <CardDescription>
                  Longueur des réponses en caractères
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Base Model" fill="#8884d8" />
                    <Bar dataKey="Fine-tuned" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Comparaison des Tokens</CardTitle>
                <CardDescription>
                  Nombre de tokens utilisés
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Base Tokens" fill="#8884d8" />
                    <Bar dataKey="FT Tokens" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Résultats détaillés */}
        {results.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Résultats Détaillés</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {results.map((result, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border rounded-lg p-4 space-y-3"
                  >
                    <div className="font-semibold">Prompt {index + 1}: {result.prompt}</div>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm font-medium mb-2">Modèle de base</div>
                        <div className="text-sm text-muted-foreground bg-muted p-3 rounded">
                          {result.base_response || "Erreur: " + result.base_error}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          {result.base_length} caractères, {result.base_tokens} tokens
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium mb-2">Modèle fine-tuné</div>
                        <div className="text-sm text-muted-foreground bg-muted p-3 rounded">
                          {result.ft_response || "Erreur: " + result.ft_error}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          {result.ft_length} caractères, {result.ft_tokens} tokens
                          {result.length_diff !== 0 && (
                            <span className={result.length_diff > 0 ? "text-green-600" : "text-red-600"}>
                              {" "}({result.length_diff > 0 ? "+" : ""}{result.length_diff})
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

