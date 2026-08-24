import { cloneElement, isValidElement } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

const VARIANTS = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90",
  accent: "bg-accent text-accent-foreground hover:bg-accent/90",
  outline: "border border-border bg-transparent text-foreground hover:bg-muted",
  ghost: "text-foreground hover:bg-muted",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
};

const SIZES = {
  default: "h-10 px-4 text-sm",
  sm: "h-8 px-3 text-xs",
  lg: "h-11 px-6 text-sm",
};

export function Button({
  variant = "primary",
  size = "default",
  asChild = false,
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
  asChild?: boolean;
}) {
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
    className,
  );
  if (asChild && isValidElement(children)) {
    return cloneElement(children as React.ReactElement<Record<string, unknown>>, {
      className: cn(classes, (children as React.ReactElement<{ className?: string }>).props.className),
    });
  }
  return (
    <button className={classes} {...props}>
      {children as ReactNode}
    </button>
  );
}
