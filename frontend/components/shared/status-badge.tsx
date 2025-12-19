import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Loader2, Clock, Ban, HelpCircle } from "lucide-react";

export function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toLowerCase();

  const map: Record<string, { label: string; cls: string; Icon: any }> = {
    succeeded: { label: "Succeeded", cls: "border-primary/25 bg-primary/10 text-foreground", Icon: CheckCircle2 },
    running: { label: "Running", cls: "border-border bg-muted/40 text-foreground", Icon: Loader2 },
    queued: { label: "Queued", cls: "border-border bg-background/50 text-muted-foreground", Icon: Clock },
    validating_files: { label: "Validating", cls: "border-border bg-background/50 text-muted-foreground", Icon: Loader2 },
    failed: { label: "Failed", cls: "border-destructive/30 bg-destructive/10 text-destructive", Icon: XCircle },
    cancelled: { label: "Cancelled", cls: "border-border bg-background/50 text-muted-foreground", Icon: Ban },
  };

  const cfg = map[s] ?? { label: status, cls: "border-border bg-background/50 text-muted-foreground", Icon: HelpCircle };

  return (
    <Badge variant="outline" className={cn("gap-1.5 rounded-full", cfg.cls)}>
      <cfg.Icon className={cn("h-3.5 w-3.5", s === "running" || s === "validating_files" ? "animate-spin" : "")} />
      {cfg.label}
    </Badge>
  );
}

