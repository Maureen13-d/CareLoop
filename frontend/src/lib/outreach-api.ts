export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Mirrors the backend Stage enum, in pathway order.
export const STAGES = [
  "screened",
  "abnormal_result",
  "referred",
  "diagnostic_done",
  "treatment_started",
  "closed",
] as const;
export type Stage = (typeof STAGES)[number];

export type Channel = "sms" | "call" | "home_visit" | "coordinator" | "clinic";
export type Kind = "reminder" | "escalation" | "response";
export type CaseStatus = "on_track" | "overdue" | "escalated" | "closed";

export type OutreachPlan = {
  case_id: string;
  patient_ref: string;
  stage: Stage;
  kind: Exclude<Kind, "response">;
  channel: Channel;
  attempt: number;
  message: string;
  days_overdue: number;
};

export type OutreachEvent = {
  id: string;
  case_id: string;
  patient_ref: string;
  stage: Stage;
  kind: Kind;
  channel: Channel;
  attempt: number;
  message: string;
  status: string;
  created_at: string;
};

export type CaseView = {
  id: string;
  patient_ref: string;
  stage: Stage;
  stage_entered_at: string;
  history: { stage: Stage; at: string }[];
  overdue: boolean;
};

export type CaseDetail = {
  case: CaseView;
  status: CaseStatus;
  next_stages: Stage[];
  events: OutreachEvent[];
};

export type EscalatedCase = {
  case_id: string;
  patient_ref: string;
  stage: Stage;
  days_overdue: number;
  escalated_at: string;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed with ${res.status}`);
  return (await res.json()) as T;
}

export const getQueue = () => getJson<OutreachPlan[]>("/outreach/queue");
export const getEscalated = () => getJson<EscalatedCase[]>("/outreach/escalated");
export const getEvents = (limit = 20) =>
  getJson<OutreachEvent[]>(`/outreach/events?limit=${limit}`);

export async function getCaseDetail(id: string): Promise<CaseDetail | null> {
  const res = await fetch(`${API_URL}/outreach/cases/${encodeURIComponent(id)}`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Case ${id} failed with ${res.status}`);
  return (await res.json()) as CaseDetail;
}

export type LoopClosureMetrics = {
  contacted_episodes: number;
  attended: number;
  still_open: number;
  unrecorded_advances: number;
  closure_rate: number | null;
  median_contacts_to_attend: number | null;
  attended_by_last_channel: Record<string, number>;
  attended_without_outreach: number;
};

export type EscalationMetrics = {
  escalated: number;
  escalation_rate: number | null;
  recovered: number;
  recovery_rate: number | null;
  awaiting_coordinator: number;
};

export type TimeToReferralMetrics = {
  completed: number;
  median_days: number | null;
  mean_days: number | null;
  within_sla_rate: number | null;
  sla_days: number;
  awaiting: number;
  awaiting_overdue: number;
};

export type Metrics = {
  generated_at: string;
  total_cases: number;
  loop_closure: LoopClosureMetrics;
  escalation: EscalationMetrics;
  time_to_referral: TimeToReferralMetrics;
  disclaimer: string;
};

export const getMetrics = () => getJson<Metrics>("/metrics");
