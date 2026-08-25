import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { Metrics, ScheduleVersion } from "@/lib/types";
import { AXIS, ChartTooltip, PALETTE, TIER_COLORS } from "@/lib/charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/StatCard";
import { EmptyState, ErrorBox, Spinner } from "@/components/States";
import ConflictsWidget from "@/components/ConflictsWidget";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";
import { pct } from "@/lib/utils";

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [versions, setVersions] = useState<ScheduleVersion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [m, v] = await Promise.all([api.getMetrics(), api.getVersions()]);
      setMetrics(m);
      setVersions(v);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function seedAndSchedule() {
    setBusy(true);
    try {
      await api.generateData(42);
      await api.generateSchedule("Initial schedule");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  const hasData = metrics && metrics.total > 0;
  const tierData = Object.entries(metrics?.interviews_by_tier ?? {}).map(([tier, count]) => ({
    name: tier.replace("TIER_", "Tier "),
    tier,
    value: count,
  }));
  const dayData = Object.entries(metrics?.interviews_by_day ?? {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([day, count]) => ({ day: day.slice(5), interviews: count }));

  if (!hasData) {
    return (
      <div className="mx-auto max-w-xl py-16 text-center">
        <p className="eyebrow mb-5">Coordinators’ board</p>
        <h2 className="display text-5xl md:text-6xl">Bring the board to life.</h2>
        <p className="mx-auto mt-5 max-w-md text-sm leading-relaxed text-muted-foreground">
          Generate a deterministic dataset and solve the initial schedule to
          stage placement week.
        </p>
        <Button size="lg" className="mt-9" onClick={seedAndSchedule} disabled={busy}>
          {busy ? "Solving…" : "Generate & schedule"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-16">
      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="grid gap-10 lg:grid-cols-[1.3fr_0.9fr]">
        <div>
          <p className="eyebrow mb-5">Placement week · Coordinators’ board</p>
          <h1 className="display text-6xl md:text-7xl">
            The board is{" "}
            <span className="underline decoration-accent decoration-4 underline-offset-8">
              full
            </span>
            .
          </h1>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground">
            <span className="font-semibold text-foreground">{metrics.scheduled}</span> of{" "}
            {metrics.total} shortlists placed — {pct(metrics.coverage)}.{" "}
            {metrics.student_clashes === 0
              ? "No clashes. Every appointment runs clean."
              : `${metrics.student_clashes} clashes need attention.`}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button asChild>
              <Link to="/schedule">Open schedule</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/replan">Handle a disruption</Link>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-x-10 gap-y-8">
          <StatCard label="Coverage" value={pct(metrics.coverage)} sub="scheduled shortlists" />
          <StatCard label="Unscheduled" value={metrics.unscheduled} sub="no feasible slot yet" />
          <StatCard label="Replan churn" value={pct(metrics.replan_churn)} sub="moved + cancelled" />
          <StatCard label="Average wait" value={`${metrics.avg_wait_minutes.toFixed(0)}m`} sub="between interviews" />
        </div>
      </section>

      {/* ── Status strip ───────────────────────────────────── */}
      <section className="flex flex-wrap items-center gap-x-6 gap-y-2 border-y border-border py-4">
        <span className="label-mono">Status</span>
        <Badge variant="info">Solver · {metrics.solver_status}</Badge>
        <Badge variant={metrics.schedule_status === "VALID" ? "success" : "destructive"}>
          Validation · {metrics.schedule_status}
        </Badge>
        <Badge variant={metrics.student_clashes === 0 ? "success" : "destructive"}>
          Clashes · {metrics.student_clashes}
        </Badge>
        <Badge>Room util · {pct(metrics.room_utilization)}</Badge>
        <Badge>Panel util · {pct(metrics.panel_utilization)}</Badge>
        <span className="label-mono ml-auto">Guests · {metrics.companies} companies</span>
      </section>

      <ConflictsWidget />

      {/* ── Charts ─────────────────────────────────────────── */}
      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Interviews per day</CardTitle>
            <p className="text-xs text-muted-foreground">Total · {metrics.scheduled.toLocaleString()}</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dayData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={PALETTE.line} strokeDasharray="2 4" />
                <XAxis dataKey="day" tick={AXIS.tick} tickLine={false} axisLine={{ stroke: PALETTE.line }} />
                <YAxis tick={AXIS.tick} tickLine={false} axisLine={false} width={36} />
                <Tooltip cursor={{ fill: "hsl(0 0% 0% / 0.04)" }} content={<ChartTooltip />} />
                <Bar dataKey="interviews" name="Interviews" fill={PALETTE.saffron} radius={[3, 3, 0, 0]} maxBarSize={46}>
                  <LabelList dataKey="interviews" position="top" style={{ fontSize: 11, fill: PALETTE.textMuted }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>By priority tier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div className="relative h-[180px] w-[180px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={tierData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={58}
                      outerRadius={86}
                      paddingAngle={2}
                      stroke="hsl(var(--background))"
                      strokeWidth={3}
                    >
                      {tierData.map((entry) => (
                        <Cell key={entry.name} fill={TIER_COLORS[entry.tier] ?? PALETTE.muted} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <span className="font-mono text-xs text-muted-foreground">placed</span>
                  <span className="display text-2xl">{metrics.scheduled}</span>
                </div>
              </div>
              <ul className="flex-1 space-y-3">
                {tierData.map((t) => (
                  <li key={t.name} className="flex items-center gap-2 text-sm">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: TIER_COLORS[t.tier] ?? PALETTE.muted }} />
                    <span className="text-muted-foreground">{t.name}</span>
                    <span className="ml-auto font-mono font-medium">{t.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ── Versions ───────────────────────────────────────── */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Schedule versions</CardTitle>
          <Link to="/schedule" className="text-sm font-medium text-primary hover:underline">
            View all →
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <THead>
              <tr>
                <TH>Version</TH>
                <TH>Reason</TH>
                <TH className="text-right">Scheduled</TH>
                <TH className="text-right">Cancelled</TH>
                <TH>Status</TH>
              </tr>
            </THead>
            <tbody>
              {[...versions].reverse().slice(0, 6).map((v) => (
                <TR key={v.id}>
                  <TD className="font-medium">
                    <Link to={`/schedule?v=${v.id}`} className="text-primary hover:underline">
                      SCH-{String(v.version_number).padStart(3, "0")}
                    </Link>
                    {v.is_active && (
                      <Badge variant="success" className="ml-2">
                        active
                      </Badge>
                    )}
                  </TD>
                  <TD className="text-muted-foreground">{v.reason}</TD>
                  <TD className="text-right tabular-nums">{v.scheduled_count}</TD>
                  <TD className="text-right tabular-nums">{v.cancelled_count}</TD>
                  <TD>
                    <Badge variant={v.solver_status === "OPTIMAL" ? "success" : "info"}>
                      {v.solver_status}
                    </Badge>
                  </TD>
                </TR>
              ))}
            </tbody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
