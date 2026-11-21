import { randomUUID } from "crypto";
import { redirect } from "next/navigation";
import { loadInbox } from "./actions";
import { PhoneLab } from "./PhoneLab";
import { Page, PageHeader } from "@/components/ui";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function PhonePage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== "patient") redirect("/escalations");
  const messages = await loadInbox();

  return (
    <Page>
      <PageHeader
        title="The same help, without a smartphone"
        description="Dial the placeholder code, pick a worry, and answer the reminder. Reply 1 to confirm, 2 to change, 3 for help, STOP to opt out. An undelivered text becomes a navigator task."
      />
      <PhoneLab sessionId={randomUUID()} initialMessages={messages} />
    </Page>
  );
}
