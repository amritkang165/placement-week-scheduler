import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "text-muted-foreground",
  success: "text-success",
  warning: "text-accent",
  destructive: "text-destructive",
  info: "text-foreground",
  purple: "text-indigo-600 dark:text-indigo-400",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof VARIANTS }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono text-[10px] font-medium uppercase tracking-[0.14em]",
        VARIANTS[variant] ?? VARIANTS.default,
        className,
      )}
      {...props}
    />
  );
}
