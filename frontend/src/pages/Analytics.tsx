import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { Company, Interview, Metrics } from "@/lib/types";
import { AXIS, ChartTooltip, PALETTE } from "@/lib/charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorBox, Spinner } from "@/components/States";
import { StatCard } from "@/components/StatCard";
import { formatDate, pct } from "@/lib/utils";

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [m, s, c] = await Promise.all([
          api.getMetrics(),
          api.getCurrentSchedule(),
          api.companies(),
        ]);
        setMetrics(m);
        setInterviews(s.interviews);
        setCompanies(c);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const perDay = useMemo(() => {
    const days = [...new Set(interviews.map((i) => i.date).filter(Boolean))] as string[];
    days.sort();
    return days.map((d) => {
      const dayIvs = interviews.filter((i) => i.date === d && i.status === "SCHEDULED");
      const usedMinutes = dayIvs.reduce((acc, i) => acc + i.duration_minutes, 0);
      const capacity = metrics ? metrics.rooms * 8 * 60 : 1; // rooms * 9:00-17:00
      return {
        day: formatDate(d),
        interviews: dayIvs.length,
        utilization: Math.min(100, Math.round((usedMinutes / capacity) * 100)),
      };
    });
  }, [interviews, metrics]);

  const perCompany = useMemo(() => {
    const tierById = new Map(companies.map((c) => [c.id, c.priority_tier]));
    const map = new Map<string, { name: string; tier: string; scheduled: number; cancelled: number; unscheduled: number }>();
    for (const iv of interviews) {
      const entry =
        map.get(iv.company_id) ??
        { name: iv.company_name, tier: tierById.get(iv.company_id) ?? "", scheduled: 0, cancelled: 0, unscheduled: 0 };
      if (iv.status === "SCHEDULED") entry.scheduled += 1;
      else if (iv.status === "CANCELLED") entry.cancelled += 1;
      else entry.unscheduled += 1;
      map.set(iv.company_id, entry);
    }
    return [...map.values()].sort((a, b) => b.scheduled - a.scheduled);
  }, [interviews, companies]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;
  if (!metrics || metrics.total === 0)
    return (
      <EmptyState
        title="No data to analyze"
        hint="Generate a schedule from the Dashboard first."
      />
    );

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow mb-2">Numbers &amp; utilization</p>
        <h2 className="large-title">Analytics</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Utilization and throughput for the active schedule version
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Coverage" value={pct(metrics.coverage)} sub={`${metrics.scheduled}/${metrics.total}`} />
        <StatCard label="Room utilization" value={pct(metrics.room_utilization)} />
        <StatCard label="Panel utilization" value={pct(metrics.panel_utilization)} />
        <StatCard label="Avg student wait" value={`${metrics.avg_wait_minutes.toFixed(0)} min`} sub="before first interview" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily load &amp; utilization</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={perDay} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={PALETTE.line} strokeDasharray="2 4" />
                <XAxis dataKey="day" tick={AXIS.tick} tickLine={false} axisLine={{ stroke: PALETTE.line }} />
                <YAxis yAxisId="left" tick={AXIS.tick} tickLine={false} axisLine={false} width={34} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={AXIS.tick}
                  tickLine={false}
                  axisLine={false}
                  unit="%"
                  domain={[0, 100]}
                  width={38}
                />
                <Tooltip cursor={{ fill: "hsl(0 0% 0% / 0.04)" }} content={<ChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: PALETTE.textMuted }} />
                <Bar yAxisId="left" dataKey="interviews" name="Interviews" fill={PALETTE.primary} radius={[3, 3, 0, 0]} maxBarSize={40} />
                <Bar yAxisId="right" dataKey="utilization" name="Utilisation" fill={PALETTE.muted} fillOpacity={0.5} radius={[3, 3, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>By company</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={perCompany.slice(0, 10)} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke={PALETTE.line} strokeDasharray="2 4" />
                <XAxis type="number" tick={AXIS.tick} tickLine={false} axisLine={{ stroke: PALETTE.line }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: PALETTE.textMuted }} width={120} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: "hsl(0 0% 0% / 0.04)" }} content={<ChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: PALETTE.textMuted }} />
                <Bar dataKey="scheduled" name="Scheduled" stackId="a" fill={PALETTE.primary} maxBarSize={14} />
                <Bar dataKey="cancelled" name="Cancelled" stackId="a" fill={PALETTE.primary} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Company detail</CardTitle>
        </CardHeader>
        <CardContent className="max-h-96 overflow-y-auto p-0">
          <Table>
            <THead>
              <tr>
                <TH>Company</TH>
                <TH>Tier</TH>
                <TH className="text-right">Scheduled</TH>
                <TH className="text-right">Cancelled</TH>
                <TH className="text-right">Unscheduled</TH>
              </tr>
            </THead>
            <tbody>
              {perCompany.map((c) => (
                <TR key={c.name}>
                  <TD className="font-medium">{c.name}</TD>
                  <TD>
                    <Badge variant={c.tier === "TIER_1" ? "info" : "default"}>{c.tier || "—"}</Badge>
                  </TD>
                  <TD className="text-right tabular-nums">{c.scheduled}</TD>
                  <TD className="text-right tabular-nums">{c.cancelled}</TD>
                  <TD className="text-right tabular-nums">{c.unscheduled}</TD>
                </TR>
              ))}
            </tbody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
