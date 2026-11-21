"use server";

import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

export async function registerScreening(formData: FormData) {
  const consent = formData.get("consent") === "on";
  try {
    const result = await api<{ public_id: string | null; status: string }>("/followup/register", {
      method: "POST",
      body: JSON.stringify({
        age_band: String(formData.get("age_band") ?? "30-34"),
        area_label: String(formData.get("area_label") ?? "Demo Zone A"),
        screening_type: String(formData.get("screening_type") ?? "general"),
        finding: String(formData.get("finding") ?? "concerning"),
        consent,
        language: String(formData.get("language") ?? "en"),
        channel: String(formData.get("channel") ?? "telegram"),
        contact: String(formData.get("contact") ?? ""),
        assigned_chw_username: "grace",
      }),
    });
    if (result.public_id) redirect(`/slip/${result.public_id}`);
    redirect(`/screen?notice=${encodeURIComponent(result.status)}`);
  } catch (error) {
    if (error instanceof ApiError) {
      redirect(`/screen?error=${encodeURIComponent(error.message)}`);
    }
    throw error;
  }
}
