import Link from "next/link";
import { PageShell } from "@/components/shared/page-shell";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <PageShell title="Page not found" subtitle="This route does not exist.">
      <div className="rounded-3xl border bg-card/50 p-8 text-center">
        <p className="text-sm text-muted-foreground">Return to the dashboard.</p>
        <div className="mt-5 flex justify-center">
          <Button asChild>
            <Link href="/">Go home</Link>
          </Button>
        </div>
      </div>
    </PageShell>
  );
}

