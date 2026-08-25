import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "border-border bg-muted text-foreground",
  success: "border-foreground bg-success text-success-foreground",
  warning: "border-foreground bg-accent text-accent-foreground",
  destructive: "border-foreground bg-destructive text-destructive-foreground",
  info: "border-foreground bg-primary text-primary-foreground",
  purple: "border-foreground bg-primary text-primary-foreground",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-none border px-2 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wider",
        VARIANTS[variant] ?? VARIANTS.default,
        className,
      )}
      {...props}
    />
  );
}
