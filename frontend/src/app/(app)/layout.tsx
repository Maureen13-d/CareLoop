import { redirect } from "next/navigation";
import { Shell } from "@/components/Shell";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const user = await getSession();
  if (!user) redirect("/login");
  return <Shell user={user}>{children}</Shell>;
}
