"use client";

import { useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { Send, Loader2, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [baseModel, setBaseModel] = useState("open-mistral-7b");
  const [fineTunedModel, setFineTunedModel] = useState("");
  const [baseResponse, setBaseResponse] = useState("");
  const [ftResponse, setFtResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Erreur",
        description: "Veuillez entrer un prompt",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setBaseResponse("");
    setFtResponse("");

    try {
      // Générer avec le modèle de base
      const baseResult = await apiClient.generateResponse(baseModel, prompt);
      setBaseResponse(baseResult.content || "");

      // Générer avec le modèle fine-tuné si fourni
      if (fineTunedModel.trim()) {
        const ftResult = await apiClient.generateResponse(fineTunedModel, prompt);
        setFtResponse(ftResult.content || "");
      }
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.message || "Erreur lors de la génération",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Inference Playground</h1>
          <p className="text-muted-foreground">
            Testez et comparez les réponses des modèles en temps réel
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Configurez les modèles et le prompt
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
                <Label htmlFor="ft-model">Modèle fine-tuné (optionnel)</Label>
                <Input
                  id="ft-model"
                  value={fineTunedModel}
                  onChange={(e) => setFineTunedModel(e.target.value)}
                  placeholder="ft:open-mistral-7b:XXX"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Entrez votre prompt ici..."
                  rows={6}
                />
              </div>
              <Button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Génération...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Générer
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Résultats */}
          <div className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Modèle de base
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {loading && !baseResponse ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : baseResponse ? (
                    <div className="prose prose-sm max-w-none">
                      <p className="whitespace-pre-wrap">{baseResponse}</p>
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-8">
                      La réponse apparaîtra ici
                    </p>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {fineTunedModel && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-primary" />
                      Modèle fine-tuné
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {loading && !ftResponse ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                      </div>
                    ) : ftResponse ? (
                      <div className="prose prose-sm max-w-none">
                        <p className="whitespace-pre-wrap">{ftResponse}</p>
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        La réponse apparaîtra ici
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

