"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

async function act(caseId: number, path: string, body: unknown, notice: string) {
  try {
    await api(path, { method: "POST", body: JSON.stringify(body) });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "That action was refused.";
    redirect(`/desk/${caseId}?error=${encodeURIComponent(message)}`);
  }
  revalidatePath(`/desk/${caseId}`);
  redirect(`/desk/${caseId}?notice=${encodeURIComponent(notice)}`);
}

export async function noteBarrier(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(caseId, `/maternal/cases/${caseId}/barriers`, { flag: String(formData.get("flag")) }, "Barrier noted.");
}

export async function voucherStep(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(
    caseId,
    `/maternal/cases/${caseId}/vouchers`,
    { action: String(formData.get("action")) },
    "Simulated transport step recorded.",
  );
}

export async function coverCheck(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(
    caseId,
    `/maternal/cases/${caseId}/cover`,
    { status: String(formData.get("status")) },
    "Simulated cover check recorded.",
  );
}
