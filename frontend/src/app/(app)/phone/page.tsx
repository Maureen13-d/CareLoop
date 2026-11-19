import { randomUUID } from "crypto";
import { redirect } from "next/navigation";
import { loadInbox } from "./actions";
import { PhoneLab } from "./PhoneLab";
import { getSession } from "@/lib/session";

export const instant = false;

export default async function PhonePage() {
  const user = await getSession();
  if (!user) redirect("/login");
  const messages = await loadInbox();

  return (
    <main className="space-y-6 px-4 py-6 md:px-0 md:py-0">
      <header className="max-w-2xl">
        <p className="text-sm text-lagoon">Basic phone</p>
        <h1 className="mt-1 text-4xl">The same help, without a smartphone.</h1>
        <p className="mt-3 text-ink-soft">
          Dial the placeholder code, pick a worry, and answer the reminder. Reply 1 to confirm,
          2 to change, 3 for help, STOP to opt out. An undelivered text becomes a navigator task.
        </p>
      </header>
      <PhoneLab sessionId={randomUUID()} initialMessages={messages} />
    </main>
  );
}
