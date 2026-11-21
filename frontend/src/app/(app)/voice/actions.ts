"use server";

import { API_URL, authToken } from "@/lib/session";
import { ApiError, api } from "@/lib/api";

export type VoiceCase = {
  key: string;
  public_id: string;
  language: string;
  area_label: string;
  age_band: string;
  finding: string;
  symptom: string;
  say: string;
};

export type VoiceTurn = {
  heard_text: string;
  reply_text: string;
  spoken_text: string;
  template_id: string;
  escalation_label: string | null;
  audio_base64: string | null;
  audio_type: string;
  audio_error: string | null;
  synthetic: boolean;
};

export type VoiceResult = { ok: true; turn: VoiceTurn } | { ok: false; message: string };

export async function loadVoiceCases(): Promise<VoiceCase[]> {
  const data = await api<{ cases: VoiceCase[] }>("/followup/voice/cases");
  return data.cases;
}

async function readTurn(res: Response): Promise<VoiceResult> {
  const body = (await res.json().catch(() => null)) as {
    error?: { message?: string };
    spoken_text?: string;
  } | null;
  if (!res.ok) {
    return { ok: false, message: body?.error?.message ?? `Request failed (${res.status}).` };
  }
  return { ok: true, turn: body as VoiceTurn };
}

export async function speakTurn(publicId: string, text: string): Promise<VoiceResult> {
  try {
    const turn = await api<VoiceTurn>("/followup/voice/turn", {
      method: "POST",
      body: JSON.stringify({ public_id: publicId, text }),
    });
    return { ok: true, turn };
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "The voice check-in could not start.";
    return { ok: false, message };
  }
}

export async function hearTurn(formData: FormData): Promise<VoiceResult> {
  const token = await authToken();
  try {
    const res = await fetch(`${API_URL}/api/v1/followup/voice/hear`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
      cache: "no-store",
    });
    return readTurn(res);
  } catch {
    return { ok: false, message: `Could not reach the API at ${API_URL}.` };
  }
}
