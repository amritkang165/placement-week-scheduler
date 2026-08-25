import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "bg-muted text-foreground",
  success: "bg-success/12 text-success",
  warning: "bg-accent/12 text-accent",
  destructive: "bg-destructive/12 text-destructive",
  info: "bg-primary/12 text-primary",
  purple: "bg-indigo-500/12 text-indigo-600 dark:text-indigo-400",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium",
        VARIANTS[variant] ?? VARIANTS.default,
        className,
      )}
      {...props}
    />
  );
}
