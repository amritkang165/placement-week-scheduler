import { cloneElement, isValidElement } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

const VARIANTS = {
  primary: "bg-primary text-primary-foreground hover:bg-primary/90",
  accent: "bg-accent text-accent-foreground hover:bg-accent/90",
  outline: "bg-card text-foreground hover:bg-muted",
  ghost: "bg-transparent text-foreground hover:bg-muted",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
};

const SIZES = {
  default: "h-11 px-5 text-sm",
  sm: "h-9 px-3 text-xs",
  lg: "h-12 px-7 text-base",
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
    "inline-flex items-center justify-center gap-2 rounded-none border-2 border-foreground font-bold uppercase tracking-wide shadow-hard transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:pointer-events-none disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
    className,
  );
  if (asChild && isValidElement(children)) {
    return cloneElement(children as React.ReactElement<{ className?: string }>, {
      className: cn(classes, (children as React.ReactElement<{ className?: string }>).props.className),
    });
  }
  return (
    <button className={classes} {...props}>
      {children as ReactNode}
    </button>
  );
}
