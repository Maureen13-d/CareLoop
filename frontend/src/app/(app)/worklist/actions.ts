"use server";

import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

async function post(caseId: string, action: string, body?: string) {
  try {
    await api(`/followup/worklist/${caseId}/${action}`, { method: "POST", body });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "That action did not go through.";
    redirect(`/worklist?error=${encodeURIComponent(message)}`);
  }
  redirect("/worklist");
}

export async function claimCase(formData: FormData) {
  await post(String(formData.get("case_id")), "claim");
}

export async function logAttempt(formData: FormData) {
  await post(String(formData.get("case_id")), "attempt");
}

export async function escalateCase(formData: FormData) {
  await post(String(formData.get("case_id")), "escalate");
}

export async function recordOutcome(formData: FormData) {
  await post(
    String(formData.get("case_id")),
    "outcome",
    JSON.stringify({ label: String(formData.get("label") ?? "reached") }),
  );
}
