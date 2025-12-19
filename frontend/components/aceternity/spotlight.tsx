import { cn } from "@/lib/utils";

export function Spotlight({
  className,
  from = "rgba(253,111,0,0.18)",
}: {
  className?: string;
  from?: string;
}) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden",
        className
      )}
      aria-hidden="true"
    >
      <div
        className="absolute -top-24 left-1/2 h-[520px] w-[980px] -translate-x-1/2 rounded-full blur-3xl"
        style={{
          background:
            `radial-gradient(circle at 30% 30%, ${from}, transparent 55%),` +
            `radial-gradient(circle at 70% 40%, rgba(253,111,0,0.10), transparent 60%),` +
            `radial-gradient(circle at 50% 70%, rgba(255,255,255,0.06), transparent 65%)`,
        }}
      />
    </div>
  );
}

