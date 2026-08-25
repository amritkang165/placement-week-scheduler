import { useRef, useState } from "react";
import {
  Building2,
  DoorOpen,
  FileJson,
  FileSpreadsheet,
  Plus,
  Save,
  Trash2,
  Users,
} from "lucide-react";
import { dataApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { SegmentedControl } from "@/components/ui/segmented";
import { ErrorBox, Spinner } from "@/components/States";

type EntityKind = "company" | "student" | "room" | "panel" | "shortlist";

const DAY_OPTIONS = ["DAY_1", "DAY_2", "DAY_3", "DAY_4"];

export default function AddData() {
  const [tab, setTab] = useState<"form" | "json" | "csv">("form");
  const [entity, setEntity] = useState<EntityKind>("company");
  const [form, setForm] = useState<Record<string, string>>({});
  const [csvEntity, setCsvEntity] = useState<EntityKind>("company");
  const [jsonText, setJsonText] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const FIELDS: Record<EntityKind, { key: string; label: string; type?: string }[]> = {
    company: [
      { key: "name", label: "Name" },
      { key: "priority_tier", label: "Tier (TIER_1/2/3)" },
      { key: "cgpa_cutoff", label: "CGPA cutoff", type: "number" },
      { key: "interview_duration_minutes", label: "Duration (min)", type: "number" },
      { key: "panel_count", label: "Panels", type: "number" },
      { key: "available_days", label: "Days (DAY_1,DAY_2,...)" },
    ],
    student: [
      { key: "name", label: "Name" },
      { key: "cgpa", label: "CGPA", type: "number" },
      { key: "branch", label: "Branch" },
      { key: "year", label: "Year", type: "number" },
    ],
    room: [
      { key: "name", label: "Room name" },
      { key: "capacity", label: "Capacity", type: "number" },
    ],
    panel: [
      { key: "company_id", label: "Company id" },
      { key: "name", label: "Panel name" },
    ],
    shortlist: [
      { key: "student_id", label: "Student id" },
      { key: "company_id", label: "Company id" },
    ],
  };

  async function submitManual() {
    setBusy(true);
    setMessage(null);
    try {
      const body: Record<string, unknown> = {};
      for (const f of FIELDS[entity]) {
        const v = form[f.key];
        if (!v) continue;
        body[f.key] = ["cgpa_cutoff", "cgpa", "year", "panel_count", "capacity", "interview_duration_minutes"].includes(
          f.key,
        )
          ? Number(v)
          : f.key === "available_days"
            ? v.split(",").map((s) => s.trim())
            : v;
      }
      if (entity === "company") {
        await dataApi.createCompany(body);
        setMessage({ ok: true, text: "Company created (with panels)." });
      } else if (entity === "student") await dataApi.createStudent(body);
      else if (entity === "room") await dataApi.createRoom(body);
      else if (entity === "panel") await dataApi.createPanel(body);
      else {
        body.cgpa_cutoff = undefined;
        await dataApi.createShortlist({ student_id: body.student_id, company_id: body.company_id });
      }
      setForm({});
    } catch (e) {
      setMessage({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function submitJson() {
    setBusy(true);
    setMessage(null);
    try {
      const parsed = JSON.parse(jsonText);
      const res = await dataApi.importJson(parsed);
      const errs = res.errors.length ? ` Errors: ${res.errors.slice(0, 3).join("; ")}` : "";
      setMessage({ ok: res.errors.length === 0, text: `Imported ${JSON.stringify(res.created)}.${errs}` });
    } catch (e) {
      setMessage({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function submitCsv(file: File) {
    setBusy(true);
    setMessage(null);
    try {
      const res = await dataApi.importCsv(csvEntity, file);
      const errs = res.errors.length ? ` Errors: ${res.errors.slice(0, 3).join("; ")}` : "";
      setMessage({ ok: res.errors.length === 0, text: `Imported ${JSON.stringify(res.created)}.${errs}` });
    } catch (e) {
      setMessage({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="eyebrow mb-2">Bring your own</p>
        <h2 className="large-title">Add data</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Add companies, students, rooms, panels, and shortlists manually or import in bulk.
        </p>
      </div>

      <div className="flex items-center justify-end gap-2">
        <Button
          variant="destructive"
          size="sm"
          onClick={async () => {
            if (!confirm("Wipe ALL placement data? This cannot be undone.")) return;
            await dataApi.wipeAll();
            setMessage({ ok: true, text: "All data cleared." });
          }}
        >
          <Trash2 className="h-4 w-4" /> Wipe all
        </Button>
      </div>

      <SegmentedControl
        value={tab}
        onChange={setTab}
        options={[
          { value: "form" as const, label: "Form" },
          { value: "json" as const, label: "JSON" },
          { value: "csv" as const, label: "CSV" },
        ]}
      />

      <Card>
        {tab === "form" && (
          <>
            <CardHeader>
              <CardTitle>Add manually</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["company", "Company", Building2],
                    ["student", "Student", Users],
                    ["room", "Room", DoorOpen],
                    ["panel", "Panel", Building2],
                    ["shortlist", "Shortlist", Plus],
                  ] as const
                ).map(([k, label, Icon]) => (
                  <button
                    key={k}
                    onClick={() => {
                      setEntity(k);
                      setForm({});
                    }}
                    className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium"
                    style={{
                      background: entity === k ? "hsl(var(--primary) / 0.15)" : "hsl(var(--card))",
                      borderColor: entity === k ? "hsl(var(--primary))" : "hsl(var(--border))",
                    }}
                  >
                    <Icon className="h-3.5 w-3.5" /> {label}
                  </button>
                ))}
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {FIELDS[entity].map((f) => (
                  <Field key={f.key} label={f.label}>
                    <Input
                      type={f.type ?? "text"}
                      value={form[f.key] ?? ""}
                      onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                      placeholder={f.key === "available_days" ? DAY_OPTIONS.join(",") : ""}
                    />
                  </Field>
                ))}
              </div>

              <Button onClick={submitManual} disabled={busy}>
                <Save className="h-4 w-4" /> {busy ? "Saving..." : `Add ${entity}`}
              </Button>
            </CardContent>
          </>
        )}

        {tab === "json" && (
          <>
            <CardHeader>
              <CardTitle>Import JSON</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                rows={12}
                placeholder={`{
  "companies": [{"name":"Acme","priority_tier":"TIER_1","cgpa_cutoff":7.5,"panel_count":2,"available_days":["DAY_1","DAY_2"]}],
  "students": [{"name":"Aman","cgpa":8.1,"branch":"CSE"}],
  "rooms": [{"name":"Room-1","capacity":6}],
  "panels": [{"company_id":"COMP-01","name":"P1"}],
  "shortlists": [{"student_id":"STU-0001","company_id":"COMP-01"}]
}`}
                className="font-mono text-xs"
              />
              <Button onClick={submitJson} disabled={busy}>
                {busy ? "Importing..." : "Import JSON"}
              </Button>
            </CardContent>
          </>
        )}

        {tab === "csv" && (
          <>
            <CardHeader>
              <CardTitle>Import CSV</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <label className="text-xs font-medium text-foreground">
                  Entity type
                  <Select
                    value={csvEntity}
                    onChange={(e) => setCsvEntity(e.target.value as EntityKind)}
                    className="ml-2 w-40"
                  >
                    <option value="companies">companies</option>
                    <option value="students">students</option>
                    <option value="rooms">rooms</option>
                    <option value="panels">panels</option>
                    <option value="shortlists">shortlists</option>
                  </Select>
                </label>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  onChange={(e) => e.target.files?.[0] && submitCsv(e.target.files[0])}
                  className="hidden"
                />
                <Button onClick={() => fileRef.current?.click()} disabled={busy}>
                  {busy ? "Importing..." : "Upload CSV"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                CSV header must match field names (e.g. students: <code>name,cgpa,branch,year</code>).
              </p>
            </CardContent>
          </>
        )}

        {message && (
          <div className="px-4 pb-4">
            <Badge variant={message.ok ? "success" : "destructive"} className="whitespace-pre-wrap">
              {message.text}
            </Badge>
          </div>
        )}
      </Card>
    </div>
  );
}
