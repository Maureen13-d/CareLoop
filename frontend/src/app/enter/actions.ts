"use server";

import { api } from "@/lib/api";

export async function simulatedCode(publicId: string) {
  try {
    return await api<{ simulated_code: string }>(
      `/followup/access/dev-code?public_id=${encodeURIComponent(publicId)}`,
    );
  } catch {
    return null;
  }
}
