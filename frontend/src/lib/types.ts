export type PriorityTier = "TIER_1" | "TIER_2" | "TIER_3";
export type DisruptionType =
  | "COMPANY_DELAY"
  | "PANEL_UNAVAILABLE"
  | "ROOM_UNAVAILABLE"
  | "STUDENT_WITHDRAWAL";

export interface Company {
  id: string;
  name: string;
  priority_tier: PriorityTier;
  cgpa_cutoff: number;
  interview_duration_minutes: number;
  panel_count: number;
  available_days: string[];
  availability_windows: { day: string; start: string; end: string }[];
  delayed_until: string | null;
}

export interface Student {
  id: string;
  name: string;
  cgpa: number;
  branch: string;
  year: number;
  status: string;
}

export interface Room {
  id: string;
  name: string;
  status: string;
  capacity: number;
}

export interface Panel {
  id: string;
  company_id: string;
  name: string;
  status: string;
}

export interface Interview {
  id: string;
  student_id: string;
  student_name: string;
  company_id: string;
  company_name: string;
  room_id: string | null;
  panel_id: string | null;
  date: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number;
  status: string; // SCHEDULED | UNSCHEDULED | CANCELLED
  reason: string | null;
}

export interface ScheduleVersion {
  id: string;
  version_number: number;
  reason: string;
  previous_version_id: string | null;
  solver_status: string;
  schedule_status: string;
  is_active: boolean;
  created_at: string | null;
  scheduled_count: number;
  unscheduled_count: number;
  cancelled_count: number;
}

export interface ScheduleResponse {
  version: ScheduleVersion;
  interviews: Interview[];
}

export interface Metrics {
  total: number;
  scheduled: number;
  unscheduled: number;
  coverage: number;
  student_clashes: number;
  room_utilization: number;
  panel_utilization: number;
  avg_wait_minutes: number;
  replan_churn: number;
  solver_status: string;
  schedule_status: string;
  interviews_by_day: Record<string, number>;
  interviews_by_tier: Record<string, number>;
  companies: number;
  students: number;
  rooms: number;
  panels: number;
}

export interface Slot {
  date?: string | null;
  start?: string | null;
  end?: string | null;
  room_id?: string | null;
  panel_id?: string | null;
}

export interface ChangeItem {
  interview_id: string;
  student_id: string;
  student_name: string;
  company_id: string;
  company_name: string;
  change_type: "UNCHANGED" | "MOVED" | "CANCELLED" | "ADDED";
  before: Slot | null;
  after: Slot | null;
  reason: string | null;
}

export interface ReplanResponse {
  version_id: string;
  version_number: number;
  solver_status: string;
  schedule_status: string;
  reason: string;
  summary: Record<string, number>;
  changes: ChangeItem[];
}

export interface Disruption {
  id: string;
  type: DisruptionType;
  entity_id: string;
  effective_from: string | null;
  details: Record<string, unknown>;
  status: string;
  created_at: string | null;
}

export interface Conflict {
  conflict_id: string;
  type: "STUDENT_CLASH" | "ROOM_CLASH" | "PANEL_CLASH";
  entity_id: string;
  message: string;
  interview_ids: string[];
  involved: { id: string; student_id?: string; room_id?: string; panel_id?: string; start: number; end: number }[];
}
