"use client";

import { useState } from "react";
import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState("Write a short onboarding email for a new employee.");
  const [output, setOutput] = useState<string>("");

  return (
    <PageShell
      title="Playground"
      subtitle="A simple UI stub you can connect to an inference endpoint later."
    >
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Prompt</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          <div className="flex gap-2">
            <Button onClick={() => setOutput(`(Demo) Output for: "${prompt}"\n\nHook this to your inference route.`)}>
              Run
            </Button>
            <Button variant="outline" onClick={() => setOutput("")} className="border-primary/25 hover:border-primary/40">
              Clear
            </Button>
          </div>

          {output ? (
            <pre className="rounded-2xl border bg-card p-4 text-sm whitespace-pre-wrap">{output}</pre>
          ) : null}
        </CardContent>
      </Card>
    </PageShell>
  );
}
