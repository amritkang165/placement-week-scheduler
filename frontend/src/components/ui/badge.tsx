import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const VARIANTS: Record<string, string> = {
  default: "bg-muted text-foreground",
  success: "bg-success/15 text-success",
  warning: "bg-accent/15 text-accent",
  destructive: "bg-destructive/15 text-destructive",
  info: "bg-primary/15 text-primary",
  purple: "bg-accent/15 text-accent",
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
