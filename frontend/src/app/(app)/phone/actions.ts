"use server";

import { API_URL } from "@/lib/session";
import { HANDSET, type Sms } from "./types";

async function readMessages(): Promise<Sms[]> {
  const res = await fetch(
    `${API_URL}/api/v1/sim/sms-outbox?phone_ref=${encodeURIComponent(HANDSET)}`,
    { cache: "no-store" },
  );
  if (!res.ok) return [];
  return (await res.json()) as Sms[];
}

export async function loadInbox(): Promise<Sms[]> {
  return readMessages();
}

export async function dial(sessionId: string, text: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/channels/ussd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, phone_ref: HANDSET, text }),
    cache: "no-store",
  });
  if (!res.ok) return "Network busy. Try again.";
  const data = (await res.json()) as { text: string };
  return data.text;
}

export async function sendSms(text: string): Promise<Sms[]> {
  await fetch(`${API_URL}/api/v1/channels/sms/inbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone_ref: HANDSET, text }),
    cache: "no-store",
  });
  return readMessages();
}

export async function markUndelivered(id: number): Promise<Sms[]> {
  await fetch(`${API_URL}/api/v1/channels/sms/${id}/undelivered`, {
    method: "POST",
    cache: "no-store",
  });
  return readMessages();
}
