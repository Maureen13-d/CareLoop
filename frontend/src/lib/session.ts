import { cookies } from "next/headers";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type SessionUser = {
  id: number;
  username: string;
  display_name: string;
  role: string;
  department_id: number | null;
};

export async function authToken(): Promise<string | undefined> {
  const jar = await cookies();
  return jar.get("careloop_token")?.value;
}

export async function getSession(): Promise<SessionUser | null> {
  const token = await authToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as SessionUser;
  } catch {
    return null;
  }
}
