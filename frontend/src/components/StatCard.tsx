import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-border bg-card p-5 shadow-card", className)}>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mono mt-3 text-3xl font-bold leading-none tracking-tight">{value}</p>
      {sub && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
