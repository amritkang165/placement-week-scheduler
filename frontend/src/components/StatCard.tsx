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
    <div className={cn("border-t border-border pt-4", className)}>
      <p className="label-mono">{label}</p>
      <p className="display mt-3 text-4xl">{value}</p>
      {sub && <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
