import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { TelegramSim } from "./TelegramSim";

export const instant = false;

export default async function TelegramPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  return (
    <main className="px-4 py-6">
      <h1 className="mb-4 text-4xl">Telegram simulator</h1>
      <TelegramSim />
    </main>
  );
}
