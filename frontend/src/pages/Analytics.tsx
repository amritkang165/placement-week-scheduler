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
        <h2 className="font-display text-3xl font-semibold tracking-tight">Analytics</h2>
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

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily load &amp; room utilization</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={perDay}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="day" fontSize={12} />
                <YAxis yAxisId="left" fontSize={12} allowDecimals={false} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  fontSize={12}
                  unit="%"
                  domain={[0, 100]}
                />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="interviews" name="Interviews" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="utilization" name="Util %" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Interviews by company</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={perCompany.slice(0, 12)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" fontSize={12} allowDecimals={false} />
                <YAxis type="category" dataKey="name" fontSize={11} width={130} />
                <Tooltip />
                <Legend />
                <Bar dataKey="scheduled" name="Scheduled" stackId="a" fill="#4f46e5" />
                <Bar dataKey="cancelled" name="Cancelled" stackId="a" fill="#ef4444" />
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
