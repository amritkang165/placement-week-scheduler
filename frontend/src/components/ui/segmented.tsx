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
    <div className={cn("inline-flex items-center rounded-lg bg-muted/70 p-1", className)}>
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all",
            value === o.value
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {o.label ?? o.value}
        </button>
      ))}
    </div>
  );
}
