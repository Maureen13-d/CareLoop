import { ChevronRight, CircleExclamationPoint, IdCard } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";
import { signIn } from "@/app/login/actions";
import { JourneyLoop } from "@/components/JourneyLoop";
import { MedicalFloaters } from "@/components/MedicalFloaters";
import { UpdateShowcase } from "@/components/UpdateShowcase";
import { Avatar, Wordmark, buttonClasses } from "@/components/ui";
import { getSession } from "@/lib/session";

export const instant = false;

type Person = { username: string; name: string; role: string; line: string };

// The three journeys the demo is built around. The other roles stay one tap away
// below, because the clinician is the only role that can issue an ID or open a case.
const PEOPLE: Person[] = [
  {
    username: "amina",
    name: "Amina Otieno",
    role: "Navigator",
    line: "Works the queue. Calls people, explains fees, finds a clinic.",
  },
  {
    username: "grace",
    name: "Grace Achieng",
    role: "Community health promoter",
    line: "Sees only the women assigned to her. Enters a home check. Does not move clinical care.",
  },
  {
    username: "aisha",
    name: "Aisha Demo",
    role: "Patient",
    line: "Uses the private chat, or the basic phone in her pocket.",
  },
];

const OTHER_PEOPLE: Person[] = [
  {
    username: "david",
    name: "David Kamau",
    role: "Clinician",
    line: "Records a concerning finding and, with consent, opens a case.",
  },
  {
    username: "wanjiku",
    name: "Wanjiku Njeri",
    role: "Counsellor",
    line: "Steps in when someone is distressed or may be in crisis.",
  },
  {
    username: "peter",
    name: "Peter Omondi",
    role: "Program manager",
    line: "Sees the funnel and the audit. Not a person’s private words.",
  },
  {
    username: "admin",
    name: "Demo Admin",
    role: "Admin",
    line: "Looks after the audit log for this demo.",
  },
];

function AccountList({ people }: { people: Person[] }) {
  return (
    <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface shadow-raised">
      {people.map((person) => (
        <li key={person.username}>
          <button
            type="submit"
            name="username"
            value={person.username}
            className="group flex w-full items-center gap-4 px-4 py-3.5 text-left transition-colors hover:bg-mint/60 focus-visible:bg-mint/60 sm:px-5"
          >
            <Avatar name={person.name} />
            <span className="min-w-0 flex-1">
              <span className="flex flex-wrap items-baseline gap-x-2">
                <span className="font-medium text-ink">{person.name}</span>
                <span className="text-[0.8125rem] font-medium text-teal-text">{person.role}</span>
              </span>
              <span className="mt-0.5 block text-sm leading-snug text-ink-2">{person.line}</span>
            </span>
            <ChevronRight aria-hidden="true" className="size-5 shrink-0 text-ink-3 transition-transform group-hover:translate-x-0.5" />
          </button>
        </li>
      ))}
    </ul>
  );
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await getSession()) redirect("/");
  const { error } = await searchParams;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
      {/* brand panel */}
      <section className="relative isolate overflow-hidden bg-emerald px-6 pt-8 pb-10 text-white sm:px-10 lg:flex lg:flex-col lg:px-14 lg:py-12">
        <div className="absolute inset-0 -z-10">
          <MedicalFloaters tone="dark" />
        </div>
        <Wordmark tone="light" />
        <div className="mt-10 max-w-xl lg:mt-16">
          <h1 className="text-[2.25rem] leading-[1.1] text-white sm:text-[2.75rem]">From a worrying check to a real visit.</h1>
          <p className="mt-5 max-w-lg text-[1.0625rem] leading-relaxed text-on-dark/85">
            CareLoop helps a person who needs a closer look get there: a calm conversation, a named worry,
            a navigator, a reminder that never mentions the check. The hospital takes over once they arrive.
          </p>
          <UpdateShowcase className="mt-8" />
        </div>
        <JourneyLoop className="mx-auto mt-10 hidden w-full max-w-[34rem] lg:block" />
        <p className="mt-8 max-w-lg text-sm leading-relaxed text-on-dark-2 lg:mt-auto">
          A synthetic demo. It does not diagnose and it is not an emergency service. The phone short code{" "}
          <span className="font-medium text-on-dark">*XYZ#</span> is a placeholder.
        </p>
      </section>

      {/* sign-in panel */}
      <main id="content" className="relative isolate flex items-start justify-center overflow-hidden px-4 py-10 sm:px-8 lg:items-center lg:py-12">
        <div className="absolute inset-0 -z-10">
          <MedicalFloaters tone="light" />
        </div>
        <div className="w-full max-w-lg">
          <h2 className="text-2xl">Step in as someone</h2>
          <p className="mt-1.5 text-[0.9375rem] text-ink-2">
            Pick a demo account. Every account uses the password{" "}
            <span className="font-medium text-ink">careloop-demo</span>, so one tap signs you in.
          </p>

          {error ? (
            <p role="alert" className="mt-5 flex gap-3 rounded-xl border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger">
              <CircleExclamationPoint aria-hidden="true" className="mt-0.5 size-[1.125rem] shrink-0" />
              {error === "offline"
                ? "The API is not running. Start the backend, then try again."
                : "That sign-in did not work. Is the backend running with the demo accounts?"}
            </p>
          ) : null}

          <form action={signIn} className="mt-6 space-y-3">
            <AccountList people={PEOPLE} />
            <details className="group">
              <summary className="inline-flex min-h-10 cursor-pointer list-none items-center gap-1.5 rounded-full px-2 text-sm font-medium text-teal-text hover:bg-mint [&::-webkit-details-marker]:hidden">
                <ChevronRight aria-hidden="true" className="size-4 transition-transform group-open:rotate-90" />
                Other demo roles
                <span className="hidden font-normal text-ink-2 sm:inline">(clinician, counsellor, program manager, admin)</span>
              </summary>
              <div className="mt-2">
                <AccountList people={OTHER_PEOPLE} />
              </div>
            </details>
          </form>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-mint-strong bg-mint px-5 py-4">
            <p className="text-sm text-ink">
              <span className="font-medium">Were you given a CareLoop card?</span>{" "}
              <span className="text-ink-2">Use its ID to see your next step.</span>
            </p>
            <Link href="/enter" className={buttonClasses({ variant: "secondary", size: "sm" })}>
              <IdCard aria-hidden="true" />I have a card
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
