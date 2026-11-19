"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { API_URL } from "@/lib/session";

export async function signIn(formData: FormData) {
  const username = String(formData.get("username") ?? "");
  const body = new URLSearchParams({ username, password: "careloop-demo" });
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      cache: "no-store",
    });
  } catch {
    redirect("/login?error=offline");
  }
  if (!res.ok) redirect("/login?error=1");
  const data = (await res.json()) as { access_token: string };
  const jar = await cookies();
  jar.set("careloop_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  redirect("/");
}

export async function signOut() {
  const jar = await cookies();
  jar.delete("careloop_token");
  redirect("/login");
}
