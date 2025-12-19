"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ArrowUpRight, Moon, Sun, Plus } from "lucide-react";
import { SiteContainer } from "@/components/shared/site-container";

type NavItem = { label: string; href: string };

export default function Navbar() {
  const pathname = usePathname();
  const nav: NavItem[] = useMemo(
    () => [
      { label: "Dashboard", href: "/" },
      { label: "Jobs", href: "/jobs" },
      { label: "Datasets", href: "/datasets" },
      { label: "Playground", href: "/playground" },
      { label: "Comparison", href: "/comparison" },
    ],
    []
  );

  const [dark, setDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const saved = localStorage.getItem("theme");
    const isDark = saved ? saved === "dark" : root.classList.contains("dark");
    setDark(isDark);
    root.classList.toggle("dark", isDark);
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <header className="sticky top-0 z-50 border-b bg-background/70 backdrop-blur-xl">
      <div className="h-px w-full bg-linear-to-r from-transparent via-primary/60 to-transparent" />

      <SiteContainer className="flex h-16 items-center justify-between gap-3">
        <Link href="/" className="group inline-flex items-center gap-2">
          <span className="relative grid h-9 w-9 place-items-center rounded-xl border bg-card">
            <span className="absolute inset-0 rounded-xl bg-primary/15 blur-md opacity-0 transition-opacity group-hover:opacity-100" />
            <span className="relative h-3 w-3 rounded-full bg-primary" />
          </span>
          <div className="leading-tight">
            <div className="font-semibold tracking-tight">MistralTune</div>
            <div className="text-xs text-muted-foreground">Studio Console</div>
          </div>
        </Link>

        <nav className="hidden lg:flex items-center gap-1 rounded-full border bg-card/40 p-1">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-4 py-2 text-sm transition",
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={toggle} className="border-primary/25 hover:border-primary/40">
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          <Button asChild className="hidden sm:inline-flex gap-2">
            <Link href="/jobs/new">
              <Plus className="h-4 w-4" /> New job
            </Link>
          </Button>

          <Button asChild variant="outline" className="hidden md:inline-flex gap-2 border-primary/25 hover:border-primary/40">
            <a href="https://github.com/Farx1/mistraltune" target="_blank" rel="noreferrer">
              GitHub <ArrowUpRight className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </SiteContainer>

      <div className="lg:hidden border-t bg-background/70">
        <SiteContainer className="flex gap-2 overflow-x-auto py-2">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "whitespace-nowrap rounded-full border px-3 py-1.5 text-sm",
                  active ? "border-primary/40 bg-primary/10 text-foreground" : "border-border text-muted-foreground"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </SiteContainer>
      </div>
    </header>
  );
}
