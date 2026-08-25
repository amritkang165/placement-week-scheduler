import { cn } from "@/lib/utils";

const ACCENTS = {
  blue: "border-primary",
  yellow: "border-accent",
  green: "border-success",
  red: "border-destructive",
};

export function StatCard({
  label,
  value,
  sub,
  className,
  accent = "blue",
}: {
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
  accent?: keyof typeof ACCENTS;
}) {
  return (
    <div className={cn("relative border-2 border-foreground bg-card p-4 pb-5 shadow-hard", className)}>
      <span className={cn("absolute -top-[3px] left-0 h-[3px] w-10", ACCENTS[accent] ?? ACCENTS.blue)} />
      <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-3 font-display text-4xl font-normal leading-none tracking-tight">{value}</p>
      {sub && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{sub}</p>}
    </div>
  );
}
