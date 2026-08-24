import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sub,
  className,
  accent = true,
}: {
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        "relative rounded-lg border border-border bg-card px-5 pb-5 pt-4",
        className,
      )}
    >
      {accent && <span className="absolute left-5 top-0 h-0.5 w-8 rounded-full bg-accent" />}
      <p className="eyebrow">{label}</p>
      <p className="mt-3 font-display text-4xl font-semibold leading-none tracking-tight">
        {value}
      </p>
      {sub && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
