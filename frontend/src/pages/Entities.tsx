import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Company, Panel, Room, Student } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search..."
          className="h-9 w-64 rounded-md border px-3 text-sm outline-none focus:border-blue-400"
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
            <select value={tier} onChange={(e) => setTier(e.target.value)} className="h-8 rounded-md border px-2 text-xs">
              <option value="ALL">All tiers</option>
              <option value="TIER_1">Tier 1</option>
              <option value="TIER_2">Tier 2</option>
              <option value="TIER_3">Tier 3</option>
            </select>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card">
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2">Company</th>
                  <th className="px-4 py-2">Tier</th>
                  <th className="px-4 py-2">CGPA cut</th>
                  <th className="px-4 py-2">Duration</th>
                  <th className="px-4 py-2">Panels</th>
                  <th className="px-4 py-2">Availability</th>
                </tr>
              </thead>
              <tbody>
                {companies
                  .filter(
                    (c) =>
                      (tier === "ALL" || c.priority_tier === tier) &&
                      c.name.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map((c) => (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-muted">
                      <td className="px-4 py-2 font-medium">{c.name}</td>
                      <td className="px-4 py-2">{tierBadge(c.priority_tier)}</td>
                      <td className="px-4 py-2">{c.cgpa_cutoff}</td>
                      <td className="px-4 py-2">{c.interview_duration_minutes} min</td>
                      <td className="px-4 py-2">{c.panel_count}</td>
                      <td className="px-4 py-2 text-xs text-muted-foreground">{c.available_days.join(", ")}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {tab === "students" && (
        <Card>
          <CardHeader>
            <CardTitle>Students ({students.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card">
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2">Name</th>
                  <th className="px-4 py-2">Branch</th>
                  <th className="px-4 py-2">Year</th>
                  <th className="px-4 py-2">CGPA</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {students
                  .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()))
                  .map((s) => (
                    <tr key={s.id} className="border-b last:border-0 hover:bg-muted">
                      <td className="px-4 py-2 font-medium">{s.name}</td>
                      <td className="px-4 py-2">{s.branch}</td>
                      <td className="px-4 py-2">{s.year}</td>
                      <td className="px-4 py-2">{s.cgpa}</td>
                      <td className="px-4 py-2">
                        <Badge variant={s.status === "ACTIVE" ? "success" : "warning"}>{s.status}</Badge>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {tab === "rooms" && (
        <Card>
          <CardHeader>
            <CardTitle>Rooms ({rooms.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card">
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2">Room</th>
                  <th className="px-4 py-2">Capacity</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {rooms
                  .filter((r) => r.name.toLowerCase().includes(search.toLowerCase()))
                  .map((r) => (
                    <tr key={r.id} className="border-b last:border-0 hover:bg-muted">
                      <td className="px-4 py-2 font-medium">{r.name}</td>
                      <td className="px-4 py-2">{r.capacity}</td>
                      <td className="px-4 py-2">
                        <Badge variant={r.status === "ACTIVE" ? "success" : "destructive"}>{r.status}</Badge>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {tab === "panels" && (
        <Card>
          <CardHeader>
            <CardTitle>Panels ({panels.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[60vh] overflow-y-auto p-0">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card">
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2">Panel</th>
                  <th className="px-4 py-2">Company</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {panels.map((p) => {
                  const company = companies.find((c) => c.id === p.company_id);
                  if (search && !company?.name.toLowerCase().includes(search.toLowerCase())) return null;
                  return (
                    <tr key={p.id} className="border-b last:border-0 hover:bg-muted">
                      <td className="px-4 py-2 font-medium">{p.name}</td>
                      <td className="px-4 py-2">{company?.name ?? p.company_id}</td>
                      <td className="px-4 py-2">
                        <Badge variant={p.status === "ACTIVE" ? "success" : "destructive"}>{p.status}</Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
