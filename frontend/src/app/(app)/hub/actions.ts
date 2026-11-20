"use server";

import { API_URL } from "@/lib/session";

const DEVICE_KEY = "synthetic-device-key";

export async function sendHub(mode: "data" | "sms", body: Record<string, unknown>) {
  const path = mode === "sms" ? "/api/v1/device/sms-ingest" : "/api/v1/device/readings";
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Device-Key": DEVICE_KEY,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const payload = (await res.json().catch(() => null)) as {
      error?: { message?: string };
      level?: string;
      duplicate?: boolean;
    } | null;
    if (!res.ok) {
      return { ok: false as const, message: payload?.error?.message ?? "The hub could not send." };
    }
    return {
      ok: true as const,
      level: payload?.level ?? "yellow",
      duplicate: Boolean(payload?.duplicate),
    };
  } catch {
    return { ok: false as const, message: `Could not reach the API at ${API_URL}.` };
  }
}
