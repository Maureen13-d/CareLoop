"use server";

import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

function rethrowRedirect(error: unknown): void {
  if (
    typeof error === "object" &&
    error !== null &&
    "digest" in error &&
    String((error as { digest: unknown }).digest).startsWith("NEXT_REDIRECT")
  ) {
    throw error;
  }
}

export async function recordFinding(formData: FormData) {
  const name = String(formData.get("display_name") ?? "").trim();
  const age = String(formData.get("age_band") ?? "");
  const zone = String(formData.get("zone") ?? "Demo Zone A").trim() || "Demo Zone A";
  const screeningType = String(formData.get("screening_type") ?? "HPV_DNA");
  const result = String(formData.get("result") ?? "positive");
  try {
    const patient = await api<{ id: number }>("/patients", {
      method: "POST",
      body: JSON.stringify({
        display_name: name,
        age_band: age,
        zone,
        preferred_language: "en",
      }),
    });
    await api(`/patients/${patient.id}/consents`, {
      method: "POST",
      body: JSON.stringify({ purpose: "care_coordination", granted: true }),
    });
    if (formData.get("sms") === "on") {
      await api(`/patients/${patient.id}/consents`, {
        method: "POST",
        body: JSON.stringify({ purpose: "sms_reminders", granted: true }),
      });
    }
    const recorded = await api<{ case_id: number | null; message: string }>(
      `/patients/${patient.id}/screenings`,
      {
        method: "POST",
        body: JSON.stringify({ screening_type: screeningType, result }),
      },
    );
    if (recorded.case_id) {
      redirect(`/desk/${recorded.case_id}?notice=${encodeURIComponent(recorded.message)}`);
    }
    redirect(`/intake?notice=${encodeURIComponent(recorded.message)}`);
  } catch (error) {
    rethrowRedirect(error);
    const message = error instanceof ApiError ? error.message : "The finding could not be saved.";
    redirect(`/intake?error=${encodeURIComponent(message)}`);
  }
}
