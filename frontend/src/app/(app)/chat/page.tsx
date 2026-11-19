import { redirect } from "next/navigation";
import { ChatPanel } from "./ChatPanel";
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
    <main className="grid gap-8 px-4 py-6 lg:grid-cols-[0.85fr_1.15fr] md:px-0 md:py-0">
      <section>
        <p className="text-sm text-lagoon">Your journey</p>
        <h1 className="mt-1 text-4xl">A private conversation</h1>
        <p className="mt-3 text-ink-soft">
          The same help exists on a basic phone. This page is the richer version: cited answers,
          and a chance to confirm a worry before anyone else sees it.
        </p>
        <ol className="mt-6 space-y-4">
          {STEPS.map(([title, line], index) => (
            <li key={title} className="flex gap-3">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-lagoon text-sm text-white">
                {index + 1}
              </span>
              <span>
                <span className="block font-medium">{title}</span>
                <span className="text-sm text-ink-soft">{line}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>
      <ChatPanel />
    </main>
  );
}
