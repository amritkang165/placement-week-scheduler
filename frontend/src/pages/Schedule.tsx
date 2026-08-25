import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import type { Company, Interview, Room, ScheduleResponse, ScheduleVersion } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorBox, Spinner } from "@/components/States";
import { cn, formatDate, minutesToTime } from "@/lib/utils";

const SLOT_MINUTES = 30;
const DAY_START = 9 * 60;
const DAY_END = 17 * 60;

function tierColor(tier: string | undefined): string {
  switch (tier) {
    case "TIER_1":
      return "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-500/20 dark:text-indigo-200 dark:border-indigo-500/30";
    case "TIER_2":
      return "bg-sky-100 text-sky-800 border-sky-200 dark:bg-sky-500/20 dark:text-sky-200 dark:border-sky-500/30";
    default:
      return "bg-muted text-foreground border-border";
  }
}

export default function Schedule() {
  const [params, setParams] = useSearchParams();
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [versions, setVersions] = useState<ScheduleVersion[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [day, setDay] = useState<string>("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [v, r, c] = await Promise.all([api.getVersions(), api.rooms(), api.companies()]);
        setVersions(v);
        setRooms(r);
        setCompanies(c);
        const active = v.find((x) => x.is_active);
        const requested = params.get("v");
        const target = requested ?? active?.id;
        if (target) {
          const s = await api.getVersion(target);
          setSchedule(s);
          const days = [...new Set(s.interviews.map((i) => i.date).filter(Boolean))] as string[];
          days.sort();
          setDay((d) => (d && days.includes(d) ? d : days[0] ?? ""));
        }
        setError(null);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.get("v")]);

  const interviews = schedule?.interviews ?? [];
  const days = useMemo(
    () => [...new Set(interviews.map((i) => i.date).filter(Boolean))].sort() as string[],
    [interviews],
  );

  const dayInterviews = useMemo(
    () =>
      interviews.filter(
        (i) =>
          i.status === "SCHEDULED" &&
          i.date === day &&
          (!search ||
            i.student_name.toLowerCase().includes(search.toLowerCase()) ||
            i.company_name.toLowerCase().includes(search.toLowerCase()) ||
            i.id.toLowerCase().includes(search.toLowerCase())),
      ),
    [interviews, day, search],
  );

  const tierByCompany = useMemo(
    () => new Map(companies.map((c) => [c.id, c.priority_tier])),
    [companies],
  );

  const slots = useMemo(() => {
    const out: number[] = [];
    for (let m = DAY_START; m < DAY_END; m += SLOT_MINUTES) out.push(m);
    return out;
  }, []);

  function interviewAt(roomId: string, startMin: number): Interview | undefined {
    return dayInterviews.find((iv) => {
      if (iv.room_id !== roomId || !iv.start_time) return false;
      const [h, m] = iv.start_time.split(":").map(Number);
      const start = h * 60 + m;
      return start <= startMin && startMin < start + iv.duration_minutes;
    });
  }

  if (loading) return <Spinner label="Loading schedule..." />;
  if (error) return <ErrorBox message={error} />;
  if (!schedule || interviews.length === 0)
    return (
      <EmptyState
        title="No schedule generated yet"
        hint="Go to the Dashboard and click 'Generate demo data & schedule'."
      />
    );

  const unscheduled = interviews.filter((i) => i.status === "UNSCHEDULED");
  const cancelled = interviews.filter((i) => i.status === "CANCELLED");
  const gridCols = rooms.length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="eyebrow mb-2">Week at a glance</p>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Schedule</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Version SCH-{String(schedule.version.version_number).padStart(3, "0")} ·{" "}
            {schedule.version.reason} ·{" "}
            <Badge variant={schedule.version.solver_status === "OPTIMAL" ? "success" : "info"}>
              {schedule.version.solver_status}
            </Badge>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search student or company…"
            className="w-64"
          />
          <Select
            value={schedule.version.id}
            onChange={(e) => setParams({ v: e.target.value })}
            className="w-64"
          >
            {[...versions].reverse().map((v) => (
              <option key={v.id} value={v.id}>
                SCH-{String(v.version_number).padStart(3, "0")} — {v.reason}
                {v.is_active ? " (active)" : ""}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="flex gap-1">
        {days.map((d) => (
          <Button
            key={d}
            size="sm"
            variant={d === day ? "primary" : "outline"}
            onClick={() => setDay(d)}
          >
            {formatDate(d)}
          </Button>
        ))}
      </div>

      <Card className="overflow-hidden">
        <CardContent className="overflow-x-auto p-0">
          <div style={{ minWidth: 180 * Math.min(gridCols, 8) }}>
            {/* Header row (sticky) */}
            <div
              className="grid border-b border-border bg-muted/60 text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground"
              style={{ gridTemplateColumns: `76px repeat(${gridCols}, minmax(110px, 1fr))` }}
            >
              <div className="px-2 py-2.5">Time</div>
              {rooms.map((r) => (
                <div key={r.id} className="border-l border-border px-2 py-2.5 text-center">
                  {r.name}
                  {r.status !== "ACTIVE" && (
                    <Badge variant="destructive" className="ml-1">
                      down
                    </Badge>
                  )}
                </div>
              ))}
            </div>
            {/* Time rows */}
            {slots.map((startMin, idx) => {
              const isHour = startMin % 60 === 0;
              return (
                <div
                  key={startMin}
                  className="grid border-b border-border last:border-0"
                  style={{ gridTemplateColumns: `76px repeat(${gridCols}, minmax(110px, 1fr))` }}
                >
                  <div
                    className={cn(
                      "border-r border-border px-2 py-1.5 text-[11px] tabular-nums text-muted-foreground",
                      isHour && "font-semibold text-foreground",
                      idx % 2 === 1 && "bg-muted/20",
                    )}
                  >
                    {minutesToTime(startMin)}
                  </div>
                  {rooms.map((r) => {
                    const iv = interviewAt(r.id, startMin);
                    const isStart = iv && iv.start_time === minutesToTime(startMin);
                    return (
                      <div
                        key={r.id}
                        className={cn(
                          "min-h-[36px] border-l border-border p-0.5 transition-colors hover:bg-muted/40",
                          idx % 2 === 1 && "bg-muted/20",
                        )}
                      >
                        {isStart && iv && (
                          <div
                            className={cn(
                              "h-full rounded border px-1.5 py-1 text-[10px] leading-tight",
                              tierColor(tierByCompany.get(iv.company_id)),
                            )}
                            title={`${iv.student_name} · ${iv.company_name} · ${iv.panel_id ?? ""}`}
                          >
                            <div className="truncate font-semibold">{iv.student_name}</div>
                            <div className="truncate opacity-75">{iv.company_name}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Unscheduled ({unscheduled.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-72 overflow-y-auto p-0">
            {unscheduled.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">All shortlists scheduled.</p>
            ) : (
              <ul className="divide-y text-sm">
                {unscheduled.slice(0, 50).map((i) => (
                  <li key={i.id} className="flex items-center justify-between px-4 py-2">
                    <span>
                      <span className="font-medium">{i.student_name}</span>
                      <span className="text-muted-foreground"> · {i.company_name}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">{i.reason ?? "no feasible slot"}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cancelled ({cancelled.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-72 overflow-y-auto p-0">
            {cancelled.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">Nothing cancelled in this version.</p>
            ) : (
              <ul className="divide-y text-sm">
                {cancelled.slice(0, 50).map((i) => (
                  <li key={i.id} className="flex items-center justify-between px-4 py-2">
                    <span>
                      <span className="font-medium">{i.student_name}</span>
                      <span className="text-muted-foreground"> · {i.company_name}</span>
                    </span>
                    <span className="text-xs text-muted-foreground">{i.reason ?? ""}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
