import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import type {
  ChangeItem,
  Company,
  Disruption,
  DisruptionType,
  Panel,
  ReplanResponse,
  Room,
  Student,
} from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";
import { EmptyState, ErrorBox, Spinner } from "@/components/States";
import { formatDate, minutesToTime } from "@/lib/utils";

const DISRUPTION_TYPES: { value: DisruptionType; label: string; entity: string }[] = [
  { value: "COMPANY_DELAY", label: "Company delay", entity: "company" },
  { value: "PANEL_UNAVAILABLE", label: "Panel unavailable", entity: "panel" },
  { value: "ROOM_UNAVAILABLE", label: "Room unavailable", entity: "room" },
  { value: "STUDENT_WITHDRAWAL", label: "Student withdrawal", entity: "student" },
];

const CHANGE_VARIANTS: Record<string, "success" | "warning" | "destructive" | "info"> = {
  ADDED: "success",
  MOVED: "warning",
  CANCELLED: "destructive",
  UNCHANGED: "info",
};

function slotText(s: ChangeItem["before"]): string {
  if (!s || !s.date || !s.start) return "—";
  return `${formatDate(s.date)} ${s.start}–${s.end} · ${s.room_id ?? "?"}/${s.panel_id ?? "?"}`;
}

export default function Replan() {
  const [type, setType] = useState<DisruptionType>("COMPANY_DELAY");
  const [entityId, setEntityId] = useState("");
  const [delayHours, setDelayHours] = useState(2);
  const [reason, setReason] = useState("Coordinator-reported disruption");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [panels, setPanels] = useState<Panel[]>([]);
  const [disruptions, setDisruptions] = useState<Disruption[]>([]);
  const [result, setResult] = useState<ReplanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"ALL" | "MOVED" | "CANCELLED" | "ADDED">("ALL");

  useEffect(() => {
    (async () => {
      try {
        const [c, s, r, p, d] = await Promise.all([
          api.companies(),
          api.students(),
          api.rooms(),
          api.panels(),
          api.listDisruptions(),
        ]);
        setCompanies(c);
        setStudents(s);
        setRooms(r);
        setPanels(p);
        setDisruptions(d);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const activeType = DISRUPTION_TYPES.find((t) => t.value === type)!;
  const entities =
    activeType.entity === "company"
      ? companies.map((c) => ({ id: c.id, label: c.name }))
      : activeType.entity === "student"
        ? students.map((s) => ({ id: s.id, label: `${s.name} (${s.id})` }))
        : activeType.entity === "room"
          ? rooms.map((r) => ({ id: r.id, label: r.name }))
          : panels.map((p) => ({
              id: p.id,
              label: `${p.name} — ${companies.find((c) => c.id === p.company_id)?.name ?? ""}`,
            }));

  async function submit() {
    if (!entityId) return;
    setBusy(true);
    setError(null);
    try {
      const details =
        type === "COMPANY_DELAY" ? { delay_hours: delayHours } : {};
      const res = await api.replan([{ type, entity_id: entityId, details }], reason);
      setResult(res);
      const d = await api.listDisruptions();
      setDisruptions(d);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Spinner />;
  if (error && !result) return <ErrorBox message={error} />;

  const changes = (result?.changes ?? []).filter(
    (c) => filter === "ALL" || c.change_type === filter,
  );
  const summary = result?.summary ?? {};

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow mb-2">Handle the unexpected</p>
        <h2 className="font-display text-3xl font-semibold tracking-tight">Disruptions</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Inject a disruption and re-solve. Unaffected interviews keep their time slots.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inject disruption</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-5">
          <Field label="Type">
            <Select
              value={type}
              onChange={(e) => {
                setType(e.target.value as DisruptionType);
                setEntityId("");
              }}
            >
              {DISRUPTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Entity" className="md:col-span-2">
            <Select
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
            >
              <option value="">Select {activeType.entity}...</option>
              {entities.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.label}
                </option>
              ))}
            </Select>
          </Field>

          {type === "COMPANY_DELAY" && (
            <Field label="Delay (hours)">
              <Input
                type="number"
                min={1}
                max={8}
                value={delayHours}
                onChange={(e) => setDelayHours(Number(e.target.value))}
              />
            </Field>
          )}

          <Field label="Reason">
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </Field>

          <div className="flex items-end">
            <Button onClick={submit} disabled={!entityId || busy} className="w-full">
              {busy ? "Solving..." : "Apply & replan"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {busy && <Spinner label="Running CP-SAT replan..." />}
      {!busy && error && <ErrorBox message={error} />}

      {result && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={result.solver_status === "OPTIMAL" ? "success" : "info"}>
              Solver: {result.solver_status}
            </Badge>
            <Badge variant={result.schedule_status === "VALID" ? "success" : "destructive"}>
              Validation: {result.schedule_status}
            </Badge>
            <Badge variant="success">Added: {summary.ADDED ?? 0}</Badge>
            <Badge variant="warning">Moved: {summary.MOVED ?? 0}</Badge>
            <Badge variant="destructive">Cancelled: {summary.CANCELLED ?? 0}</Badge>
            <Badge>Unchanged: {summary.UNCHANGED ?? 0}</Badge>
            <Badge variant="purple">
              Churn:{" "}
              {(
                (((summary.MOVED ?? 0) + (summary.CANCELLED ?? 0)) /
                  Math.max(1, result.changes.length)) *
                100
              ).toFixed(1)}
              %
            </Badge>
            <Link
              to={`/schedule?v=${result.version_id}`}
              className="ml-auto text-sm text-primary hover:underline"
            >
              View SCH-{String(result.version_number).padStart(3, "0")} →
            </Link>
          </div>

          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Changes ({changes.length})</CardTitle>
              <div className="flex gap-1">
                {(["ALL", "MOVED", "CANCELLED", "ADDED"] as const).map((f) => (
                  <Button
                    key={f}
                    size="sm"
                    variant={filter === f ? "primary" : "outline"}
                    onClick={() => setFilter(f)}
                  >
                    {f}
                  </Button>
                ))}
              </div>
            </CardHeader>
            <CardContent className="max-h-[480px] overflow-y-auto p-0">
              <THead>
                <tr>
                  <TH>Interview</TH>
                  <TH>Student</TH>
                  <TH>Company</TH>
                  <TH>Change</TH>
                  <TH>Before</TH>
                  <TH>After</TH>
                </tr>
              </THead>
              <tbody>
                {changes.map((c) => (
                  <TR key={c.interview_id}>
                    <TD className="font-mono text-xs">{c.interview_id}</TD>
                    <TD>{c.student_name}</TD>
                    <TD>{c.company_name}</TD>
                    <TD>
                      <Badge variant={CHANGE_VARIANTS[c.change_type]}>{c.change_type}</Badge>
                    </TD>
                    <TD className="text-muted-foreground">{slotText(c.before)}</TD>
                    <TD>{slotText(c.after)}</TD>
                  </TR>
                ))}
              </tbody>
            </CardContent>
          </Card>
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Disruption log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {disruptions.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">No disruptions recorded yet.</p>
          ) : (
            <ul className="divide-y text-sm">
              {disruptions.slice(0, 10).map((d) => (
                <li key={d.id} className="flex items-center justify-between px-4 py-2">
                  <span>
                    <Badge
                      variant={
                        d.type === "STUDENT_WITHDRAWAL"
                          ? "purple"
                          : d.type === "ROOM_UNAVAILABLE"
                            ? "destructive"
                            : "warning"
                      }
                    >
                      {d.type}
                    </Badge>{" "}
                    <span className="ml-2 font-mono text-xs">{d.entity_id}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {d.created_at ? new Date(d.created_at).toLocaleString() : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
