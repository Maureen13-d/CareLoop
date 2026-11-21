import { Badge } from "@/components/ui";
import type { OutreachEvent } from "@/lib/outreach-api";

export const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS reminder",
  call: "Phone call",
  home_visit: "Home visit (CHW)",
  coordinator: "Care coordinator",
  clinic: "Clinic visit",
};

export const fmtStage = (s: string) => {
  const text = s.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });

/** What kind of outreach contact this was. */
export function KindBadge({ kind }: { kind: OutreachEvent["kind"] }) {
  if (kind === "response") return <Badge tone="teal">Attended</Badge>;
  if (kind === "escalation") return <Badge tone="danger">Escalation</Badge>;
  return <Badge tone="outline">Reminder</Badge>;
}
