"use client";

import { PageShell } from "@/components/shared/page-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ComparisonPage() {
  return (
    <PageShell
      title="Comparison"
      subtitle="Structure-ready page for evaluating base vs fine-tuned outputs."
    >
      <div className="grid gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-6 overflow-hidden">
          <CardHeader><CardTitle>Base model</CardTitle></CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Add your prompt + response evaluation here.
          </CardContent>
        </Card>
        <Card className="lg:col-span-6 overflow-hidden">
          <CardHeader><CardTitle>Fine-tuned model</CardTitle></CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Add your fine-tuned run + scoring here.
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
