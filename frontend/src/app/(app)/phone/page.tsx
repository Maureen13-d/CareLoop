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
        description="Dial the placeholder code, or press Call for a simulated voice check. You hear the words and see them on the screen. Nothing is dialled. Reply 1 to confirm, 2 to change, 3 for help, STOP to opt out."
      />
      <PhoneLab sessionId={randomUUID()} initialMessages={messages} />
    </Page>
  );
}
