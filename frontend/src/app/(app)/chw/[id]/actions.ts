"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

async function back(id: string, path: string, body: unknown, notice: string) {
  try {
    await api(path, { method: "POST", body: JSON.stringify(body) });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "That action was refused.";
    redirect(`/chw/${id}?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/");
  revalidatePath(`/chw/${id}`);
  redirect(`/chw/${id}?notice=${encodeURIComponent(notice)}`);
}

export async function saveReading(formData: FormData) {
  const id = String(formData.get("pregnancyId"));
  const signs = formData.getAll("sign").map(String);
  await back(
    id,
    `/maternal/pregnancies/${id}/readings`,
    {
      systolic: Number(formData.get("systolic")),
      diastolic: Number(formData.get("diastolic")),
      pulse: Number(formData.get("pulse")),
      urine_protein: String(formData.get("urine_protein")),
      hb_band: String(formData.get("hb_band")),
      danger_signs: signs,
    },
    "Reading saved. The server set the label.",
  );
}

export async function saveCheckin(formData: FormData) {
  const id = String(formData.get("pregnancyId"));
  const answers: Record<string, string> = {};
  for (const key of ["bleeding", "headache", "vision", "swelling", "pain", "movement", "fever", "fluid", "breathing", "mood"]) {
    const value = String(formData.get(key) ?? "");
    if (value) answers[key] = value;
  }
  if (Object.keys(answers).length === 0) answers.all_clear = "yes";
  await back(
    id,
    `/maternal/pregnancies/${id}/checkins`,
    { channel: "web", language: String(formData.get("language") ?? "en"), answers },
    "Check-in recorded.",
  );
}

export async function moveBand(formData: FormData) {
  const id = String(formData.get("pregnancyId"));
  await back(
    id,
    `/maternal/pregnancies/${id}/band`,
    { device_id: String(formData.get("device_id")), action: String(formData.get("action")) },
    "Band updated.",
  );
}
