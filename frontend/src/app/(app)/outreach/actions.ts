"use server";

import { revalidatePath } from "next/cache";
import { API_URL } from "@/lib/outreach-api";

export async function runSweep(): Promise<void> {
  const res = await fetch(`${API_URL}/outreach/sweep`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Sweep failed with ${res.status}`);
  revalidatePath("/outreach");
}
