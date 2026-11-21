import { redirect } from "next/navigation";
import { Badge, Page, PageHeader } from "@/components/ui";
import { DEMO_CARD_ID } from "@/lib/demoCard";
import { getSession } from "@/lib/session";
import { TelegramSim } from "./TelegramSim";

export const instant = false;

export default async function TelegramPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "patient") redirect("/escalations");
  return (
    <Page>
      <PageHeader
        title="Telegram simulator"
        description={`The follow-up guide as a person would see it in Telegram. On the live bot, use card ${DEMO_CARD_ID}. That is the same ID as the sign-language card.`}
        meta={<Badge tone="outline">Simulated, nothing is sent</Badge>}
      />
      <TelegramSim />
    </Page>
  );
}
