import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Company, Panel, Room, Student } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input, Select } from "@/components/ui/input";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";
import { ErrorBox, Spinner } from "@/components/States";
import { cn } from "@/lib/utils";

type Tab = "companies" | "students" | "rooms" | "panels";

const TABS: { key: Tab; label: string }[] = [
  { key: "companies", label: "Companies" },
  { key: "students", label: "Students" },
  { key: "rooms", label: "Rooms" },
  { key: "panels", label: "Panels" },
];

function tierBadge(tier: string) {
  return (
    <Badge variant={tier === "TIER_1" ? "info" : tier === "TIER_2" ? "warning" : "default"}>
      {tier}
    </Badge>
  );
}

export default function Entities() {
  const [tab, setTab] = useState<Tab>("companies");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [panels, setPanels] = useState<Panel[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tier, setTier] = useState("ALL");

  useEffect(() => {
    (async () => {
      try {
        const [c, s, r, p] = await Promise.all([
          api.companies(),
          api.students(),
          api.rooms(),
          api.panels(),
        ]);
        setCompanies(c);
        setStudents(s);
        setRooms(r);
        setPanels(p);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="eyebrow mb-2">Who’s on the board</p>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Entities</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Companies, students, rooms, and panels in the current dataset
          </p>
        </div>
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search…"
          className="w-64"
        />
      </div>

      <div className="flex gap-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium",
              tab === t.key ? "bg-primary text-primary-foreground" : "bg-card text-foreground hover:bg-muted",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "companies" && (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Companies ({companies.length})</CardTitle>
            <Select value={tier} onChange={(e) => setTier(e.target.value)} className="w-32">
              <option value="ALL">All tiers</option>
              <option value="TIER_1">Tier 1</option>
              <option value="TIER_2">Tier 2</option>
              <option value="TIER_3">Tier 3</option>
            </Select>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <Table>
              <THead>
                <tr>
                  <TH>Company</TH>
                  <TH>Tier</TH>
                  <TH className="text-right">CGPA cut</TH>
                  <TH className="text-right">Duration</TH>
                  <TH className="text-right">Panels</TH>
                  <TH>Availability</TH>
                </tr>
              </THead>
              <tbody>
                {companies
                  .filter(
                    (c) =>
                      (tier === "ALL" || c.priority_tier === tier) &&
                      c.name.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map((c) => (
                    <TR key={c.id}>
                      <TD className="font-medium">{c.name}</TD>
                      <TD>{tierBadge(c.priority_tier)}</TD>
                      <TD className="text-right tabular-nums">{c.cgpa_cutoff}</TD>
                      <TD className="text-right tabular-nums">{c.interview_duration_minutes} min</TD>
                      <TD className="text-right tabular-nums">{c.panel_count}</TD>
                      <TD className="text-xs text-muted-foreground">{c.available_days.join(", ")}</TD>
                    </TR>
                  ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === "students" && (
        <Card>
          <CardHeader>
            <CardTitle>Students ({students.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <Table>
              <THead>
                <tr>
                  <TH>Name</TH>
                  <TH>Branch</TH>
                  <TH className="text-right">Year</TH>
                  <TH className="text-right">CGPA</TH>
                  <TH>Status</TH>
                </tr>
              </THead>
              <tbody>
                {students
                  .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()))
                  .map((s) => (
                    <TR key={s.id}>
                      <TD className="font-medium">{s.name}</TD>
                      <TD>{s.branch}</TD>
                      <TD className="text-right tabular-nums">{s.year}</TD>
                      <TD className="text-right tabular-nums">{s.cgpa}</TD>
                      <TD>
                        <Badge variant={s.status === "ACTIVE" ? "success" : "warning"}>{s.status}</Badge>
                      </TD>
                    </TR>
                  ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === "rooms" && (
        <Card>
          <CardHeader>
            <CardTitle>Rooms ({rooms.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <Table>
              <THead>
                <tr>
                  <TH>Room</TH>
                  <TH className="text-right">Capacity</TH>
                  <TH>Status</TH>
                </tr>
              </THead>
              <tbody>
                {rooms
                  .filter((r) => r.name.toLowerCase().includes(search.toLowerCase()))
                  .map((r) => (
                    <TR key={r.id}>
                      <TD className="font-medium">{r.name}</TD>
                      <TD className="text-right tabular-nums">{r.capacity}</TD>
                      <TD>
                        <Badge variant={r.status === "ACTIVE" ? "success" : "destructive"}>{r.status}</Badge>
                      </TD>
                    </TR>
                  ))}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === "panels" && (
        <Card>
          <CardHeader>
            <CardTitle>Panels ({panels.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <Table>
              <THead>
                <tr>
                  <TH>Panel</TH>
                  <TH>Company</TH>
                  <TH>Status</TH>
                </tr>
              </THead>
              <tbody>
                {panels.map((p) => {
                  const company = companies.find((c) => c.id === p.company_id);
                  if (search && !company?.name.toLowerCase().includes(search.toLowerCase())) return null;
                  return (
                    <TR key={p.id}>
                      <TD className="font-medium">{p.name}</TD>
                      <TD>{company?.name ?? p.company_id}</TD>
                      <TD>
                        <Badge variant={p.status === "ACTIVE" ? "success" : "destructive"}>{p.status}</Badge>
                      </TD>
                    </TR>
                  );
                })}
              </tbody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
