import type {
  ChangeItem,
  Company,
  Conflict,
  Disruption,
  DisruptionType,
  Metrics,
  Panel,
  ReplanResponse,
  Room,
  ScheduleResponse,
  ScheduleVersion,
  Student,
} from "./types";

// API base URL. For hosted deploys set VITE_API_URL to the backend origin
// (e.g. https://placement-week-api.onrender.com) — the "/api" path is added here.
// Defaults to "/api" so the Vite dev proxy works locally.
const ORIGIN: string = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";
const BASE = `${ORIGIN}/api`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  generateData: (seed = 42) =>
    request<{ message: string; counts: Record<string, number> }>("/generate-data", {
      method: "POST",
      body: JSON.stringify({ seed }),
    }),

  generateSchedule: (reason = "Initial schedule") =>
    request<ScheduleVersion>("/schedule", {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  getCurrentSchedule: () => request<ScheduleResponse>("/schedule"),

  getVersion: (versionId: string) => request<ScheduleResponse>(`/schedule/${versionId}`),

  getVersions: () => request<ScheduleVersion[]>("/schedule/versions"),

  getMetrics: () => request<Metrics>("/schedule/metrics"),

  getConflicts: () => request<Conflict[]>("/schedule/conflicts"),

  getVersionChanges: (versionId: string) =>
    request<{ version_id: string; summary: Record<string, number>; changes: ChangeItem[] }>(
      `/schedule/${versionId}/changes`,
    ),

  createDisruption: (type: DisruptionType, entityId: string, details: Record<string, unknown>) =>
    request<Disruption>("/disruptions", {
      method: "POST",
      body: JSON.stringify({ type, entity_id: entityId, details }),
    }),

  replan: (
    disruptions: { type: DisruptionType; entity_id: string; details?: Record<string, unknown> }[],
    reason: string,
  ) =>
    request<ReplanResponse>("/replan", {
      method: "POST",
      body: JSON.stringify({
        disruptions: disruptions.map((d) => ({ details: {}, ...d })),
        reason,
      }),
    }),

  listDisruptions: () => request<Disruption[]>("/disruptions"),

  companies: () => request<Company[]>("/companies"),
  students: () => request<Student[]>("/students"),
  rooms: () => request<Room[]>("/rooms"),
  panels: () => request<Panel[]>("/panels"),
};

export const dataApi = {
  createCompany: (body: Record<string, unknown>) =>
    request<Company>("/data/company", { method: "POST", body: JSON.stringify(body) }),
  createStudent: (body: Record<string, unknown>) =>
    request<Student>("/data/student", { method: "POST", body: JSON.stringify(body) }),
  createRoom: (body: Record<string, unknown>) =>
    request<Room>("/data/room", { method: "POST", body: JSON.stringify(body) }),
  createPanel: (body: Record<string, unknown>) =>
    request<Panel>("/data/panel", { method: "POST", body: JSON.stringify(body) }),
  createShortlist: (body: Record<string, unknown>) =>
    request<{ id: string }>("/data/shortlist", { method: "POST", body: JSON.stringify(body) }),
  importJson: (body: Record<string, unknown>) =>
    request<{ created: Record<string, number>; errors: string[] }>("/data/import", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  importCsv: (entity: string, file: File) => {
    const fd = new FormData();
    fd.append("entity", entity);
    fd.append("file", file);
    return fetch(`${BASE}/data/import/csv`, { method: "POST", body: fd }).then((res) =>
      res.ok ? res.json() : Promise.reject(new Error(`CSV import failed (${res.status})`)),
    );
  },
  wipeAll: () => request<{ status: string }>("/data/all", { method: "DELETE" }),
};
