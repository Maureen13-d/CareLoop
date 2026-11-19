export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type OutreachPlan = {
  case_id: string;
  patient_ref: string;
  stage: string;
  kind: "reminder" | "escalation";
  channel: "sms" | "call" | "home_visit" | "coordinator";
  attempt: number;
  message: string;
  days_overdue: number;
};

export type OutreachEvent = {
  id: string;
  case_id: string;
  patient_ref: string;
  stage: string;
  kind: "reminder" | "escalation";
  channel: "sms" | "call" | "home_visit" | "coordinator";
  attempt: number;
  message: string;
  status: string;
  created_at: string;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed with ${res.status}`);
  return (await res.json()) as T;
}

export const getQueue = () => getJson<OutreachPlan[]>("/outreach/queue");
export const getEvents = (limit = 20) =>
  getJson<OutreachEvent[]>(`/outreach/events?limit=${limit}`);
