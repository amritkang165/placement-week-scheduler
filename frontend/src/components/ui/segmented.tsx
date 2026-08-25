import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
  className,
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label?: ReactNode }[];
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-5 overflow-x-auto", className)}>
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "whitespace-nowrap border-b pb-1 font-mono text-[11px] font-medium uppercase tracking-[0.14em] transition-colors",
            value === o.value
              ? "border-accent text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          {o.label ?? o.value}
        </button>
      ))}
    </div>
  );
}
