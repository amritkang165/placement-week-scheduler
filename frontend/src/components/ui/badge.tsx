import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "border-border bg-muted text-foreground",
  success: "border-success/30 bg-success/10 text-success dark:text-success",
  warning: "border-accent/40 bg-accent/15 text-accent-foreground",
  destructive: "border-destructive/30 bg-destructive/10 text-destructive dark:text-destructive",
  info: "border-primary/30 bg-primary/10 text-primary dark:text-primary",
  purple: "border-primary/30 bg-primary/10 text-primary dark:text-primary",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
        VARIANTS[variant] ?? VARIANTS.default,
        className,
      )}
      {...props}
    />
  );
}
