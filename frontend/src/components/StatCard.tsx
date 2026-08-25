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
    <div className={cn("rounded-sm border border-border bg-card p-5 shadow-sm", className)}>
      <p className="label-mono">{label}</p>
      <p className="display mt-3 text-4xl leading-none">{value}</p>
      {sub && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
