import { redirect } from "next/navigation";
import { ChatPanel } from "./ChatPanel";
import { Page, PageHeader } from "@/components/ui";
import { getSession } from "@/lib/session";

export const instant = false;

const STEPS = [
  ["A check needs a closer look", "Someone invites you. You can say no."],
  ["You join", "On this chat, or on a basic phone."],
  ["You name what is in the way", "Only what you confirm reaches a navigator."],
  ["A navigator helps", "Fees, the trip, which clinic."],
  ["A visit is booked", "The reminder says the time and the place. Nothing else."],
  ["You arrive", "The clinic confirms it."],
  ["Their team takes over", "CareLoop only checks that you were not lost."],
];

export default async function ChatPage() {
  const user = await getSession();
  if (!user) redirect("/login");

  return (
    <Page>
      <PageHeader
        title="A private conversation"
        description="The same help exists on a basic phone. This is the richer version: answers that show their source, and a chance to confirm a worry before anyone else sees it."
      />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <aside aria-labelledby="journey-heading" className="order-2 rounded-2xl border border-mint-strong bg-mint p-5 lg:order-1">
          <h2 id="journey-heading" className="text-base">
            Your journey
          </h2>
          <ol className="relative mt-4 space-y-4 before:absolute before:top-3 before:bottom-3 before:left-[0.875rem] before:w-px before:bg-mint-strong">
            {STEPS.map(([title, line], index) => (
              <li key={title} className="relative flex gap-3">
                <span className="relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full bg-deep text-[0.8125rem] font-semibold text-white">
                  {index + 1}
                </span>
                <span>
                  <span className="block text-[0.9375rem] font-medium text-ink">{title}</span>
                  <span className="text-sm text-ink-2">{line}</span>
                </span>
              </li>
            ))}
          </ol>
        </aside>
        <div className="order-1 lg:order-2">
          <ChatPanel />
        </div>
      </div>
    </Page>
  );
}
