import { cn } from "@/lib/utils";

export function BentoGrid({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("grid gap-4 lg:grid-cols-12", className)}>{children}</div>;
}

export function BentoCard({
  className,
  title,
  description,
  children,
}: {
  className?: string;
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className={cn("relative overflow-hidden rounded-3xl border bg-card/60 p-5 backdrop-blur", className)}>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent" />
      <div className="relative">
        <div className="text-sm font-semibold">{title}</div>
        {description ? <div className="mt-1 text-sm text-muted-foreground">{description}</div> : null}
        {children ? <div className="mt-4">{children}</div> : null}
      </div>
    </div>
  );
}

