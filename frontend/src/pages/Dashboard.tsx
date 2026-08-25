import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import type { Metrics, ScheduleVersion } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/StatCard";
import { EmptyState, ErrorBox, Spinner } from "@/components/States";
import ConflictsWidget from "@/components/ConflictsWidget";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";
import { pct } from "@/lib/utils";

const TIER_COLORS: Record<string, string> = {
  TIER_1: "#4f46e5",
  TIER_2: "#f59e0b",
  TIER_3: "#94a3b8",
};

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
    value: count,
  }));
  const dayData = Object.entries(metrics?.interviews_by_day ?? {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([day, count]) => ({ day: day.slice(5), interviews: count }));

  if (!hasData) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-border bg-card p-10 text-center shadow-card md:p-16">
          <p className="eyebrow mb-3">Coordinators’ board</p>
          <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight md:text-4xl">
            Set the stage for placement week.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
            Generate a deterministic dataset and solve the initial schedule to
            bring the board to life.
          </p>
          <Button size="lg" className="mt-8" onClick={seedAndSchedule} disabled={busy}>
            {busy ? "Solving…" : "Generate & schedule"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <p className="eyebrow mb-3">Placement week · Coordinators’ board</p>
          <h2 className="text-4xl font-bold leading-[1.08] tracking-tight md:text-5xl">
            <span className="text-primary">{metrics.scheduled}</span> of {metrics.total}
            <span className="block text-xl font-medium text-muted-foreground md:text-2xl">
              interviews on the board.
            </span>
          </h2>
          <p className="mt-5 max-w-xl text-sm leading-relaxed text-muted-foreground">
            <span className="font-semibold text-foreground">{pct(metrics.coverage)}</span> scheduled ·{" "}
            <span className="font-semibold text-foreground">{metrics.unscheduled}</span> unresolved.{" "}
            {metrics.student_clashes === 0
              ? "No student clashes — every appointment runs clean."
              : `${metrics.student_clashes} clashes need attention.`}
          </p>
          <div className="mt-7 flex flex-wrap gap-2">
            <Button asChild>
              <Link to="/schedule">
                Open schedule <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/replan">Handle a disruption</Link>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Coverage" value={pct(metrics.coverage)} sub={`${metrics.scheduled} scheduled`} />
          <StatCard label="Unscheduled" value={metrics.unscheduled} sub="no feasible slot yet" />
          <StatCard label="Replan churn" value={pct(metrics.replan_churn)} sub="moved + cancelled share" />
          <StatCard label="On the floor" value={metrics.companies} sub={`${metrics.rooms} rooms · ${metrics.panels} panels`} />
        </div>
      </section>

      {/* ── Status strip ───────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={metrics.solver_status === "OPTIMAL" ? "success" : "info"}>
          Solver · {metrics.solver_status}
        </Badge>
        <Badge variant={metrics.schedule_status === "VALID" ? "success" : "destructive"}>
          Validation · {metrics.schedule_status}
        </Badge>
        <Badge variant={metrics.student_clashes === 0 ? "success" : "destructive"}>
          Clashes · {metrics.student_clashes}
        </Badge>
        <Badge>Room util · {pct(metrics.room_utilization)}</Badge>
        <Badge>Panel util · {pct(metrics.panel_utilization)}</Badge>
        <Badge>Avg wait · {metrics.avg_wait_minutes.toFixed(0)} min</Badge>
      </div>

      <ConflictsWidget />

      {/* ── Charts ─────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Interviews per day</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={dayData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" fontSize={12} tickLine={false} axisLine={{ stroke: "#a1a1aa" }} />
                <YAxis fontSize={12} allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ borderRadius: 8, borderColor: "hsl(var(--border))", background: "hsl(var(--card))" }} />
                <Bar dataKey="interviews" fill="#4f46e5" radius={[0, 0, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Scheduled by priority tier</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={tierData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85} paddingAngle={2}>
                  {tierData.map((entry) => (
                    <Cell key={entry.name} fill={TIER_COLORS[entry.name.replace(" ", "_").toUpperCase()] ?? TIER_COLORS.TIER_3} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 8, borderColor: "hsl(var(--border))", background: "hsl(var(--card))" }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 flex justify-center gap-4 text-xs text-muted-foreground">
              {tierData.map((t) => (
                <span key={t.name} className="flex items-center gap-1.5">
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: TIER_COLORS[t.name.replace(" ", "_").toUpperCase()] ?? TIER_COLORS.TIER_3 }} />
                  {t.name}: {t.value}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

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
