import { redirect } from "next/navigation";
import { Badge, Page, PageHeader } from "@/components/ui";
import { getSession } from "@/lib/session";
import { TelegramSim } from "./TelegramSim";

export const instant = false;

export default async function TelegramPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  return (
    <Page>
      <PageHeader
        title="Telegram simulator"
        description="The follow-up guide as a person would see it in Telegram. It speaks fixed lines, does not generate text and never names a condition."
        meta={<Badge tone="outline">Simulated, nothing is sent</Badge>}
      />
      <TelegramSim />
    </Page>
  );
}
