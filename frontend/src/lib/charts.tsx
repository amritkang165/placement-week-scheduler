import type { ReactNode } from "react";

export const PALETTE = {
  ink: "#2b2b2b",
  saffron: "#f6961e",
  muted: "#c9c2b4",
  line: "#e6e0d6",
  textMuted: "#8a857a",
};

export const TIER_COLORS: Record<string, string> = {
  TIER_1: PALETTE.ink,
  TIER_2: PALETTE.saffron,
  TIER_3: PALETTE.muted,
};

export const AXIS = {
  tick: { fontSize: 11, fill: PALETTE.textMuted },
  stroke: PALETTE.line,
};

export function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: {
    name?: string;
    value?: number | string;
    color?: string;
    payload?: { fill?: string; [k: string]: any };
  }[];
  label?: string;
}): ReactNode {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-xs shadow-sm">
      {label && <div className="mb-1.5 font-semibold text-foreground">{label}</div>}
      <div className="space-y-1">
        {payload.map((p, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: p.color ?? p.payload?.fill }}
            />
            <span className="text-muted-foreground">{p.name}</span>
            <span className="ml-auto font-mono font-medium text-foreground">
              {typeof p.value === "number" ? p.value.toLocaleString() : p.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
