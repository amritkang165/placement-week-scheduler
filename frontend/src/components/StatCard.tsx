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
    <div className={cn("rounded-xl border border-border bg-muted/50 p-4", className)}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mono mt-1.5 text-2xl font-bold leading-none tracking-tight">{value}</p>
      {sub && <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
