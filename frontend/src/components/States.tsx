import { AlertTriangle, Inbox, Loader2 } from "lucide-react";

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 font-mono text-sm text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
      <p className="uppercase tracking-widest">{label ?? "Loading…"}</p>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 border-2 border-foreground bg-destructive px-4 py-3 text-sm text-destructive-foreground shadow-hard">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center border-2 border-dashed border-foreground px-6 py-16 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center border-2 border-foreground bg-accent text-accent-foreground shadow-hard-sm">
        <Inbox className="h-5 w-5" />
      </div>
      <p className="font-display text-lg uppercase">{title}</p>
      {hint && <p className="mt-1 max-w-sm text-xs text-muted-foreground">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
