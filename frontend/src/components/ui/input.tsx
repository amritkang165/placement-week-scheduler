import { cn } from "@/lib/utils";
import type { InputHTMLAttributes, LabelHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

const base =
  "h-10 w-full rounded-none border-2 border-foreground bg-card px-3 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:border-accent focus:shadow-hard-sm focus:outline-none disabled:opacity-60";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(base, className)} {...props} />;
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(base, "appearance-none rounded-none bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22><path d=%22M2 4l4 4 4-4%22 fill=%22none%22 stroke=%22%23000%22 stroke-width=%222%22/></svg>')] bg-[right_0.6rem_center] bg-no-repeat pr-9", className)}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(base, "h-auto py-2 leading-relaxed", className)} {...props} />;
}

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1 block font-mono text-[11px] font-bold uppercase tracking-widest text-muted-foreground", className)}
      {...props}
    />
  );
}

export function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-1", className)}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}
