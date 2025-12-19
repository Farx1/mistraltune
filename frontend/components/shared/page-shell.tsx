import { Spotlight } from "@/components/aceternity/spotlight";
import { DotGrid } from "@/components/aceternity/dot-grid";
import { SiteContainer } from "@/components/shared/site-container";

export function PageShell({
  title,
  subtitle,
  right,
  children,
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <main className="relative">
      <Spotlight />
      <DotGrid />

      <SiteContainer className="relative py-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            {subtitle ? <p className="mt-1 text-muted-foreground">{subtitle}</p> : null}
          </div>
          {right ? <div>{right}</div> : null}
        </div>

        <div className="mt-6">{children}</div>
      </SiteContainer>
    </main>
  );
}

