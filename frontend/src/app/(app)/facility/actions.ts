"use server";

import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

async function post(caseId: FormDataEntryValue | null, action: "arrive" | "lost") {
  try {
    await api(`/followup/facility/${caseId}/${action}`, { method: "POST" });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "That decision was not recorded.";
    redirect(`/facility?error=${encodeURIComponent(message)}`);
  }
  redirect("/facility");
}

export async function markArrived(formData: FormData) {
  await post(formData.get("case_id"), "arrive");
}

export async function markLost(formData: FormData) {
  await post(formData.get("case_id"), "lost");
}
