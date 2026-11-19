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
  revalidatePath("/");
  revalidatePath("/desk");
  revalidatePath(`/desk/${caseId}`);
  redirect(`/desk/${caseId}?notice=${encodeURIComponent(notice)}`);
}

export async function claimCase(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(caseId, `/cases/${caseId}/claim`, {}, "You now own this case.");
}

export async function moveCase(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  const toState = String(formData.get("toState") ?? "");
  await act(
    caseId,
    `/cases/${caseId}/transitions`,
    { to_state: toState, note: "Recorded from the navigation desk" },
    "The journey moved forward.",
  );
}

export async function declineCase(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  const note = String(formData.get("note") ?? "").trim();
  await act(caseId, `/cases/${caseId}/decline`, { note }, "Their choice to stop was recorded.");
}

export async function closeCase(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(
    caseId,
    `/cases/${caseId}/close`,
    {
      evidence_type: String(formData.get("evidence_type") ?? ""),
      description: String(formData.get("description") ?? ""),
      note: "Closed from the navigation desk",
    },
    "The loop is closed.",
  );
}

export async function markLost(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  const note = String(formData.get("note") ?? "").trim();
  await act(caseId, `/cases/${caseId}/mark-lost`, { note }, "A person recorded this as lost to follow-up.");
}

export async function resolveEscalation(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  const escalationId = Number(formData.get("escalationId"));
  const note = String(formData.get("note") ?? "").trim();
  await act(caseId, `/escalations/${escalationId}/resolve`, { note }, "Escalation resolved.");
}

export async function requestVisit(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(
    caseId,
    `/cases/${caseId}/hospital/request`,
    {},
    "The simulated clinic accepted the visit request.",
  );
}

export async function advanceClinic(formData: FormData) {
  const caseId = Number(formData.get("caseId"));
  await act(
    caseId,
    `/cases/${caseId}/hospital/advance`,
    {},
    "The simulated clinic recorded its next milestone.",
  );
}
