"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { API_URL, STAGES } from "@/lib/outreach-api";

export async function markAttended(formData: FormData): Promise<void> {
  const caseId = String(formData.get("caseId") ?? "");
  const toStage = String(formData.get("toStage") ?? "");
  if (!caseId || !(STAGES as readonly string[]).includes(toStage)) {
    throw new Error("Invalid request");
  }

  const res = await fetch(`${API_URL}/outreach/cases/${encodeURIComponent(caseId)}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to_stage: toStage }),
    cache: "no-store",
  });

  revalidatePath("/");
  revalidatePath("/outreach");
  revalidatePath(`/cases/${caseId}`);

  const page = `/cases/${encodeURIComponent(caseId)}`;
  // 409 = someone already moved this case (e.g. a double submit): just show the current state.
  if (res.status === 409) redirect(page);
  if (!res.ok) throw new Error(`Respond failed with ${res.status}`);
  redirect(`${page}?attended=${toStage}`);
}
