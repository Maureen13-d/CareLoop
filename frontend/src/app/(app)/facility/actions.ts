"use server";

import { redirect } from "next/navigation";
import { api } from "@/lib/api";

export async function markArrived(formData: FormData) {
  await api(`/followup/facility/${formData.get("case_id")}/arrive`, { method: "POST" });
  redirect("/facility");
}

export async function markLost(formData: FormData) {
  await api(`/followup/facility/${formData.get("case_id")}/lost`, { method: "POST" });
  redirect("/facility");
}
