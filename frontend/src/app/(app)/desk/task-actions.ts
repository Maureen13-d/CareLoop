"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { ApiError, api } from "@/lib/api";

export async function completeTask(formData: FormData) {
  const id = Number(formData.get("taskId"));
  const back = String(formData.get("back") || "/");
  try {
    await api(`/navigator/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "done" }),
    });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "Could not update the task.";
    redirect(`${back}${back.includes("?") ? "&" : "?"}error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/");
  revalidatePath("/desk");
  redirect(back);
}
