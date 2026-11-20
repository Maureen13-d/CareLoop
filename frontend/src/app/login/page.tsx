import { redirect } from "next/navigation";
import { signIn } from "@/app/login/actions";
import { getSession } from "@/lib/session";

export const instant = false;

const PEOPLE = [
  {
    username: "amina",
    name: "Amina Otieno",
    role: "Navigator",
    line: "Works the queue. Calls people, explains fees, finds a clinic.",
  },
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
  {
    username: "aisha",
    name: "Aisha Demo",
    role: "Patient",
    line: "Uses the private chat, or the basic phone in her pocket.",
  },
  {
    username: "grace",
    name: "Grace Achieng",
    role: "Community health promoter",
    line: "Sees only the women assigned to her. Enters a home check. Does not move clinical care.",
  },
];

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await getSession()) redirect("/");
  const { error } = await searchParams;

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl items-center gap-12 px-6 py-12 lg:grid-cols-[1.1fr_0.9fr]">
      <section>
        <p className="text-sm font-medium uppercase tracking-[0.16em] text-lagoon">CareLoop</p>
        <h1 className="mt-4 max-w-xl text-5xl leading-[1.05] text-ink">
          From a worrying check to a real visit.
        </h1>
        <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
          CareLoop helps a person who needs a closer look get there: a calm conversation,
          a named worry, a navigator, a reminder that never mentions the check. The hospital
          takes over once they arrive.
        </p>
        <p className="mt-8 max-w-lg text-sm leading-relaxed text-ink-soft">
          This is a synthetic demo. It does not diagnose, it is not an emergency service, and
          the phone short code <span className="font-medium text-ink">*XYZ#</span> is a placeholder.
        </p>
      </section>
      <section className="rounded-[2rem] border border-line bg-paper-2 p-6 shadow-[0_20px_60px_rgba(28,25,21,0.06)]">
        <h2 className="text-2xl">Step in as someone</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Every demo account uses the password <span className="font-medium text-ink">careloop-demo</span>.
        </p>
        {error ? (
          <p className="mt-4 rounded-2xl bg-[#f8e8e4] px-3 py-2 text-sm text-danger" role="alert">
            {error === "offline"
              ? "The API is not running. Start the backend, then try again."
              : "That sign-in did not work. Is the backend running with the demo accounts?"}
          </p>
        ) : null}
        <form action={signIn} className="mt-5 grid gap-2">
          {PEOPLE.map((person) => (
            <button
              key={person.username}
              name="username"
              value={person.username}
              className="rounded-2xl border border-line bg-white px-4 py-3 text-left hover:border-lagoon"
            >
              <span className="flex items-baseline justify-between gap-3">
                <span className="font-medium">{person.name}</span>
                <span className="text-xs uppercase tracking-wide text-lagoon">{person.role}</span>
              </span>
              <span className="mt-1 block text-sm text-ink-soft">{person.line}</span>
            </button>
          ))}
        </form>
        <p className="text-sm">
          <a className="underline" href="/enter">
            I have a card
          </a>
        </p>
      </section>
    </main>
  );
}
