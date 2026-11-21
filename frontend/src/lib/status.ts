import type { Tone } from "@/components/ui";

// Display mapping only: how a status from the API is shown. No business rules live here.

export function priorityTone(priority: string): Tone {
  if (priority === "urgent") return "danger";
  if (priority === "high") return "warn";
  return "neutral";
}

export function priorityLabel(priority: string): string {
  if (priority === "urgent") return "Urgent";
  if (priority === "high") return "High";
  if (priority === "normal") return "Normal";
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}

/** Tone for a chase-list reason, judged from the reason text the API sends. */
export function reasonTone(reason: string): Tone {
  const text = reason.toLowerCase();
  if (text.includes("worse") || text.includes("danger")) return "danger";
  if (text.startsWith("barrier")) return "teal";
  if (text.includes("no reply") || text.includes("unreached") || text.includes("not arrived")) return "warn";
  return "neutral";
}

/** Tone for a maternal risk label. The label is decision support, never a diagnosis. */
export function riskTone(level: string | null): Tone {
  if (level === "red") return "danger";
  if (level === "yellow") return "warn";
  if (level === "green") return "teal";
  return "neutral";
}

export function sentence(text: string): string {
  const clean = text.replaceAll("_", " ").trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}
