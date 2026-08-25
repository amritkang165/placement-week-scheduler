import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "border bg-muted text-foreground",
  success: "bg-success/10 text-success",
  warning: "bg-accent/10 text-accent",
  destructive: "bg-destructive/10 text-destructive",
  info: "bg-primary/10 text-primary",
  purple: "bg-indigo-500/10 text-indigo-600",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-transparent px-2 py-0.5 text-[11px] font-medium",
        VARIANTS[variant] ?? VARIANTS.default,
        className,
      )}
      {...props}
    />
  );
}
